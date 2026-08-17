# EarthScape Climate Agency — Software Requirements Specification

> Maps every requirement from `Background Climate change.txt` (FR = Functional, NFR = Non-Functional)
> to design, implementation and verification. Reference: [FR.x]/[NFR.x] follow the file's numbering.

## Functional requirements

### FR1 — User Authentication and Authorization
| Requirement | Design | Implementation | Verification |
|---|---|---|---|
| Secure auth with roles (administrators, analysts) | JWT (HS256) + pbkdf2-sha256 (120k iters, salted) | `backend/app/security.py`, `auth/router.py` | `tests/test_auth.py`; login as both demo users |
| Access control by role | Server-side `require_role` dependency on every admin route | `backend/app/auth/deps.py` | 403 returned for analyst on admin endpoints; Admin page hidden in UI |

### FR2 — Data Ingestion
| Requirement | Design | Implementation | Verification |
|---|---|---|---|
| Diverse datasets (satellite, weather stations, sensors) | Synthetic generators with realistic seasonal patterns | `backend/app/ingestion/generate.py` | `/ingest/datasets` lists 3 datasets; HDFS `/raw/` |
| Historical + real-time sources | Historical CSV generation; live sensor simulator thread | `streaming/hub.py` | WebSocket `/ws/stream` live readings |
| Common climate formats | CSV, JSON, NetCDF (CF-style) | `ingestion/router.py` (`_read_netcdf`) | Upload API tested with `.nc` (12 rows parsed) |

### FR3 — Data Storage (HDFS)
| Requirement | Design | Implementation | Verification |
|---|---|---|---|
| Scalable, fault-tolerant HDFS storage | Emulated HDFS: 1 MB blocks, 2x replication, NameNode metadata JSON | `storage/hdfs.py` | `tests/test_hdfs.py` (roundtrip, replication, corruption survival) |
| Partitioning/organization | `/raw/<dataset>` partitions; MR grouping by region/year keys | `storage/hdfs.py`, `processing/engine.py` | File list shows partitions; job results grouped |
| Encryption at rest | Fernet per-block encryption, key at `data/keys/` (0600) | `storage/hdfs.py` | `test_encrypted_at_rest` (no plaintext in blocks) |

### FR4 — Data Processing (MapReduce)
| Requirement | Design | Implementation | Verification |
|---|---|---|---|
| Parallel MapReduce across nodes | Split → parallel map (2 spawn workers) → shuffle/sort → reduce | `processing/engine.py` | `tests/test_mapreduce.py`; live job run (10,605 map outputs, 66 groups) |
| Climate patterns, anomalies, correlations | temp_trends (avg/min/max), anomaly_counts (3-sigma), correlation (Pearson r) | `processing/jobs.py` | Job results charted in Processing page |
| Graceful missing-data handling | Missing values counted per group; ML interpolates/fills | `jobs.py`, `ml/models.py` | `test_missing_data_reported` |

### FR5 — Real-time Data Processing
| Requirement | Design | Implementation | Verification |
|---|---|---|---|
| Real-time streaming | Pub/sub StreamHub + 2 s simulator + WebSocket push | `streaming/hub.py` | WS client receives readings |
| Integration with batch | Windowed flush (30 s) appends to `live_sensor_stream.csv` → available to batch jobs | `streaming/hub.py` | File present with growing rows |

### FR6 — Machine Learning
| Requirement | Design | Implementation | Verification |
|---|---|---|---|
| Predictive analysis of trends/impacts | Seasonal linear regression (sin/cos features) → 30-day forecast | `ml/models.py` | `tests/test_ml.py` |
| Anomaly detection, trend, correlation | IsolationForest (80 trees, 3% contamination); Pearson correlation | `ml/models.py` | `test_anomaly_training`, `test_correlation_range` |
| Regular model refinement | Retrain endpoints on latest data | `ml/router.py` | UI train buttons; persisted via joblib + DB |

### FR7 — Data Visualization
| Requirement | Design | Implementation | Verification |
|---|---|---|---|
| Interactive dashboards | React 19 SPA, Recharts, WebSocket live charts | `frontend/src/pages/Dashboard.tsx` | Browser E2E screenshots |
| Patterns, anomalies, predictions visuals | Charts on Processing/ML/Dashboard pages | `frontend/src/pages/*` | `docs/screenshots/v_*.png` |
| Customizable, user-friendly interfaces | Role-aware navigation, configurable job limits, filters | `frontend/src/App.tsx` | Role tests in UI |

### FR8 — Notifications and Alerts
| Requirement | Design | Implementation | Verification |
|---|---|---|---|
| Automated threshold alerts | Rule engine evaluated on every streamed reading | `alerts/engine.py` | Alert cards observed live in browser |
| Configurable, real-time | Rule CRUD (admin) + WS alert push | `alerts/router.py` | Rules page; WS alert events |

### FR9 — Feedback and Support
| Requirement | Design | Implementation | Verification |
|---|---|---|---|
| Support system | Ticket create/list; admin status workflow (open → in_progress → resolved) | `support/router.py` | Ticket submitted in E2E; admin resolves |

## Non-functional requirements

| NFR | Design | Implementation | Verification |
|---|---|---|---|
| Performance monitoring | psutil metrics, job runtimes table, HDFS inventory | `monitoring/router.py` | Monitoring page auto-refresh |
| Optimization strategies | Worker/split sizing (`MR_WORKERS`), spawn context, config knobs | `config.py` | Job durations tracked |
| Encryption storage + transmission | Fernet at rest; JWT over HTTPS; `scripts/gen_cert.sh` | `storage/hdfs.py`, `scripts/` | `test_encrypted_at_rest`; HTTPS run command documented |
| Regulatory compliance | `docs/COMPLIANCE.md` (CF conventions, GDPR-style handling) | docs | — |
| 99% uptime target | Uptime tracked; status endpoint; scheduled maintenance = backup + restart | `monitoring/router.py` | `status: operational` |
| Automated backups | Startup + every 6 h scheduler (DB + NameNode); on-demand | `monitoring/router.py` | `backup/status` shows last run |
| Horizontal scalability | Configurable replication/block size/workers; pluggable storage interface | `config.py` | LB counters in `/monitor/lb` |
| Load balancing | Round-robin replica reads; alternating primary writes | `storage/hdfs.py` | `test_load_balance_counters` |
| Data standards compliance | CF/NetCDF, ISO 19115 mapping, WMO roadmap | `docs/COMPLIANCE.md` | — |
| User documentation | Guides, FAQs, tutorials | `docs/USER_GUIDE.md` | — |
| Developer documentation | Architecture, workflows, ML models | `docs/DEVELOPER_GUIDE.md` | — |
| Video of complete working system | `docs/demo_video.webm` + narration script | `docs/VIDEO_SCRIPT.md` | — |

## Assumptions & constraints
- Hadoop emulated in Python (no cluster available); same HDFS/MapReduce semantics, swap-ready interface
- Environment: 3.6 GB RAM, 5.6 GB free disk → modest dataset sizes, 2 MR workers
- Demo accounts: `admin/admin123` (admin), `analyst/analyst123` (analyst)