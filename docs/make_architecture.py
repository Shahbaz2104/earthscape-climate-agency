#!/usr/bin/env python3
"""Render the EarthScape Climate Agency architecture diagram (docs/architecture.png).

Reproducible: run `.venv/bin/python ../docs/make_architecture.py` from backend/,
or `.venv/bin/python docs/make_architecture.py` from the project root.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = __file__.rsplit("/", 1)[0] + "/architecture.png"

NAVY = "#0f2a43"
BLUE = "#4da3ff"
GREEN = "#1f9d6b"
PURPLE = "#7c5cd6"
AMBER = "#d97706"
RED = "#d64545"
GRAY = "#f4f6f9"
BORDER = "#c8d2de"
TEXT = "#24344a"
MUTED = "#5b6b80"

fig, ax = plt.subplots(figsize=(16, 11), dpi=200)
ax.set_xlim(0, 100)
ax.set_ylim(0, 68)
ax.axis("off")


def box(x, y, w, h, title, lines=None, fc=GRAY, ec=BORDER, title_color=NAVY, fs=8.6, tfs=10.5, lw=1.4):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.35,rounding_size=1.2",
                       linewidth=lw, edgecolor=ec, facecolor=fc, zorder=2)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h - 1.8, title, ha="center", va="center", fontsize=tfs,
            fontweight="bold", color=title_color, zorder=3)
    if lines:
        for i, ln in enumerate(lines):
            ax.text(x + w / 2, y + h - 4.2 - i * 2.1, ln, ha="center", va="center",
                    fontsize=fs, color=TEXT, zorder=3)


def arrow(x1, y1, x2, y2, label=None, color=BLUE, ls="-", lx=0, ly=0.9, fs=7.6):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=13,
                        linewidth=1.5, color=color, linestyle=ls, zorder=1)
    ax.add_patch(a)
    if label:
        ax.text((x1 + x2) / 2 + lx, (y1 + y2) / 2 + ly, label, ha="center", va="center",
                fontsize=fs, color=MUTED, zorder=3,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"))


ax.text(50, 66.2, "EarthScape Climate Agency — System Architecture",
        ha="center", fontsize=15, fontweight="bold", color=NAVY)
ax.text(50, 64.0, "Climate big-data analytics platform", ha="center", fontsize=10.5, color=MUTED)

# --- Layer 1: data sources ---
box(4, 57, 18, 5.2, "Satellites", ["imagery, NDVI"], fc="#e8f2fd", ec=BORDER)
box(26, 57, 18, 5.2, "Weather Stations", ["temp, humidity, CO2"], fc="#e8f2fd", ec=BORDER)
box(48, 57, 18, 5.2, "Environmental Sensors", ["real-time readings"], fc="#e8f2fd", ec=BORDER)
box(70, 57, 26, 5.2, "Data Sources", ["historical + real-time", "CSV · JSON · NetCDF"], fc="#dcebf9", ec=BORDER)

arrow(13, 57, 13, 54.2, label="")
arrow(35, 57, 35, 54.2, label="")
arrow(57, 57, 57, 54.2, label="")
arrow(35, 54.8, 50, 54.8, label="ingestion API", lx=0, ly=0.4)
arrow(65, 54.8, 77, 54.8, label="generator + simulator", lx=0, ly=0.4)

# --- Layer 2: React SPA ---
box(6, 44.5, 88, 7.6, "React SPA (Vite · TypeScript) — port 5173",
    ["Dashboard · Climate Data · Processing · ML Lab · Alerts · Monitoring · Support · Admin",
     "interactive dashboards (Recharts) · role-aware UI (admin / analyst)"],
    fc="#fdeee6", ec="#e8b48f", title_color="#a8541e")

arrow(50, 44.5, 50, 41.8, label="REST (JSON, JWT Bearer) + WebSocket /ws/stream", lx=0, ly=-0.6, color=BLUE)

# --- Layer 3: FastAPI ---
box(6, 30.5, 88, 9.0, "FastAPI Backend — port 8000",
    ["auth (JWT + RBAC)  ·  ingestion  ·  processing (MapReduce)  ·  ml (scikit-learn)",
     "alerts (threshold rules)  ·  monitoring  ·  support (tickets)"],
    fc="#edf7f2", ec="#9fd0b8", title_color=GREEN)

# --- Layer 4: storage & platform services ---
box(4, 14, 30, 12.5, "Emulated HDFS", ["NameNode (metadata)", "DataNodes · 2× replication",
     "1 MB blocks · encrypted at rest", "load-balanced reads/writes", "fault-tolerant reads"],
    fc="#f3eefe", ec="#b8a2e6", title_color=PURPLE)
box(38, 14, 24, 12.5, "SQLite", ["users · jobs · rules", "notifications · tickets",
     "forecasts · anomalies"], fc="#fdf3f0", ec="#e8b0a2", title_color=RED)
box(66, 14, 30, 12.5, "StreamHub (real-time)", ["sensor simulator (2 s tick)",
     "pub/sub + WebSocket push", "windowed flush → batch CSV", "threshold rule evaluation"],
    fc="#fbf7ea", ec="#e3cd8a", title_color=AMBER)

# --- ML artifacts ---
box(66, 3.5, 30, 8.0, "ML Artifacts", ["anomaly_model.joblib", "forecast_model.joblib",
     "anomalies · forecasts tables", "30-day temperature projections"], fc="#eef2fb", ec="#b8c8ea", title_color=NAVY)

# Arrows: api -> services
arrow(50, 30.5, 50, 28.2, label="service calls", lx=0, ly=-0.6, color=GREEN)
arrow(20, 26.5, 20, 28.2, label="HDFS I/O (block store)", lx=6.5, ly=0.6, color=PURPLE)
arrow(50, 26.5, 50, 28.2, label="state", lx=-4.5, ly=0.6, color=RED)
arrow(80, 26.5, 80, 28.2, label="stream events", lx=4.5, ly=0.6, color=AMBER)
arrow(80, 14, 80, 11.5, label="model persist / retrain", lx=6, ly=0.5, color=NAVY)

# --- MapReduce annotation ---
box(4, 3.5, 58, 8.0, "MapReduce Engine (parallel processing)",
    ["input split → map ×2 workers (spawn) → shuffle/sort → reduce",
     "jobs: temp_trends · co2_emissions · anomaly_counts · correlation"],
    fc="#eef6fb", ec="#b8d4ea", title_color=NAVY)
arrow(19, 14, 19, 11.5, label="read splits", lx=-2.5, ly=-0.5, color=PURPLE)
arrow(33, 11.5, 46, 11.5, label="", color=GRAY)
arrow(46, 14, 46, 11.5, label="results → UI tables/charts", lx=8.5, ly=-0.5, color=GREEN)

# legend
lx0, ly0 = 3, 0.4
ax.text(lx0, ly0 + 1.6, "Legend:", fontsize=8.5, fontweight="bold", color=TEXT)
leg = [("Data sources / ingest", BLUE), ("Frontend / dashboard", "#a8541e"),
       ("Backend services", GREEN), ("Storage & streaming", PURPLE),
       ("ML & processing", NAVY), ("Alerts / state", RED)]
x = lx0
for label, c in leg:
    ax.plot([x, x + 2.4], [ly0, ly0], color=c, linewidth=5, solid_capstyle="round")
    ax.text(x + 3.0, ly0, label, fontsize=7.8, color=MUTED, va="center")
    x += len(label) * 1.55 + 7.5

fig.savefig(OUT, bbox_inches="tight", facecolor="white")
print(f"Saved {OUT}")
