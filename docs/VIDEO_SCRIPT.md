# Demo Video Script (≈ 4–5 minutes)

A screen-capture walkthrough has been generated as **`docs/demo_video.webm`** (28 s slideshow of
the live pages). Record with a screen recorder (OBS/SimpleScreenRecorder) at 1080p for the full
narrated version. Start both servers first.

## 0:00 – Intro (voiceover)
> "This is the EarthScape Climate Agency platform — an end-to-end system for ingesting,
> processing, analyzing and visualizing climate data. It covers HDFS-style storage, Hadoop
> MapReduce batch processing, real-time streaming, machine learning, alerting, monitoring and
> role-based security."

## 0:20 – Login & roles
- Open http://localhost:5173 — sign in as `admin / admin123`
- Show sidebar: 8 modules. Mention RBAC: analysts can't see Admin.

## 0:45 – Dashboard (live)
- Point to the **live temperature chart** — "this is a WebSocket stream from simulated
  sensors around the world, every 2 seconds".
- Wait for an alert card to appear (they fire frequently — CO2 threshold).

## 1:30 – Climate Data / HDFS
- Open **Climate Data** → stats (files, size, blocks, 2x replication).
- Click **Generate demo datasets** (or show existing files).
- Click a file → preview. Click **corrupt** on a file → "I just killed one replica of a block;
  the file is still readable thanks to replication — this is HDFS fault tolerance."

## 2:30 – MapReduce processing
- Open **Processing** → click **Run** on `temp_trends`.
- Wait for result: "10,605 map outputs, 66 groups, ~1.3 seconds, 2 input splits, parallel
  map → shuffle → reduce." Show the bar chart + table.
- Run `correlation` → show the temp↔CO2 chart. Show **job history** with runtimes.

## 3:30 – Machine learning
- Open **ML Lab** → train **anomaly detection** → show detected anomalies table.
- Train **forecast** → show 30-day temperature projection chart.
- Point at the **correlation panel**.

## 4:00 – Alerts, monitoring, support
- **Alerts**: show rules (temp > 35°C critical, CO2 > 400 ppm), add a rule live, show inbox.
- **Monitoring**: CPU/memory/disk/uptime, click **backup now**, show backup list.
- **Support**: submit a ticket; as admin, move it to resolved (switch to analyst account to
  show restricted access).

## 4:50 – Outro
> "Batch + streaming integration, retrainable models, configurable alerts, monitoring and
> documentation — all running on an emulated Hadoop stack that can be swapped for a real
> cluster. That's EarthScape."
