import { useEffect, useState } from "react";
import { api, fmtNum, fmtSize, severityColor, WS_URL } from "../api";
import { Line, LineChart, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

export default function Dashboard() {
  const [overview, setOverview] = useState<any>(null);
  const [trends, setTrends] = useState<any[]>([]);
  const [anomalies, setAnomalies] = useState(0);
  const [stream, setStream] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [notifs, setNotifs] = useState<any[]>([]);

  useEffect(() => {
    api("/monitor/overview").then(setOverview).catch(() => {});
    api("/ml/anomalies?limit=1000").then((a) => setAnomalies(a.length)).catch(() => {});
    api("/alerts/notifications").then(setNotifs).catch(() => {});
  }, []);

  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/stream`);
    ws.onmessage = (e) => {
      const ev = JSON.parse(e.data);
      if (ev.type === "reading") {
        setStream((s) => [...s.slice(-59), ev]);
        setTrends((t) => {
          const last = t[t.length - 1];
          const row = { time: ev.ts.slice(11, 19), temp: ev.temp_c };
          if (last && last.time === row.time) return [...t.slice(0, -1), row];
          return [...t.slice(-29), row];
        });
      } else if (ev.type === "alert") {
        setAlerts((a) => [{ ...ev, ts: ev.ts }, ...a].slice(0, 8));
      }
    };
    return () => ws.close();
  }, []);

  return (
    <div className="page">
      <h1>Climate Dashboard</h1>
      <p className="muted">Live monitoring of the EarthScape platform and global climate signals</p>

      <div className="stats">
        <Stat label="HDFS files" value={fmtNum(overview?.hdfs?.files)} sub={`${fmtSize(overview?.hdfs?.size_bytes || 0)} stored · ${overview?.hdfs?.blocks} blocks`} />
        <Stat label="Records processed" value={fmtNum(overview?.records_processed)} sub={`${overview?.jobs?.total} jobs run`} />
        <Stat label="Anomalies detected" value={fmtNum(anomalies)} sub="IsolationForest model" />
        <Stat label="Unread alerts" value={fmtNum(overview?.unread)} sub={`${fmtNum(overview?.notifications)} total notifications`} />
      </div>

      <div className="grid2">
        <Card title="Live temperature — real-time stream (WebSocket)">
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={trends}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="time" stroke="#9ca3af" fontSize={11} />
              <YAxis stroke="#9ca3af" fontSize={11} unit="°C" />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151" }} />
              <Line type="monotone" dataKey="temp" stroke="#34d399" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
          <div className="feed">
            {stream.slice(-5).reverse().map((r, i) => (
              <div key={i} className="feed-row">
                <b>{r.station}</b> <span className="muted">{r.region}</span>
                <span className="val">{r.temp_c}°C</span>
                <span className="val dim">{r.co2_ppm} ppm</span>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Live alerts">
          {alerts.length === 0 && <p className="muted">No alerts yet — the engine watches every streamed reading.</p>}
          {alerts.map((a, i) => (
            <div key={i} className="alert-line" style={{ borderLeftColor: severityColor(a.severity) }}>
              <b>{a.title}</b>
              <div>{a.station}: {a.value} vs threshold {a.threshold}</div>
            </div>
          ))}
        </Card>
      </div>

      <div className="grid2">
        <Card title="Latest notifications">
          {notifs.slice(0, 8).map((n) => (
            <div key={n.id} className="alert-line" style={{ borderLeftColor: severityColor(n.severity) }}>
              <b>{n.title}</b>
              <div>{n.body}</div>
            </div>
          ))}
          {notifs.length === 0 && <p className="muted">No notifications yet.</p>}
        </Card>
        <Card title="Platform health">
          {overview && (
            <table className="tbl">
              <tbody>
                <tr><td>Jobs succeeded</td><td>{overview.jobs.total - overview.jobs.failed} / {overview.jobs.total}</td></tr>
                <tr><td>HDFS replication</td><td>{overview.hdfs.replication}x fault tolerance</td></tr>
                <tr><td>Open support tickets</td><td>{overview.tickets_open}</td></tr>
                <tr><td>Registered users</td><td>{overview.users}</td></tr>
                <tr><td>Stored anomalies</td><td>{overview.anomalies}</td></tr>
              </tbody>
            </table>
          )}
        </Card>
      </div>
    </div>
  );
}

function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value || "—"}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}

export function Card({ title, children, wide }: { title: string; children: React.ReactNode; wide?: boolean }) {
  return (
    <div className={`card ${wide ? "wide" : ""}`}>
      <h3>{title}</h3>
      {children}
    </div>
  );
}

export { severityColor };