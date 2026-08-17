import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["EARTHSCAPE_SECRET"] = "test-secret-0123456789abcdef0123456789abcdef"
from app.db import init_db
from app.storage.hdfs import hdfs
from app.security import hash_password, verify_password, create_token, decode_token


def test_password():
    h = hash_password("secret123")
    assert verify_password("secret123", h)
    assert not verify_password("wrong", h)


def test_token():
    t = create_token(1, "a", "admin")
    d = decode_token(t)
    assert d["sub"] == "1" and d["role"] == "admin"
    assert decode_token("garbage") is None


def test_hdfs():
    init_db()
    try:
        hdfs.delete("/test.bin")
    except KeyError:
        pass
    data = b"a" * 1024 * 100 + b"climate" * 1000
    info = hdfs.put("test.bin", data)
    assert info["size"] == len(data)
    assert hdfs.read("/test.bin") == data
    hdfs.corrupt("/test.bin", 0)
    assert hdfs.read("/test.bin") == data  # survives via replica
    hdfs.delete("/test.bin")
    try:
        hdfs.read("/test.bin")
        assert False, "should be deleted"
    except KeyError:
        pass


def test_mapreduce():
    init_db()
    csv = "region,station_id,date,temp_c\nNA,S1,2020-01-01,10\nNA,S1,2020-01-02,12\nEU,S2,2020-01-01,5\n"
    try:
        hdfs.delete("/raw/tiny.csv")
    except KeyError:
        pass
    hdfs.put("tiny.csv", csv.encode(), partition="raw")
    from app.processing.engine import run_job
    from app.processing import jobs
    r = run_job(jobs.temp_trends, "/raw/tiny.csv")
    assert len(r["results"]) >= 1
    assert r["duration_ms"] > 0


def test_auth_flow():
    from app.auth.router import seed_users
    init_db()
    seed_users()
    from app.db import q1
    u = q1("SELECT * FROM users WHERE username='admin'")
    assert u and verify_password("admin123", u["password_hash"])


if __name__ == "__main__":
    for fn in (test_password, test_token, test_hdfs, test_mapreduce, test_auth_flow):
        fn()
        print(f"PASS {fn.__name__}")