import shutil, threading, time
import psutil
from fastapi import APIRouter, Depends
from ..config import DB_PATH, NAMENODE_FILE, BACKUPS_DIR, MODELS_DIR, BACKUP_INTERVAL_HOURS
from ..storage.hdfs import hdfs
from ..db import q, q1
from ..auth.deps import get_current_user, require_role

router = APIRouter(prefix="/monitor", tags=["monitoring"])
START = time.time()
_last_backup = None
_backup_lock = threading.Lock()


def _do_backup():
    global _last_backup
    with _backup_lock:
        ts = time.strftime("%Y%m%d-%H%M%S")
        d = BACKUPS_DIR / ts
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy2(DB_PATH, d / "app.db")
        shutil.copy2(NAMENODE_FILE, d / "namenode.json")
        _last_backup = ts
        return ts


def backup_scheduler():
    """Automated backups: run at startup, then every BACKUP_INTERVAL_HOURS."""
    try:
        _do_backup()
    except Exception:
        pass
    while True:
        time.sleep(BACKUP_INTERVAL_HOURS * 3600)
        try:
            _do_backup()
        except Exception:
            pass


def start_backup_scheduler():
    threading.Thread(target=backup_scheduler, daemon=True).start()


@router.get("/system")
def system(user=Depends(get_current_user)):
    uptime = time.time() - START
    return {
        "uptime_sec": round(uptime),
        "uptime_hours": round(uptime / 3600, 2),
        "status": "operational",
        "uptime_target_pct": 99.0,
        "cpu_pct": psutil.cpu_percent(interval=0.2),
        "mem_pct": psutil.virtual_memory().percent,
        "mem_used_gb": round(psutil.virtual_memory().used / 1e9, 2),
        "disk_free_gb": round(shutil.disk_usage("/").free / 1e9, 2),
    }


@router.get("/overview")
def overview(user=Depends(get_current_user)):
    return {
        "hdfs": hdfs.info(),
        "jobs": {"total": q1("SELECT COUNT(*) c FROM jobs")["c"],
                 "failed": q1("SELECT COUNT(*) c FROM jobs WHERE status='failed'")["c"]},
        "records_processed": q1("SELECT SUM(records) s FROM jobs WHERE status='done'")["s"] or 0,
        "notifications": q1("SELECT COUNT(*) c FROM notifications")["c"],
        "unread": q1("SELECT COUNT(*) c FROM notifications WHERE read=0")["c"],
        "tickets_open": q1("SELECT COUNT(*) c FROM tickets WHERE status='open'")["c"],
        "anomalies": q1("SELECT COUNT(*) c FROM anomalies")["c"],
        "users": q1("SELECT COUNT(*) c FROM users")["c"],
    }


@router.post("/backup")
def backup(user=Depends(require_role("admin"))):
    ts = _do_backup()
    return {"backup": ts, "location": str(BACKUPS_DIR / ts)}


@router.get("/backups")
def backups(user=Depends(get_current_user)):
    return sorted([{"name": p.name, "size": sum(f.stat().st_size for f in p.iterdir())}
                   for p in BACKUPS_DIR.iterdir() if p.is_dir()], key=lambda x: x["name"], reverse=True)


@router.get("/backup/status")
def backup_status(user=Depends(get_current_user)):
    return {"last_automated": _last_backup, "interval_hours": BACKUP_INTERVAL_HOURS,
            "next_due_in_sec": max(0, BACKUP_INTERVAL_HOURS * 3600 - (time.time() - START)) if _last_backup else 0}


@router.get("/lb")
def load_balance(user=Depends(get_current_user)):
    return hdfs.load_balance()