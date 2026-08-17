import asyncio, json
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .auth.router import router as auth_router, seed_users
from .ingestion.router import router as ingest_router
from .processing.router import router as processing_router
from .ml.router import router as ml_router
from .alerts.router import router as alerts_router
from .alerts.engine import seed_rules, check_rules, notify
from .monitoring.router import router as monitor_router, start_backup_scheduler
from .support.router import router as support_router
from .streaming.hub import hub


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_users()
    seed_rules()
    hub.start_simulator()
    start_backup_scheduler()
    from .processing.router import JOBS
    from .config import DATASETS_DIR
    if not (DATASETS_DIR / "weather_stations.csv").exists():
        from .ingestion.generate import generate_all
        from .storage.hdfs import hdfs
        counts = generate_all()
        for name in counts:
            hdfs.put_file(name, DATASETS_DIR / name, partition="raw")
    hub.subscribe(lambda e: _handle_stream(e))
    yield


def _handle_stream(event):
    if event.get("type") == "reading":
        for rule in check_rules(event):
            notify(f"ALERT [{rule['severity'].upper()}] {rule['metric']} {rule['operator']} {rule['threshold']}",
                   f"{event['station']} ({event['region']}): {event[rule['metric']]} — {rule['description']}",
                   rule["severity"])
            hub.publish({"type": "alert", "severity": rule["severity"], "metric": rule["metric"],
                         "station": event["station"], "value": event[rule["metric"]],
                         "threshold": rule["threshold"], "title": rule["description"]})


app = FastAPI(title="EarthScape Climate Agency", version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(auth_router)
app.include_router(ingest_router)
app.include_router(processing_router)
app.include_router(ml_router)
app.include_router(alerts_router)
app.include_router(monitor_router)
app.include_router(support_router)


@app.get("/")
def root():
    return {"app": "EarthScape Climate Agency", "docs": "/docs", "status": "ok"}


@app.websocket("/ws/stream")
async def ws_stream(ws: WebSocket):
    await ws.accept()
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue()
    unsubscribe = await loop.run_in_executor(None, lambda: hub.subscribe(lambda e: queue.put_nowait(e)))
    try:
        while True:
            event = await queue.get()
            await ws.send_text(json.dumps(event))
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        unsubscribe()