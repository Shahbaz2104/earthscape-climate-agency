# Developer Documentation

## System architecture

```
┌────────────────────────────  React SPA (:5173)  ────────────────────────────┐
│ Dashboard · Data · Processing · ML Lab · Alerts · Monitoring · Support · Admin │
└───────────────┬───────────────────────────────┬────────────────────────────┘
                │ REST (JSON + JWT)             │ WebSocket /ws/stream
┌───────────────▼───────────────────────────────▼────────────────────────────┐
│                            FastAPI (:8000)                                  │
│  auth │ ingestion │ processing │ ml │ alerts │ monitoring │ support         │
│  ┌──────────┐ ┌──────────────┐ ┌─────────────┐ ┌──────────────────────┐     │
│  │ StreamHub│ │ MapReduce    │ │ ML models   │ │ Emulated HDFS        │     │
│  │ pub/sub  │ │ spawn pool   │ │ sklearn     │ │ NameNode + 2x blocks │     │
│  │ simulator│ │ map→shuffle→ │ │ joblib save │ │ SQLite (app state)   │     │
│  └──────────┘ │ reduce       │ └─────────────┘ └──────────────────────┘     │
└───────────────┴──────────────┴──────────────────────────────────────────────┘
```

## Key modules (`backend/app/`)

### storage/hdfs.py — emulated HDFS
- Files split into 1 MB blocks (`BLOCK_SIZE`), each block written to 2 "datanodes"
  (`REPLICATION`) under `data/hdfs/blocks/`.
- `namenode.json` holds file → block → replica metadata; written atomically under a thread lock.
- `read()` tries replicas in order → survives `corrupt()` (deletes one replica).
- Swap for real Hadoop by re-implementing the same interface (`put/read/read_text/list/delete`).

### processing/engine.py — MapReduce
- `run_job(job, input_path, limit)` reads the file from HDFS, splits rows into
  `MR_WORKERS` chunks (input splits), maps in a **spawn** Pool (fork would deadlock with the
  streaming thread — see PROGRESS.md), shuffles/sorts by key, reduces per group.
- Jobs are plain module-level functions named `_{job_name}_map` / `_{job_name}_reduce`
  so spawn workers can import them. Header-aware parsing (`_row`) makes jobs work on any
  CSV layout.

### streaming/hub.py — real-time layer
- `StreamHub` = in-process pub/sub; simulator thread publishes a sensor reading every 2 s.
- Every `FLUSH_WINDOW_SEC` the window is appended to `data/datasets/live_sensor_stream.csv`
  (bridge from real-time → batch).
- `main.py` subscribes the alert engine: each reading → `check_rules()` → notifications
  (SQLite) + alert events back through the hub → WebSocket clients.

### ml/models.py — machine learning
- `train_anomaly`: IsolationForest (80 trees, 3% contamination) on
  [temp, humidity, CO2]; predictions persisted to `data/models/anomaly_model.joblib` and
  flagged rows to the `anomalies` table.
- `train_forecast`: linear regression on [day index, sin(2πt/365), cos(2πt/365)] →
  seasonal temperature projection; stored as JSON in `forecasts` table.
- `correlation`: Pearson r between temp and CO2.

### alerts/engine.py
Rules stored in SQLite; operators gt/gte/lt/lte/eq. `check_rules(event)` is synchronous and
cheap — safe to call on the streaming thread.

### auth/
- pbkdf2-sha256 password hashing (stdlib), JWT HS256 (PyJWT; `sub` must be a **string**,
  PyJWT ≥ 2.10 enforces ≥ 32-byte keys).
- `deps.require_role("admin")` → 403 for analysts. Frontend hides admin routes.

## Database (SQLite, `data/app.db`)
`users · jobs · rules · notifications · tickets · forecasts · anomalies` — see `db.SCHEMA`.

## Configuration (`config.py`)
| Setting | Purpose |
|---|---|
| `BLOCK_SIZE` / `REPLICATION` | HDFS block size and replication factor |
| `MR_WORKERS` | MapReduce parallelism (keep ≤ 2 on small machines) |
| `STREAM_INTERVAL_SEC` | Simulator tick |
| `FLUSH_WINDOW_SEC` | Real-time → batch flush window |
| `JWT_SECRET` | Override via env `EARTHSCAPE_SECRET` (min 32 chars) |

## Extending
- **New MapReduce job**: add `_x_map` / `_x_reduce` functions + class in `processing/jobs.py`,
  register in `processing/router.py:JOBS` → appears in the UI automatically.
- **New metric for alerts**: extend `alerts/engine.py` operator map and `check_rules` fields.
- **New chart**: Recharts components in `frontend/src/pages/*` consume the existing APIs.

## Tests
`backend/tests/smoke.py` covers password hashing, JWT, HDFS replication/fault-tolerance,
MapReduce execution, and the auth flow. Run: `.venv/bin/python tests/smoke.py`
