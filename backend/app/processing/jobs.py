"""Climate MapReduce jobs. Map/reduce funcs are module-level so workers can pickle them."""
import statistics


def _row(header, line):
    parts = line.split(",")
    cols = [h.strip() for h in header.split(",")]
    if len(parts) != len(cols):
        return {}
    return dict(zip(cols, parts))


def _f(row, *names):
    for n in names:
        if n in row and row[n] not in (None, ""):
            return row[n]
    return None


def _temp_trends_map(key, value):
    header, line = value
    row = _row(header, line)
    region, date = _f(row, "region"), _f(row, "date", "timestamp")
    if not region or not date:
        return []
    try:
        t = float(_f(row, "temp_c"))
    except (TypeError, ValueError):
        return [(f"{region}::{date[:4]}", None)]
    return [(f"{region}::{date[:4]}", t)]


def _temp_trends_reduce(key, values):
    region, year = key.split("::")
    ok = [v for v in values if v is not None]
    return {"region": region, "year": year, "count": len(values), "missing": len(values) - len(ok),
            "avg_temp_c": round(statistics.mean(ok), 2) if ok else None,
            "min_temp_c": round(min(ok), 2) if ok else None,
            "max_temp_c": round(max(ok), 2) if ok else None}


def _co2_emissions_map(key, value):
    header, line = value
    row = _row(header, line)
    country, year = _f(row, "country"), _f(row, "year")
    try:
        co2 = float(_f(row, "co2_mt", "co2_ppm"))
    except (TypeError, ValueError):
        return []
    if not country or not year:
        return []
    return [((country, year), co2)]


def _co2_emissions_reduce(key, values):
    country, year = key
    return {"country": country, "year": year, "total_co2_mt": round(sum(values), 1), "readings": len(values)}


def _anomaly_counts_map(key, value):
    header, line = value
    row = _row(header, line)
    station = _f(row, "station_id", "station")
    try:
        t = float(_f(row, "temp_c"))
    except (TypeError, ValueError):
        return []
    return [(station, t)]


def _anomaly_counts_reduce(key, values):
    ok = [v for v in values if v is not None]
    if len(ok) < 5:
        return {"station": key, "count": len(values), "anomalies": 0}
    mu, sd = statistics.mean(ok), statistics.stdev(ok) or 1.0
    anom = [v for v in ok if abs(v - mu) > 3 * sd]
    return {"station": key, "count": len(values), "anomalies": len(anom),
            "rate_pct": round(100 * len(anom) / len(ok), 2), "mean_temp_c": round(mu, 2)}


def _correlation_map(key, value):
    header, line = value
    row = _row(header, line)
    date = _f(row, "date", "timestamp")
    try:
        t, c = float(_f(row, "temp_c")), float(_f(row, "co2_ppm"))
    except (TypeError, ValueError):
        return []
    if not date:
        return []
    return [(date[:4], (t, c))]


def _correlation_reduce(key, values):
    ts, cs = zip(*values)
    n = len(ts)
    mt, mc = sum(ts) / n, sum(cs) / n
    cov = sum((a - mt) * (b - mc) for a, b in zip(ts, cs)) / n
    st, sc = (sum((a - mt) ** 2 for a in ts) / n) ** 0.5, (sum((b - mc) ** 2 for b in cs) / n) ** 0.5
    r = cov / (st * sc) if st and sc else 0.0
    return {"year": key, "samples": n, "avg_temp_c": round(mt, 2), "avg_co2_ppm": round(mc, 2),
            "pearson_r": round(r, 4)}


class _Job:
    name = ""
    def map(self, key, value):
        return getattr(globals(), f"_{self.name}_map")(key, value)
    def reduce(self, key, values):
        return getattr(globals(), f"_{self.name}_reduce")(key, values)


class temp_trends(_Job):
    name = "temp_trends"


class co2_emissions(_Job):
    name = "co2_emissions"


class anomaly_counts(_Job):
    name = "anomaly_counts"


class correlation(_Job):
    name = "correlation"