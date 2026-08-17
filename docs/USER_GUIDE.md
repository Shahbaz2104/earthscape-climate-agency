# EarthScape Climate Agency — User Guide

## Getting started
1. Start the backend: `cd backend && .venv/bin/uvicorn app.main:app --port 8000`
2. Start the frontend: `cd frontend && npm run dev` → open http://localhost:5173
3. Sign in with `admin/admin123` (full access) or `analyst/analyst123` (analyst access)

## Pages

### 📊 Dashboard
Live view of the whole platform. The temperature chart streams sensor readings in real time
over WebSocket. Live alerts appear instantly when a threshold rule fires. Platform health shows
job success rates, HDFS replication, and stored anomalies.

### 🗄️ Climate Data
- **Generate demo datasets** — creates realistic weather station (2015–2025, with ~2% missing
  values), emissions and satellite records, then uploads them to HDFS `/raw/`.
- **Upload CSV/JSON** — bring your own climate data (max 50 MB).
- Files are stored as replicated HDFS blocks. The **corrupt** button simulates a DataNode
  failure — the file stays readable thanks to the second replica (fault-tolerance demo).

### ⚙️ Processing
Run MapReduce batch jobs over the stored data:
- **temp_trends** — average/min/max temperature per region and year (missing values counted)
- **co2_emissions** — CO2 totals per country and year
- **anomaly_counts** — statistical outliers per station (3-sigma rule)
- **correlation** — temperature vs CO2 correlation per year

Results are shown as tables + charts, and every run is recorded in job history with runtime.

### 🧠 ML Lab
- **Train anomaly detection** — IsolationForest flags unusual readings (shown with scores)
- **Train forecast** — seasonal regression projects the next 30 days of temperature
- Correlation panel reports the current temperature↔CO2 Pearson coefficient

### 🔔 Alerts
Rules (metric + operator + threshold + severity) are evaluated against *every* streamed
reading. Admin can add/toggle rules; everyone sees the notification inbox. Alert events also
stream live to the dashboard.

### 📈 Monitoring
CPU, memory, disk, uptime (99% target), plus reliability tooling: **backup now** snapshots the
database and HDFS metadata. Job runtimes are tracked under Processing → history.

### 💬 Support
Submit a ticket (subject + message). Admins can move tickets through open → in progress →
resolved.

### 🛡️ Admin (admin only)
Create users, change roles, delete users. Analysts cannot access this page (403), cannot delete
HDFS files, and cannot create alert rules or run backups.

## Roles summary
| Capability | Analyst | Admin |
|---|---|---|
| View data / run jobs / train ML | ✓ | ✓ |
| Upload data, view alerts | ✓ | ✓ |
| Delete HDFS files | ✗ | ✓ |
| Manage alert rules, backups, users | ✗ | ✓ |

## FAQ
- **Where is the data stored?** `data/hdfs/` (blocks + namenode metadata), app state in
  `data/app.db`, models in `data/models/`, backups in `data/backups/`.
- **How do I reset everything?** Stop servers, delete `data/`, restart — datasets regenerate
  automatically on first boot.
- **Is this real Hadoop?** The platform emulates HDFS/MapReduce semantics in Python so it runs
  anywhere; the storage engine can be swapped for a real Hadoop cluster later.
