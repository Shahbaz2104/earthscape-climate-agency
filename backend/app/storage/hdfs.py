"""Emulated HDFS: NameNode metadata (JSON) + DataNode block files, 2x replication.
Blocks are encrypted at rest with Fernet (key: data/keys/hdfs.key or EARTHSCAPE_KEY).
Reads balance across replicas round-robin; per-datanode counters exposed for monitoring.
"""
import json, os, threading, time, uuid
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken
from ..config import NAMENODE_FILE, BLOCKS_DIR, BLOCK_SIZE, REPLICATION, DATA_DIR

_lock = threading.Lock()
_read_counts = {}   # node -> reads served
_write_counts = {}  # node -> writes served
_rr_index = 0       # round-robin cursor for replica reads


def _get_key() -> bytes:
    env = os.environ.get("EARTHSCAPE_KEY")
    if env:
        return env.encode()
    key_file = DATA_DIR / "keys" / "hdfs.key"
    key_file.parent.mkdir(parents=True, exist_ok=True)
    if not key_file.exists():
        key_file.write_bytes(Fernet.generate_key())
        key_file.chmod(0o600)
    return key_file.read_bytes()


def _fernet():
    return Fernet(_get_key())


class HDFS:
    def __init__(self):
        self._meta = {"files": {}}
        self._load()

    def _load(self):
        if NAMENODE_FILE.exists():
            self._meta = json.loads(NAMENODE_FILE.read_text())

    def _save(self):
        NAMENODE_FILE.write_text(json.dumps(self._meta, indent=1))

    def put(self, name: str, data: bytes, partition: str = ""):
        """Store bytes as encrypted blocks in HDFS with replication (load-balanced writes)."""
        global _rr_index
        with _lock:
            path = f"/{name}" if not partition else f"/{partition}/{name}"
            if path in self._meta["files"]:
                raise ValueError(f"File already exists: {path} (delete first)")
            f = _fernet()
            blocks = []
            for i in range(0, len(data), BLOCK_SIZE):
                blk = data[i:i + BLOCK_SIZE]
                enc = f.encrypt(blk)
                block_id = f"{uuid.uuid4().hex}"
                replicas = []
                start = _rr_index % REPLICATION
                for r in range(REPLICATION):
                    node = f"datanode-{(start + r) % REPLICATION}"
                    fn = BLOCKS_DIR / f"{block_id}.r{r}"
                    fn.write_bytes(enc)
                    replicas.append({"node": node, "file": fn.name})
                    _write_counts[node] = _write_counts.get(node, 0) + 1
                _rr_index += 1
                blocks.append({"id": block_id, "size": len(blk), "encrypted": True, "replicas": replicas})
            self._meta["files"][path] = {
                "path": path, "size": len(data), "blocks": blocks,
                "block_count": len(blocks), "replication": REPLICATION, "encrypted": True,
                "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            self._save()
            return self._meta["files"][path]

    def put_file(self, name: str, src: Path, partition: str = ""):
        return self.put(name, src.read_bytes(), partition)

    def read(self, path: str) -> bytes:
        global _rr_index
        with _lock:
            f = self._meta["files"].get(path)
            if not f:
                raise KeyError(f"Not found in HDFS: {path}")
            out = b""
            for b in f["blocks"]:
                ok = False
                start = _rr_index % len(b["replicas"])  # load-balance across replicas
                _rr_index += 1
                for i in range(len(b["replicas"])):
                    rep = b["replicas"][(start + i) % len(b["replicas"])]
                    fn = BLOCKS_DIR / rep["file"]
                    if fn.exists():
                        out += self._decrypt(fn.read_bytes(), b.get("encrypted"))
                        _read_counts[rep["node"]] = _read_counts.get(rep["node"], 0) + 1
                        ok = True
                        break
                if not ok:
                    raise RuntimeError(f"All replicas lost for block {b['id']}")
            return out

    def _decrypt(self, data: bytes, encrypted: bool) -> bytes:
        if not encrypted:
            return data
        try:
            return _fernet().decrypt(data)
        except InvalidToken:
            raise RuntimeError("Block decryption failed — wrong key?")

    def read_text(self, path: str) -> str:
        return self.read(path).decode("utf-8", errors="replace")

    def list(self, prefix: str = "/") -> list:
        with _lock:
            out = []
            for p, f in self._meta["files"].items():
                if p.startswith(prefix):
                    out.append({"path": p, "size": f["size"], "blocks": f["block_count"],
                                "replication": f["replication"], "encrypted": f.get("encrypted", False),
                                "created": f["created"]})
            return sorted(out, key=lambda x: x["path"])

    def info(self):
        files = self._meta["files"]
        return {
            "files": len(files),
            "size_bytes": sum(f["size"] for f in files.values()),
            "blocks": sum(f["block_count"] for f in files.values()),
            "replication": REPLICATION,
            "encrypted": all(f.get("encrypted", False) for f in files.values()),
            "namenode": str(NAMENODE_FILE),
        }

    def load_balance(self):
        """Read/write distribution across DataNodes (load-balancing monitor)."""
        nodes = sorted(set(list(_read_counts) + list(_write_counts)))
        return {"nodes": [{"node": n, "reads": _read_counts.get(n, 0), "writes": _write_counts.get(n, 0)}
                          for n in nodes],
                "strategy": "round-robin replica selection on reads; alternating primary on writes"}

    def delete(self, path: str):
        with _lock:
            f = self._meta["files"].pop(path, None)
            if not f:
                raise KeyError(f"Not found in HDFS: {path}")
            for b in f["blocks"]:
                for rep in b["replicas"]:
                    fn = BLOCKS_DIR / rep["file"]
                    if fn.exists():
                        fn.unlink()
            self._save()

    def corrupt(self, path: str, block_index: int = 0):
        """Simulate a DataNode failure to demonstrate fault tolerance."""
        with _lock:
            f = self._meta["files"].get(path)
            if not f:
                raise KeyError(path)
            b = f["blocks"][block_index]
            (BLOCKS_DIR / b["replicas"][0]["file"]).unlink(missing_ok=True)
            return {"path": path, "block": block_index,
                    "remaining_replicas": [r["node"] for r in b["replicas"][1:]]}


hdfs = HDFS()