import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from .generate import generate_all
from ..auth.deps import get_current_user
from ..config import DATASETS_DIR
from ..storage.hdfs import hdfs
from ..db import q1

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/generate")
def generate(user=Depends(get_current_user)):
    counts = generate_all()
    for name, count in counts.items():
        hdfs.put_file(name, DATASETS_DIR / name, partition="raw")
    return {"generated": counts, "note": "Uploaded to HDFS /raw/"}


@router.post("/upload")
async def upload(file: UploadFile = File(...), user=Depends(get_current_user)):
    if not file.filename.endswith((".csv", ".json", ".nc", ".nc4")):
        raise HTTPException(400, "Supported formats: CSV, JSON, NetCDF (.nc/.nc4)")
    data = await file.read()
    if len(data) > 50 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 50MB)")
    dest = DATASETS_DIR / file.filename
    dest.write_bytes(data)
    try:
        if file.filename.endswith(".nc") or file.filename.endswith(".nc4"):
            df = _read_netcdf(dest)
        elif file.filename.endswith(".csv"):
            df = pd.read_csv(dest)
        else:
            df = pd.read_json(dest)
        rows = len(df)
    except Exception as e:
        raise HTTPException(400, f"Unparseable file: {e}")
    hdfs.put(file.filename, data, partition="raw")
    return {"file": file.filename, "columns": list(df.columns), "rows": rows, "hdfs_path": f"/raw/{file.filename}"}


def _read_netcdf(path):
    """Convert a NetCDF file to a DataFrame (common climate science format)."""
    import netCDF4
    ds = netCDF4.Dataset(path)
    try:
        vars_ = {name: ds.variables[name][:] for name in ds.variables}
        rec = None
        for name in ds.dimensions:
            if ds.dimensions[name].isunlimited() or ds.dimensions[name].size > 1:
                rec = name
                break
        if rec is None or not vars_:
            raise ValueError("No record dimension or variables found")
        import numpy as np
        out = {}
        for name, arr in vars_.items():
            if arr.ndim == 1 and len(arr) == len(ds.dimensions[rec]):
                out[name] = np.asarray(arr).tolist()
        df = pd.DataFrame(out)
        for name in ds.ncattrs():
            if not name.startswith("_"):
                df.attrs[name] = ds.getncattr(name)
        return df
    finally:
        ds.close()


@router.get("/datasets")
def list_datasets(user=Depends(get_current_user)):
    out = []
    for f in sorted(DATASETS_DIR.glob("*.*")):
        if f.name.startswith("live_"):
            continue
        out.append({"name": f.name, "size": f.stat().st_size, "hdfs": f"/raw/{f.name}"})
    return out