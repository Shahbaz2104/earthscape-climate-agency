import json
from fastapi import APIRouter, Depends, HTTPException
from ..storage.hdfs import hdfs
from ..db import q, execute
from ..processing.engine import run_job
from ..processing import jobs
from ..auth.deps import get_current_user, require_role

router = APIRouter(prefix="/hdfs", tags=["hdfs"])

JOBS = {"temp_trends": {"name": "temp_trends", "desc": "Regional temperature trends by year (fills missing values)",
                        "input": "/raw/weather_stations.csv"},
        "co2_emissions": {"name": "co2_emissions", "desc": "CO2 emissions totals per country and year",
                          "input": "/raw/emissions.csv"},
        "anomaly_counts": {"name": "anomaly_counts", "desc": "Statistical anomaly counts per station (3-sigma)",
                           "input": "/raw/weather_stations.csv"},
        "correlation": {"name": "correlation", "desc": "Temperature vs CO2 correlation per year",
                        "input": "/raw/weather_stations.csv"}}


@router.get("/files")
def list_files(user=Depends(get_current_user)):
    return hdfs.list()


@router.get("/files/{path:path}")
def file_info(path: str, user=Depends(get_current_user)):
    f = [x for x in hdfs.list() if x["path"].lstrip("/") == path]
    if not f:
        raise HTTPException(404, "Not found")
    preview = hdfs.read_text("/" + path)[:2000]
    return {**f[0], "preview": preview}


@router.delete("/files/{path:path}")
def delete_file(path: str, user=Depends(require_role("admin"))):
    hdfs.delete("/" + path)
    return {"ok": True}


@router.post("/files/{path:path}/corrupt")
def corrupt_block(path: str, user=Depends(require_role("admin"))):
    return hdfs.corrupt("/" + path, 0)


@router.get("/info")
def info(user=Depends(get_current_user)):
    return hdfs.info()


@router.get("/jobs")
def list_jobs(user=Depends(get_current_user)):
    return [{"id": k, **v} for k, v in JOBS.items()]


@router.get("/history")
def job_history(user=Depends(get_current_user)):
    return q("SELECT * FROM jobs ORDER BY id DESC LIMIT 50")


@router.post("/jobs/{job_id}/run")
def run(job_id: str, user=Depends(get_current_user), body: dict = None):
    spec = JOBS.get(job_id)
    if not spec:
        raise HTTPException(404, "Unknown job")
    limit = (body or {}).get("limit")
    job = getattr(jobs, job_id)
    execute("INSERT INTO jobs (name, status) VALUES (?,?)", (spec["name"], "running"))
    from ..db import q1
    running = q1("SELECT id FROM jobs WHERE name=? ORDER BY id DESC LIMIT 1", (spec["name"],))
    try:
        result = run_job(job, spec["input"], limit=limit)
        execute("UPDATE jobs SET status='done', duration_ms=?, records=?, finished_at=datetime('now'), detail=? WHERE id=?",
                (result["duration_ms"], len(result["results"]), json.dumps(result["results"][:50]), running["id"]))
        return result
    except Exception as e:
        execute("UPDATE jobs SET status='failed', detail=? WHERE id=?", (str(e), running["id"]))
        raise HTTPException(500, f"Job failed: {e}")