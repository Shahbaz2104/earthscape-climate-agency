# EarthScape Climate Agency — Build Progress

## Status: COMPLETE ✅ (backend + frontend + E2E + docs + requirements-gap closure)

## Gap closure (round 2 — all 6 items done)
- [x] **Encryption at rest** — every HDFS block now Fernet-encrypted (key `data/keys/hdfs.key`, 0600, or `EARTHSCAPE_KEY`); verified: no plaintext in blocks, round-trip works, `encrypted: true` in namenode
- [x] **HTTPS/TLS-ready** — `backend/scripts/gen_cert.sh` (self-signed cert) + documented uvicorn `--ssl-keyfile/--ssl-certfile`; frontend API/WS base URL configurable via `VITE_API_URL`
- [x] **Automated backups** — scheduler thread: backup at startup + every `BACKUP_INTERVAL_HOURS` (6 h); `/monitor/backup/status` shows schedule; verified fired at startup (20260817-220426)
- [x] **Load balancing** — round-robin replica reads + alternating primary writes; per-node read/write counters at `/monitor/lb`; shown on Monitoring page
- [x] **NetCDF support** — `.nc`/`.nc4` upload via netCDF4 (CF-style), verified with a real uploaded file (12 rows, 2 vars)
- [x] **Demo video** — `docs/demo_video.webm` (28 s slideshow of all 7 pages, ffmpeg-built) + `docs/VIDEO_SCRIPT.md` for narrated version
- [x] **Compliance** — `docs/COMPLIANCE.md`: NetCDF/CF, ISO 19115 mapping, WMO roadmap, GDPR-style user-data handling, big-data best practices, production checklist; linked from README
- [x] Smoke tests still green; final API sweep green (encrypted HDFS, LB counters, backup schedule)

## Round 1 — core build (all done)
- [x] Backend scaffold: FastAPI + venv, all deps installed (fastapi, uvicorn, pandas, scikit-learn, psutil, PyJWT, cryptography, netCDF4)
- [x] **Emulated HDFS** (`app/storage/hdfs.py`): block storage (1MB blocks), 2x replication, NameNode metadata, fault-tolerant read (survives corrupted node), delete/corrupt-for-demo
- [x] **Data ingestion** (`app/ingestion/`): realistic synthetic datasets — weather_stations (10,800 rows, 2015–2025, ~1.8% missing values), emissions (180 rows), satellite (3,000 rows); CSV upload API; auto-upload to HDFS `/raw/`
- [x] **MapReduce engine** (`app/processing/engine.py`): split → parallel map (2 spawn workers) → shuffle/sort → parallel reduce; runs on HDFS input
  - Jobs: `temp_trends` (region×year avg/min/max, missing counted), `co2_emissions`, `anomaly_counts` (3-sigma), `correlation` (temp↔CO2 Pearson per year)
- [x] **Real-time streaming** (`app/streaming/hub.py`): sensor simulator (8 stations, 1 reading / 2s), pub/sub hub, WebSocket `/ws/stream`, windowed flush to `live_sensor_stream.csv`
- [x] **ML models** (`app/ml/models.py`): IsolationForest anomaly detection (120/4000 found), seasonal linear-regression 30-day forecast, temp↔CO2 correlation; models persisted via joblib; retrain endpoints
- [x] **Alerts** (`app/alerts/engine.py`): configurable threshold rules (temp_c, co2_ppm, humidity), evaluated on every streamed reading, in-app notifications + WS push
- [x] **Auth + RBAC** (`app/auth/`): JWT (HS256), pbkdf2 password hashing, roles admin/analyst, admin-only user management; seeded users: `admin/admin123`, `analyst/analyst123`
- [x] **Monitoring** (`app/monitoring/`): system metrics (CPU/RAM/disk/uptime), platform overview, on-demand backup (db + namenode) + backup list
- [x] **Support** (`app/support/`): ticket create/list, admin status updates
- [x] Smoke tests pass (`tests/smoke.py`): password, JWT, HDFS replication, MapReduce, auth flow
- [x] **Frontend** (React 19 + TS + Vite): 8 pages — Dashboard (live WS charts + alerts), Climate Data (HDFS browser, upload, corrupt demo), Processing (run jobs, results, history), ML Lab (train anomaly/forecast, correlation), Alerts (rule CRUD + inbox), Monitoring (metrics + backup), Support (tickets), Admin (user mgmt, admin-only)
- [x] `tsc -b` clean + `vite build` passes
- [x] **E2E browser-verified** (agent-browser, headless Chrome): login both accounts → dashboard live stream renders → MapReduce job runs from UI (10,605 map outputs, 66 groups, ~1.3 s) → ML training button → alerts page rules/inbox → screenshots saved in `docs/screenshots/`
- [x] **Docs**: README.md, docs/USER_GUIDE.md, docs/DEVELOPER_GUIDE.md, docs/VIDEO_SCRIPT.md (4:50 demo script)

## Known notes / decisions
- No real Hadoop available → emulated with same semantics behind `hdfs` module (pluggable later)
- Multiprocessing uses `spawn` (fork deadlocks with streaming thread) — fixed
- PyJWT 2.13 requires `sub` as string — fixed
- Machine: 3.6GB RAM, 5.6GB free disk → datasets kept small, 2 MR workers
- JWT secret must be ≥32 bytes (PyJWT 2.10+ enforces)

## How to run
```
cd backend && .venv/bin/uvicorn app.main:app --port 8000
```
API docs: http://localhost:8000/docs
