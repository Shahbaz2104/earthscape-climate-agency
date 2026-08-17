import { useEffect, useState } from "react";
import { api } from "../api";
import { Card, severityColor } from "./Dashboard";

export default function Alerts({ role }: { role: string }) {
  const [rules, setRules] = useState<any[]>([]);
  const [notifs, setNotifs] = useState<any[]>([]);
  const [form, setForm] = useState({ metric: "temp_c", operator: "gt", threshold: 35, severity: "warning", description: "" });

  const load = () => {
    api("/alerts/rules").then(setRules).catch(() => {});
    api("/alerts/notifications").then(setNotifs).catch(() => {});
  };
  useEffect(load, []);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    await api("/alerts/rules", { method: "POST", body: form });
    setForm({ ...form, description: "" });
    load();
  }

  async function toggle(r: any) {
    await api(`/alerts/rules/${r.id}`, { method: "PATCH", body: { enabled: r.enabled ? 0 : 1 } });
    load();
  }

  async function markRead() {
    await api("/alerts/notifications/read", { method: "POST" });
    load();
  }

  return (
    <div className="page">
      <h1>Alerts & Notifications</h1>
      <p className="muted">Threshold rules evaluated against every real-time sensor reading; fires automatically</p>

      <div className="grid2">
        <Card title="Alert rules">
          <table className="tbl">
            <thead><tr><th>Metric</th><th>Op</th><th>Threshold</th><th>Severity</th><th>Enabled</th><th>Description</th></tr></thead>
            <tbody>
              {rules.map((r) => (
                <tr key={r.id}>
                  <td>{r.metric}</td>
                  <td>{r.operator}</td>
                  <td>{r.threshold}</td>
                  <td><span className="pill" style={{ color: severityColor(r.severity) }}>{r.severity}</span></td>
                  <td>
                    <button className={`btn sm ${r.enabled ? "" : "danger"}`} onClick={() => toggle(r)}>
                      {r.enabled ? "on" : "off"}
                    </button>
                  </td>
                  <td className="muted">{r.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {role === "admin" && (
            <form className="inline-form" onSubmit={add}>
              <select value={form.metric} onChange={(e) => setForm({ ...form, metric: e.target.value })}>
                <option value="temp_c">temp_c</option>
                <option value="co2_ppm">co2_ppm</option>
                <option value="humidity">humidity</option>
              </select>
              <select value={form.operator} onChange={(e) => setForm({ ...form, operator: e.target.value })}>
                <option value="gt">&gt;</option><option value="gte">≥</option>
                <option value="lt">&lt;</option><option value="lte">≤</option>
              </select>
              <input type="number" step="0.1" value={form.threshold} onChange={(e) => setForm({ ...form, threshold: +e.target.value })} />
              <select value={form.severity} onChange={(e) => setForm({ ...form, severity: e.target.value })}>
                <option>info</option><option>warning</option><option>critical</option>
              </select>
              <input placeholder="description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
              <button className="btn primary sm">Add rule</button>
            </form>
          )}
        </Card>

        <Card title="Notification inbox">
          <button className="btn sm" onClick={markRead}>Mark all read</button>
          {notifs.slice(0, 20).map((n) => (
            <div key={n.id} className={`alert-line ${n.read ? "dim" : ""}`} style={{ borderLeftColor: severityColor(n.severity) }}>
              <b>{n.title}</b>
              <div>{n.body}</div>
              <div className="muted dim">{n.created_at}</div>
            </div>
          ))}
          {notifs.length === 0 && <p className="muted">No notifications yet — they appear in real time as rules fire.</p>}
        </Card>
      </div>
    </div>
  );
}