from fastapi import APIRouter, Depends
from . import models
from ..auth.deps import get_current_user

router = APIRouter(prefix="/ml", tags=["ml"])


@router.post("/train/anomaly")
def train_anomaly(user=Depends(get_current_user), body: dict = None):
    return models.train_anomaly(limit=(body or {}).get("limit") or 12000)


@router.post("/train/forecast")
def train_forecast(user=Depends(get_current_user), body: dict = None):
    b = body or {}
    return models.train_forecast(days=b.get("days") or 365, horizon=b.get("horizon") or 30,
                                 limit=b.get("limit") or 12000)


@router.get("/correlation")
def correlation(user=Depends(get_current_user)):
    return models.correlation()


@router.get("/anomalies")
def anomalies(user=Depends(get_current_user), limit: int = 200):
    return models.list_anomalies(limit)


@router.get("/forecast/latest")
def latest_forecast(user=Depends(get_current_user)):
    return models.latest_forecast()