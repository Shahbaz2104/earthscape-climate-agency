import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["EARTHSCAPE_SECRET"] = "test-secret-0123456789abcdef0123456789abcdef"

import pytest
from app.db import init_db
from app.ml import models


@pytest.fixture(autouse=True)
def fresh_db():
    init_db()


@pytest.fixture(autouse=True)
def data():
    from app.ingestion.generate import generate_all
    from app.config import DATASETS_DIR
    if not (DATASETS_DIR / "weather_stations.csv").exists():
        generate_all()


def test_anomaly_training():
    r = models.train_anomaly(limit=2000)
    assert r["samples"] == 2000
    assert 0 < r["anomalies_detected"] < 1000
    assert r["path"].endswith("anomaly_model.joblib")


def test_forecast_training():
    r = models.train_forecast(limit=2000)
    assert len(r["points"]) == 30
    assert "temp_c" in r["points"][0]


def test_correlation_range():
    r = models.correlation(limit=2000)
    assert -1.0 <= r["pearson_r"] <= 1.0
    assert r["samples"] > 0


def test_forecast_persisted():
    models.train_forecast(limit=2000)
    assert models.latest_forecast() is not None