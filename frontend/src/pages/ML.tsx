import { useEffect, useState } from "react";
import { api } from "../api";
import { Card } from "./Dashboard";
import { Line, LineChart, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ScatterChart, Scatter, ZAxis } from "recharts";

export default function ML() {
  const [corr, setCorr] = useState<any>(null);
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [forecast, setForecast] = useState<any>(null);
  const [training, setTraining] = useState("");
  const [msg, setMsg] = useState("");

  const load = () => {
    api("/ml/correlation").then(setCorr).catch(() => {});
    api("/ml/anomalies?limit=300").then(setAnomalies).catch(() => {});
    api("/ml/forecast/latest").then(setForecast).catch(() => {});
  };
  useEffect(load, []);

  async function train(what: string) {
    setTraining(what);
    setMsg("");
    try {
      const r = await api(`/ml/train/${what}`, { method: "POST", body: { limit: 8000 } });
      setMsg(what === "anomaly" ? `Anomaly model trained: ${r.samples} samples, ${r.anomalies_detected} anomalies detected (IsolationForest)` : `Forecast model trained on ${r.trained_on} daily points → 30-day projection`);
      load();
    } catch (e) {
      setMsg(`Training failed: ${(e as Error).message}`);
    }
    setTraining("");
  }

  return (
    <div className="page">
      <h1>Machine Learning Lab</h1>
      <p className="muted">Predictive analysis: anomaly detection, trend forecasting, correlation — models retrain on latest data</p>

      <div className="actions">
        <button className="btn primary" disabled={!!training} onClick={() => train("anomaly")}>
          {training === "anomaly" ? "Training…" : "Train anomaly detection (IsolationForest)"}
        </button>
        <button className="btn" disabled={!!training} onClick={() => train("forecast")}>
          {training === "forecast" ? "Training…" : "Train temperature forecast (30 days)"}
        </button>
      </div>
      {msg && <div className="banner">{msg}</div>}

      <div className="grid2">
        <Card title="Anomaly detection — flagged readings">
          {anomalies.length === 0 && <p className="muted">Train the anomaly model first.</p>}
          <ResponsiveContainer width="100%" height={240}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="score" name="Anomaly score" stroke="#9ca3af" fontSize={11} />
              <YAxis dataKey="features" hide />
              <ZAxis dataKey="id" range={[30, 30]} />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151" }} cursor={{ strokeDasharray: "3 3" }} />
              <Scatter data={anomalies} fill="#ff5c5c" />
            </ScatterChart>
          </ResponsiveContainer>
          <table className="tbl">
            <thead><tr><th>Station</th><th>Date</th><th>Score</th><th>Features</th></tr></thead>
            <tbody>
              {anomalies.slice(0, 8).map((a) => (
                <tr key={a.id}>
                  <td>{a.station}</td>
                  <td>{a.ts}</td>
                  <td>{a.score}</td>
                  <td className="muted">{a.features}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <Card title="Temperature forecast — next 30 days">
          {forecast ? (
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={forecast.points}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="date" stroke="#9ca3af" fontSize={10} tickFormatter={(d: string) => d.slice(5, 10)} />
                <YAxis stroke="#9ca3af" fontSize={11} unit="°C" />
                <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151" }} />
                <Line type="monotone" dataKey="temp_c" stroke="#a78bfa" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          ) : <p className="muted">Train the forecast model first.</p>}
          {corr && (
            <div className="corr-box">
              <b>Temperature ↔ CO₂ correlation: r = {corr.pearson_r}</b> ({corr.interpretation})
              <div className="muted dim">{corr.note}</div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}