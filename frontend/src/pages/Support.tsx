import { useEffect, useState } from "react";
import { api } from "../api";
import { Card } from "./Dashboard";

export default function Support({ role }: { role: string }) {
  const [tickets, setTickets] = useState<any[]>([]);
  const [form, setForm] = useState({ subject: "", body: "" });
  const [msg, setMsg] = useState("");

  useEffect(() => { api("/support/tickets").then(setTickets).catch(() => {}); }, []);
  const load = () => api("/support/tickets").then(setTickets).catch(() => {});

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    await api("/support/tickets", { method: "POST", body: form });
    setForm({ subject: "", body: "" });
    setMsg("Ticket submitted — support will respond.");
    load();
  }

  async function update(t: any, status: string) {
    await api(`/support/tickets/${t.id}`, { method: "PATCH", body: { status } });
    load();
  }

  return (
    <div className="page">
      <h1>Support & Feedback</h1>
      <p className="muted">Report issues, request assistance, and give feedback</p>

      {msg && <div className="banner">{msg}</div>}

      <div className="grid2">
        <Card title="Submit a ticket">
          <form className="stack" onSubmit={submit}>
            <label>Subject
              <input value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} required />
            </label>
            <label>Message
              <textarea rows={5} value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })} required />
            </label>
            <button className="btn primary">Submit</button>
          </form>
        </Card>

        <Card title={`Tickets (${tickets.length})`}>
          {tickets.map((t) => (
            <div key={t.id} className="ticket">
              <div className="ticket-head">
                <b>{t.subject}</b>
                <span className={`pill ${t.status}`}>{t.status}</span>
              </div>
              <div className="muted">{t.body}</div>
              {role === "admin" && (
                <div className="row-actions">
                  {t.username && <span className="muted dim">by {t.username} · {t.created_at}</span>}
                  <button className="btn sm" onClick={() => update(t, "in_progress")}>in progress</button>
                  <button className="btn sm" onClick={() => update(t, "resolved")}>resolve</button>
                </div>
              )}
            </div>
          ))}
          {tickets.length === 0 && <p className="muted">No tickets yet.</p>}
        </Card>
      </div>
    </div>
  );
}