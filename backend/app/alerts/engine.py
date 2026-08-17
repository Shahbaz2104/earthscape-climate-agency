"""Alert engine: threshold rules evaluated against streamed readings + batch results."""
from ..db import q, execute

OPERATORS = {"gt": lambda v, t: v > t, "gte": lambda v, t: v >= t,
             "lt": lambda v, t: v < t, "lte": lambda v, t: v <= t,
             "eq": lambda v, t: v == t}


def seed_rules():
    if not q("SELECT COUNT(*) c FROM rules") or q("SELECT COUNT(*) c FROM rules")[0]["c"] == 0:
        execute("INSERT INTO rules (metric, operator, threshold, severity, enabled, description) VALUES (?,?,?,?,?,?)",
                ("temp_c", "gt", 35.0, "critical", 1, "Heatwave threshold: temperature above 35C"))
        execute("INSERT INTO rules (metric, operator, threshold, severity, enabled, description) VALUES (?,?,?,?,?,?)",
                ("temp_c", "lt", -15.0, "warning", 1, "Extreme cold below -15C"))
        execute("INSERT INTO rules (metric, operator, threshold, severity, enabled, description) VALUES (?,?,?,?,?,?)",
                ("co2_ppm", "gt", 420.0, "warning", 1, "CO2 concentration above 420 ppm"))
        execute("INSERT INTO rules (metric, operator, threshold, severity, enabled, description) VALUES (?,?,?,?,?,?)",
                ("humidity", "lt", 20.0, "info", 1, "Drought indicator: humidity below 20%"))


def check_rules(event):
    """Returns list of fired (rule, value) pairs for a streamed reading."""
    fired = []
    for rule in q("SELECT * FROM rules WHERE enabled=1"):
        v = event.get(rule["metric"])
        if v is None:
            continue
        op = OPERATORS.get(rule["operator"])
        if op and op(v, rule["threshold"]):
            fired.append(rule)
    return fired


def notify(title, body, severity="info", user_id=None):
    execute("INSERT INTO notifications (user_id, title, body, severity) VALUES (?,?,?,?)",
            (user_id, title, body, severity))