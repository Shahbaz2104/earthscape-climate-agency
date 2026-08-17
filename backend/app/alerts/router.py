from fastapi import APIRouter, Depends
from ..db import q, execute, q1
from ..auth.deps import get_current_user, require_role

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/rules")
def rules(user=Depends(get_current_user)):
    return q("SELECT * FROM rules ORDER BY id")


@router.post("/rules")
def create_rule(body: dict, user=Depends(require_role("admin"))):
    metric = body.get("metric")
    if metric not in ("temp_c", "co2_ppm", "humidity"):
        return {"error": "metric must be temp_c, co2_ppm or humidity"}
    execute("INSERT INTO rules (metric, operator, threshold, severity, enabled, description) VALUES (?,?,?,?,?,?)",
            (metric, body.get("operator", "gt"), body.get("threshold", 0), body.get("severity", "info"),
             int(body.get("enabled", 1)), body.get("description", "")))
    return {"ok": True}


@router.patch("/rules/{rid}")
def update_rule(rid: int, body: dict, user=Depends(require_role("admin"))):
    if "enabled" in body:
        execute("UPDATE rules SET enabled=? WHERE id=?", (int(body["enabled"]), rid))
    if "threshold" in body:
        execute("UPDATE rules SET threshold=? WHERE id=?", (body["threshold"], rid))
    return {"ok": True}


@router.delete("/rules/{rid}")
def delete_rule(rid: int, user=Depends(require_role("admin"))):
    execute("DELETE FROM rules WHERE id=?", (rid,))
    return {"ok": True}


@router.get("/notifications")
def notifications(user=Depends(get_current_user)):
    return q("SELECT * FROM notifications ORDER BY id DESC LIMIT 100")


@router.post("/notifications/read")
def mark_read(user=Depends(get_current_user), body: dict = None):
    execute("UPDATE notifications SET read=1 WHERE read=0")
    return {"ok": True}