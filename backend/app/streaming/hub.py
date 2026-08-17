"""In-process streaming hub + sensor simulator + windowed flush into batch storage."""
import json, random, threading, time
from ..config import STREAM_INTERVAL_SEC, FLUSH_WINDOW_SEC, DATASETS_DIR
from ..storage.hdfs import hdfs

STATIONS = [
    ("North America", "New York", 12.0), ("Europe", "London", 11.0), ("Asia", "Tokyo", 16.0),
    ("Africa", "Nairobi", 19.0), ("South America", "Sao Paulo", 21.0), ("Oceania", "Sydney", 18.0),
    ("North America", "Anchorage", 2.0), ("Asia", "Delhi", 25.0),
]


class StreamHub:
    def __init__(self):
        self._subs = []
        self._lock = threading.Lock()
        self.readings = 0
        self._started = False
        self._flush_file = None

    def subscribe(self, callback):
        with self._lock:
            self._subs.append(callback)
        return lambda: self._subs.remove(callback) if callback in self._subs else None

    def publish(self, event: dict):
        event = dict(event)
        event["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            subs = list(self._subs)
        for cb in subs:
            try:
                cb(event)
            except Exception:
                pass
        self.readings += 1

    def start_simulator(self):
        if self._started:
            return
        self._started = True
        self._flush_file = DATASETS_DIR / "live_sensor_stream.csv"
        if not self._flush_file.exists():
            self._flush_file.write_text("region,station,temp_c,co2_ppm,humidity,ts\n")
        threading.Thread(target=self._sim_loop, daemon=True).start()

    def _sim_loop(self):
        rng = random.Random()
        window = []
        while True:
            region, station, base = rng.choice(STATIONS)
            t = base + rng.gauss(0, 2.5)
            if rng.random() < 0.004:
                t += rng.uniform(8, 14)  # simulate an extreme event
            reading = {"region": region, "station": station,
                       "temp_c": round(t, 2),
                       "co2_ppm": round(398 + rng.gauss(0, 2), 1),
                       "humidity": round(rng.uniform(30, 90), 1)}
            self.publish({"type": "reading", **reading})
            window.append(reading)
            if len(window) >= FLUSH_WINDOW_SEC / STREAM_INTERVAL_SEC:
                with open(self._flush_file, "a") as f:
                    for r in window:
                        f.write(f"{r['region']},{r['station']},{r['temp_c']},{r['co2_ppm']},{r['humidity']},{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                window = []
            time.sleep(STREAM_INTERVAL_SEC)


hub = StreamHub()