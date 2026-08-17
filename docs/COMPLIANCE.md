# Compliance & Standards

EarthScape Climate Agency aligns its data handling with environmental data conventions and
industry best practices for big data processing. This document maps each requirement to the
implemented approach and notes follow-ups for production deployment.

## Environmental data standards & protocols

| Standard / convention | Status | Implementation |
|---|---|---|
| **NetCDF / CF conventions** (Climate and Forecast) | ✅ supported | NetCDF (`.nc`/`.nc4`) ingestion with `netCDF4`; CF-style metadata attributes preserved as DataFrame attrs on ingest |
| **ISO 19115** (geospatial metadata) | ⚠️ mapped | Dataset metadata (station coords, timestamps, source) stored in dataset columns; full ISO 19115 record generation is a follow-up |
| **WMO data exchange** (BUFR/GTS) | ⚠️ future | Streaming ingest currently uses a JSON/CSV-compatible sensor schema; a WMO-compatible adapter is on the roadmap |
| Open formats (CSV, JSON, NetCDF) | ✅ | All ingest formats are open, non-proprietary |

## Data protection (GDPR-style handling of user data)

- **Encryption at rest** — every HDFS block is encrypted with Fernet (AES-128-CBC + HMAC);
  key at `data/keys/hdfs.key` (0600 perms) or `EARTHSCAPE_KEY` env override. Rotating the key
  invalidates stored blocks (key management must follow an org policy in production).
- **Encryption in transit** — JWT bearer tokens over HTTPS; run with
  `scripts/gen_cert.sh` + `uvicorn --ssl-keyfile --ssl-certfile` (self-signed for dev,
  real CA certificates for production).
- **Passwords** — pbkdf2-sha256 with 120k iterations and per-user salt; never stored in
  plaintext.
- **Access control** — role-based access (admin/analyst) enforced server-side on every route
  (`auth/deps.py`), not just hidden in the UI.
- **Minimal retention** — user data is limited to account + support tickets; climate data is
  agency-owned input data.

## Big-data best practices

- **Fault tolerance**: 2x block replication, reads survive DataNode loss (demonstrable via the
  "corrupt" action); `namenode.json` is the single source of truth.
- **Parallel processing**: MapReduce with input splits, parallel map, shuffle/sort, reduce;
  workers sized to machine (spawn context, configurable `MR_WORKERS`).
- **Load balancing**: round-robin replica selection on reads, alternating primary node on
  writes; per-node read/write counters exposed via `/monitor/lb`.
- **Reliability**: automated backups every 6 h + at startup (DB + NameNode metadata), on-demand
  backup, uptime tracking toward the 99% target, scheduled maintenance via restart + backup.
- **Monitoring**: CPU/memory/disk/uptime, job runtimes, HDFS inventory, stream health.

## Production checklist (follow-ups)

- [ ] Real CA certificate + HSTS header for HTTPS
- [ ] Key rotation policy and secrets manager integration for `EARTHSCAPE_KEY`
- [ ] ISO 19115 metadata generation for uploaded datasets
- [ ] Audit log for admin actions (user changes, deletes, backups)
- [ ] GDPR data-export/deletion endpoints for user accounts
- [ ] Swap emulated HDFS for a real Hadoop cluster via the storage interface (unchanged API)
- [ ] Penetration test + dependency scanning (CVE watch on FastAPI/sklearn/pandas)