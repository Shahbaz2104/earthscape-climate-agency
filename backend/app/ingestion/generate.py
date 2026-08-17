"""Synthetic climate dataset generation (realistic seasonal patterns + missing data)."""
import math, random
import numpy as np
import pandas as pd
from pathlib import Path
from ..config import DATASETS_DIR

REGIONS = {
    "North America": [(34.0, -118.2, "Los Angeles"), (40.7, -74.0, "New York"), (61.2, -149.9, "Anchorage")],
    "Europe": [(51.5, -0.12, "London"), (48.8, 2.35, "Paris"), (60.2, 24.9, "Helsinki")],
    "Asia": [(35.7, 139.7, "Tokyo"), (28.6, 77.2, "Delhi"), (31.2, 121.5, "Shanghai")],
    "Africa": [(-1.29, 36.8, "Nairobi"), (30.0, 31.2, "Cairo"), (-33.9, 18.4, "Cape Town")],
    "South America": [(-23.5, -46.6, "Sao Paulo"), (-33.4, -70.7, "Santiago"), (-3.7, -38.5, "Fortaleza")],
    "Oceania": [(-33.9, 151.2, "Sydney"), (-37.8, 144.9, "Melbourne"), (-41.3, 174.8, "Wellington")],
}


def _seasonal_temp(lat, day, base, warming):
    amp = max(2.0, 18.0 - abs(lat) * 0.3)
    return base + warming - amp * math.cos(2 * math.pi * (day - 15) / 365)


def generate_all(rows_per_station=600, years=(2015, 2025)):
    rng = random.Random(42)
    stations = []
    for region, cities in REGIONS.items():
        for lat, lon, city in cities:
            stations.append({"station_id": f"{region[:3].upper()}{len(stations)+1:02d}",
                             "station": city, "region": region, "lat": lat, "lon": lon,
                             "base": 5.0 + (lat + 90) * 0.28, "warming": rng.uniform(0.8, 2.4)})

    rows = []
    for s in stations:
        for i in range(rows_per_station):
            year = rng.randint(*years)
            day = rng.randint(1, 365)
            ts = f"{year}-{day:03d}"
            temp = _seasonal_temp(s["lat"], day, s["base"], s["warming"] * (year - years[0]) / (years[1] - years[0]))
            temp += rng.gauss(0, 2.2)
            co2 = 398 + (year - 2015) * 2.35 + rng.gauss(0, 1.5)
            rows.append({
                "station_id": s["station_id"], "station": s["station"], "region": s["region"],
                "lat": s["lat"], "lon": s["lon"], "date": ts,
                "temp_c": round(temp, 2), "humidity": round(rng.uniform(30, 90), 1),
                "pressure_hpa": round(1013 + rng.gauss(0, 8), 1), "co2_ppm": round(co2, 1),
            })
            if rng.random() < 0.018:
                rows[-1]["temp_c"] = None
            if rng.random() < 0.012:
                rows[-1]["humidity"] = None

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], format="%Y-%j")
    df = df.sort_values(["station", "date"])
    df.to_csv(DATASETS_DIR / "weather_stations.csv", index=False)

    years_list = list(range(years[0], years[1]))
    countries = [city[2] for cities in REGIONS.values() for city in cities]
    emis = pd.DataFrame({
        "country": countries * len(years_list),
        "year": sorted(years_list * len(countries)),
    })
    emis = emis.sort_values(["country", "year"]).reset_index(drop=True)
    rng2 = random.Random(7)
    emis["co2_mt"] = emis["country"].map(
        {c: rng2.uniform(20, 9000) for c in emis["country"].unique()}) * (1 + (emis["year"] - years[0]) * 0.015)
    emis["co2_mt"] = emis["co2_mt"].round(1)
    emis.to_csv(DATASETS_DIR / "emissions.csv", index=False)

    sat_rows = []
    for i in range(3000):
        lat, lon = rng.uniform(-60, 70), rng.uniform(-180, 180)
        year = rng.randint(*years)
        ndvi = max(0, min(1, 0.55 + rng.gauss(0, 0.15) + (1 if lat < -23 or lat > 23 else 0.1)))
        sat_rows.append({"tile_id": f"T{i+1:05d}", "lat": round(lat, 2), "lon": round(lon, 2),
                         "date": f"{year}-{rng.randint(1,365):03d}", "ndvi": round(ndvi, 3),
                         "land_temp_c": round(-15 + (lat + 60) * 0.55 + rng.gauss(0, 4), 2)})
    pd.DataFrame(sat_rows).to_csv(DATASETS_DIR / "satellite.csv", index=False)
    return {
        "weather_stations.csv": len(df),
        "emissions.csv": len(emis),
        "satellite.csv": len(sat_rows),
    }


if __name__ == "__main__":
    print(generate_all())