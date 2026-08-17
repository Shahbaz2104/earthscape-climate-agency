import { useEffect, useState } from "react";
import { api } from "../api";
import { Card } from "./Dashboard";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";

export default function Processing() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [result, setResult] = useState<any>(null);
  const [running, setRunning] = useState<string | null>(null);
  const [error, setError] = useState("");

  const load = () => {
    api("/hdfs/jobs").then(setJobs).catch(() => {});
    api("/hdfs/history").then(setHistory).catch(() => {});
  };
  useEffect(load, []);

  async function run(id: string) {
    setRunning(id);
    setError("");
    setResult(null);
    try {
      const r = await api(`/hdfs/jobs/${id}/run`, { method: "POST", body: {} });
      setResult(r);
    } catch (e) {
      setError((e as Error).message);
    }
    setRunning(null);
    load();
  }

  const isTrend = result?.job === "temp_trends";
  const isCorr = result?.job === "correlation";

  return (
    <div className="page">
      <h1>Batch Processing — Hadoop MapReduce</h1>
      <p className="muted">Parallel map → shuffle/sort → reduce jobs over data split across distributed nodes</p>

      <div className="stats">
        <Stat label="Jobs run" value={`${history.length}`} />
        <Stat label="Failed" value={`${history.filter((h) => h.status === "failed").length}`} />
        <Stat label="Workers" value="2" />
        <Stat label="Last duration" value={history[0] ? `${history[0].duration_ms} ms` : "—"} />
      </div>

      <div className="grid2">
        <Card title="Available jobs">
          {jobs.map((j) => (
            <div key={j.id} className="job-row">
              <div>
                <b>{j.name}</b>
                <div className="muted">{j.desc}</div>
                <div className="muted dim">input: {j.input}</div>
              </div>
              <button className="btn primary sm" disabled={!!running} onClick={() => run(j.id)}>
                {running === j.id ? "Running…" : "Run"}
              </button>
            </div>
          ))}
          {error && <div className="error">{error}</div>}
        </Card>

        <Card title="Job history (monitoring)">
          <table className="tbl">
            <thead><tr><th>Job</th><th>Status</th><th>Duration</th><th>Records</th></tr></thead>
            <tbody>
              {history.map((h) => (
                <tr key={h.id}>
                  <td>{h.name}</td>
                  <td><span className={`pill ${h.status}`}>{h.status}</span></td>
                  <td>{h.duration_ms ? `${h.duration_ms} ms` : "—"}</td>
                  <td>{h.records ?? "—"}</td>
                </tr>
              ))}
              {history.length === 0 && <tr><td colSpan={4} className="muted">Run a job to see history.</td></tr>}
            </tbody>
          </table>
        </Card>
      </div>

      {result && (
        <Card wide title={`Result — ${result.job} (${result.duration_ms} ms, ${result.split_count} splits, ${result.map_output} map outputs, ${result.reduce_groups} groups)`}>
          {isTrend && (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={result.results.slice(0, 45)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="region" stroke="#9ca3af" fontSize={10} interval={0} angle={-30} height={60} />
                <YAxis stroke="#9ca3af" fontSize={11} unit="°C" />
                <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151" }} />
                <Legend />
                <Bar dataKey="avg_temp_c" fill="#34d399" name="Avg temp" />
                <Bar dataKey="max_temp_c" fill="#f59e0b" name="Max temp" />
              </BarChart>
            </ResponsiveContainer>
          )}
          {isCorr && (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={result.results}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="year" stroke="#9ca3af" fontSize={11} />
                <YAxis stroke="#9ca3af" fontSize={11} domain={[-1, 1]} />
                <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151" }} />
                <Bar dataKey="pearson_r" fill="#4da3ff" name="Temp↔CO2 correlation" />
              </BarChart>
            </ResponsiveContainer>
          )}
          <table className="tbl">
            <thead>
              <tr>{Object.keys(result.results[0] || {}).map((k) => <th key={k}>{k}</th>)}</tr>
            </thead>
            <tbody>
              {result.results.slice(0, 30).map((r: any, i: number) => (
                <tr key={i}>{Object.values(r).map((v: any, j: number) => <td key={j}>{v}</td>)}</tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
    </div>
  );
}