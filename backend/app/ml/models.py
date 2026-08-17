"""ML: anomaly detection (IsolationForest), trend forecast (seasonal regression), correlation."""
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression
from ..db import q1, execute
from ..config import DATASETS_DIR, MODELS_DIR

FEATURES = ["temp_c", "humidity", "co2_ppm"]


def load_weather(limit=12000):
    df = pd.read_csv(DATASETS_DIR / "weather_stations.csv", nrows=limit)
    df["temp_c"] = df["temp_c"].interpolate(limit_direction="both")
    df["humidity"] = df["humidity"].fillna(df["humidity"].median())
    return df


def train_anomaly(limit=12000):
    df = load_weather(limit)
    X = df[FEATURES].values
    model = IsolationForest(contamination=0.03, n_estimators=80, random_state=42)
    model.fit(X)
    preds = model.predict(X)
    scores = model.decision_function(X)
    model_path = MODELS_DIR / "anomaly_model.joblib"
    import joblib
    joblib.dump(model, model_path)
    anom = df[preds == -1]
    execute("DELETE FROM anomalies")
    for _, r in anom.iterrows():
        execute("INSERT INTO anomalies (station, ts, score, features) VALUES (?,?,?,?)",
                (r["station"], str(r["date"]), round(float(scores[int(r.name)]), 4),
                 json.dumps({f: round(float(r[f]), 2) for f in FEATURES})))
    return {"model": "isolation_forest", "path": str(model_path), "samples": len(df),
            "anomalies_detected": int((preds == -1).sum()),
            "mean_score": round(float(scores.mean()), 4)}


def train_forecast(days=365, horizon=30, limit=12000):
    df = load_weather(limit).groupby("date").agg({"temp_c": "mean", "co2_ppm": "mean"}).reset_index()
    df = df.sort_values("date").tail(days).reset_index(drop=True)
    t = np.arange(len(df)).reshape(-1, 1)
    phi = 2 * np.pi * t / 365.0
    X = np.hstack([t, np.sin(phi), np.cos(phi)])
    model = LinearRegression()
    model.fit(X, df["temp_c"].values)
    t_future = np.arange(len(df), len(df) + horizon).reshape(-1, 1)
    phi_f = 2 * np.pi * t_future / 365.0
    Xf = np.hstack([t_future, np.sin(phi_f), np.cos(phi_f)])
    pred = model.predict(Xf)
    import joblib
    joblib.dump(model, MODELS_DIR / "forecast_model.joblib")
    last_date = pd.to_datetime(df["date"].iloc[-1])
    payload = {"trained_on": len(df), "model": "seasonal_linear_regression", "points": [
        {"date": str(last_date + pd.Timedelta(days=i + 1)), "temp_c": round(float(p), 2)}
        for i, p in enumerate(pred)]}
    execute("INSERT INTO forecasts (model, target, payload) VALUES (?,?,?)",
            ("forecast", "temp_c", json.dumps(payload)))
    return payload


def correlation(limit=12000):
    df = load_weather(limit)
    df = df.dropna(subset=["temp_c", "co2_ppm"])
    r = df["temp_c"].corr(df["co2_ppm"])
    return {"pearson_r": round(float(r), 4), "samples": len(df),
            "interpretation": "Strong positive" if r > 0.6 else "Moderate" if r > 0.3 else "Weak",
            "note": "Correlation is not causation; warming trend and CO2 rise co-occur."}


def latest_forecast():
    row = q1("SELECT * FROM forecasts ORDER BY id DESC LIMIT 1")
    return json.loads(row["payload"]) if row else None


def list_anomalies(limit=200):
    from ..db import q
    return q("SELECT * FROM anomalies ORDER BY id DESC LIMIT ?", (limit,))