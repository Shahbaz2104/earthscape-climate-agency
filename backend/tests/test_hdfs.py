import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["EARTHSCAPE_SECRET"] = "test-secret-0123456789abcdef0123456789abcdef"

import pytest
from app.db import init_db
from app.storage.hdfs import hdfs
from app.config import BLOCKS_DIR
import json


@pytest.fixture(autouse=True)
def fresh_db():
    init_db()


@pytest.fixture(autouse=True)
def cleanup():
    yield
    for p in list(hdfs.list()):
        hdfs.delete(p["path"])


def test_put_read_delete_roundtrip():
    data = b"climate" * 5000
    info = hdfs.put("test.bin", data)
    assert info["size"] == len(data)
    assert info["encrypted"] is True
    assert hdfs.read("/test.bin") == data


def test_encrypted_at_rest():
    data = b"secret-payload-" * 500
    hdfs.put("enc.bin", data)
    f = hdfs._meta["files"]["/enc.bin"]
    block = (BLOCKS_DIR / f["blocks"][0]["replicas"][0]["file"]).read_bytes()
    assert data[:20] not in block
    assert hdfs.read("/enc.bin") == data


def test_fault_tolerance_after_corruption():
    data = b"x" * 1024 * 50
    hdfs.put("fault.bin", data)
    hdfs.corrupt("/fault.bin", 0)
    assert hdfs.read("/fault.bin") == data


def test_replication_is_2():
    data = b"y" * 1024
    hdfs.put("rep.bin", data)
    f = hdfs._meta["files"]["/rep.bin"]
    assert f["replication"] == 2
    assert len(f["blocks"][0]["replicas"]) == 2


def test_load_balance_counters():
    data = b"z" * 1024
    for i in range(4):
        hdfs.put(f"lb{i}.bin", data)
        hdfs.read(f"/lb{i}.bin")
    lb = hdfs.load_balance()
    assert len(lb["nodes"]) >= 2
    assert sum(n["reads"] for n in lb["nodes"]) >= 4