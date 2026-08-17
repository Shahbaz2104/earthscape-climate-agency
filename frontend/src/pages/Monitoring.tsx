import { useEffect, useState } from "react";
import { api, fmtSize } from "../api";
import { Card } from "./Dashboard";

export default function Monitoring() {
  const [sys, setSys] = useState<any>(null);
  const [backups, setBackups] = useState<any[]>([]);
  const [lb, setLb] = useState<any>(null);
  const [bkStatus, setBkStatus] = useState<any>(null);
  const [msg, setMsg] = useState("");

  const load = () => {
    api("/monitor/system").then(setSys).catch(() => {});
    api("/monitor/backups").then(setBackups).catch(() => {});
    api("/monitor/lb").then(setLb).catch(() => {});
    api("/monitor/backup/status").then(setBkStatus).catch(() => {});
  };
  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, []);

  async function backup() {
    const r = await api("/monitor/backup", { method: "POST" });
    setMsg(`Backup created: ${r.backup} → ${r.location}`);
    load();
  }

  const uptimeH = sys ? Math.floor(sys.uptime_sec / 3600) : 0;
  const uptimeM = sys ? Math.floor((sys.uptime_sec % 3600) / 60) : 0;

  return (
    <div className="page">
      <h1>Performance Monitoring</h1>
      <p className="muted">Resource utilization, processing times and reliability (99% uptime target)</p>

      {msg && <div className="banner">{msg}</div>}

      <div className="stats">
        <Stat label="Uptime" value={`${uptimeH}h ${uptimeM}m`} sub={`target ≥ 99% · status ${sys?.status ?? "—"}`} />
        <Stat label="CPU" value={`${sys?.cpu_pct ?? "—"}%`} />
        <Stat label="Memory" value={`${sys?.mem_pct ?? "—"}%`} sub={`${sys?.mem_used_gb ?? "—"} GB used`} />
        <Stat label="Disk free" value={`${sys?.disk_free_gb ?? "—"} GB`} />
      </div>

      <div className="grid2">
        <Card title="System metrics (auto-refresh 5s)">
          <div className="meter"><div className="meter-fill cpu" style={{ width: `${sys?.cpu_pct || 0}%` }} /></div>
          <div className="meter-label">CPU {sys?.cpu_pct ?? 0}%</div>
          <div className="meter"><div className="meter-fill mem" style={{ width: `${sys?.mem_pct || 0}%` }} /></div>
          <div className="meter-label">Memory {sys?.mem_pct ?? 0}%</div>
          <table className="tbl">
            <tbody>
              <tr><td>Application uptime</td><td>{uptimeH}h {uptimeM}m</td></tr>
              <tr><td>Disk free</td><td>{sys?.disk_free_gb ?? "—"} GB</td></tr>
              <tr><td>HDFS namenode</td><td className="muted">data/hdfs/namenode.json</td></tr>
              <tr><td>Job runtimes tracked</td><td>see Processing → history</td></tr>
            </tbody>
          </table>
        </Card>

        <Card title="Reliability — backups & fault tolerance">
          <div className="actions">
            <button className="btn primary" onClick={backup}>Run backup now (DB + NameNode metadata)</button>
          </div>
          {bkStatus && (
            <p className="muted dim">
              Automated backups: every {bkStatus.interval_hours} h · last: {bkStatus.last_automated || "startup pending"}
            </p>
          )}
          <table className="tbl">
            <thead><tr><th>Backup</th><th>Size</th></tr></thead>
            <tbody>
              {backups.map((b) => (
                <tr key={b.name}><td>{b.name}</td><td>{fmtSize(b.size)}</td></tr>
              ))}
              {backups.length === 0 && <tr><td colSpan={2} className="muted">No backups yet.</td></tr>}
            </tbody>
          </table>
          <p className="muted dim">
            HDFS stores every block twice (2x replication). The Climate Data page can corrupt a DataNode block to
            demonstrate fault-tolerant reads. Backups are scheduled automatically at startup + on demand.
          </p>
        </Card>
      </div>

      {lb && lb.nodes.length > 0 && (
        <Card wide title="Load balancing — reads/writes per DataNode (round-robin)">
          <table className="tbl">
            <thead><tr><th>Node</th><th>Reads served</th><th>Writes served</th></tr></thead>
            <tbody>
              {lb.nodes.map((n: any) => (
                <tr key={n.node}>
                  <td>{n.node}</td>
                  <td>{n.reads}</td>
                  <td>{n.writes}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="muted dim">Strategy: {lb.strategy}</p>
        </Card>
      )}
    </div>
  );
}

function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}