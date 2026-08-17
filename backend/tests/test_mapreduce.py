import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["EARTHSCAPE_SECRET"] = "test-secret-0123456789abcdef0123456789abcdef"

import pytest
from app.db import init_db
from app.storage.hdfs import hdfs
from app.processing.engine import run_job
from app.processing import jobs

CSV = "region,station_id,date,temp_c\nNA,S1,2020-01-01,10\nNA,S1,2020-01-02,12\nEU,S2,2020-01-01,5\n"


@pytest.fixture(autouse=True)
def setup():
    init_db()
    try:
        hdfs.delete("/raw/tiny.csv")
    except KeyError:
        pass
    hdfs.put("tiny.csv", CSV.encode(), partition="raw")
    yield
    try:
        hdfs.delete("/raw/tiny.csv")
    except KeyError:
        pass


def test_temp_trends_job():
    r = run_job(jobs.temp_trends, "/raw/tiny.csv")
    assert len(r["results"]) >= 1
    assert r["map_output"] > 0
    assert r["duration_ms"] > 0


def test_missing_data_reported():
    csv = "region,station_id,date,temp_c\nNA,S1,2020-01-01,\nNA,S1,2020-01-02,10\n"
    hdfs.put("tiny2.csv", csv.encode(), partition="raw")
    r = run_job(jobs.temp_trends, "/raw/tiny2.csv")
    row = [x for x in r["results"] if x["region"] == "NA"][0]
    assert row["missing"] >= 1
    assert row["avg_temp_c"] == 10.0