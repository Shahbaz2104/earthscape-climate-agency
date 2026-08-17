import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATASETS_DIR = DATA_DIR / "datasets"
HDFS_DIR = DATA_DIR / "hdfs"
BLOCKS_DIR = HDFS_DIR / "blocks"
NAMENODE_FILE = HDFS_DIR / "namenode.json"
MODELS_DIR = DATA_DIR / "models"
BACKUPS_DIR = DATA_DIR / "backups"
DB_PATH = DATA_DIR / "app.db"

for d in (DATASETS_DIR, BLOCKS_DIR, MODELS_DIR, BACKUPS_DIR):
    d.mkdir(parents=True, exist_ok=True)

JWT_SECRET = os.environ.get("EARTHSCAPE_SECRET", "earthscape-dev-secret-0123456789abcdef-please-change")
JWT_ALGO = "HS256"
JWT_EXPIRE_MINUTES = 60 * 12
BLOCK_SIZE = 1024 * 1024  # 1 MB demo blocks
REPLICATION = 2
MR_WORKERS = 2
STREAM_INTERVAL_SEC = 2.0
FLUSH_WINDOW_SEC = 30.0
BACKUP_INTERVAL_HOURS = 6