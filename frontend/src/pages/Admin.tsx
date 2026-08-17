import { useEffect, useState } from "react";
import { api } from "../api";
import { Card } from "./Dashboard";

export default function Admin() {
  const [users, setUsers] = useState<any[]>([]);
  const [form, setForm] = useState({ username: "", password: "", role: "analyst" });
  const [msg, setMsg] = useState("");

  useEffect(() => { api("/auth/users").then(setUsers).catch(() => {}); }, []);
  const load = () => api("/auth/users").then(setUsers).catch(() => {});

  async function create(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api("/auth/users", { method: "POST", body: form });
      setForm({ username: "", password: "", role: "analyst" });
      setMsg(`Created user ${form.username}`);
      load();
    } catch (err) {
      setMsg((err as Error).message);
    }
  }

  async function changeRole(u: any, role: string) {
    await api(`/auth/users/${u.id}`, { method: "PATCH", body: { role } });
    load();
  }

  async function del(u: any) {
    await api(`/auth/users/${u.id}`, { method: "DELETE" });
    load();
  }

  return (
    <div className="page">
      <h1>Administration</h1>
      <p className="muted">User authentication & authorization — role-based access control (admin / analyst)</p>

      {msg && <div className="banner">{msg}</div>}

      <div className="grid2">
        <Card title="Create user">
          <form className="stack" onSubmit={create}>
            <label>Username
              <input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required />
            </label>
            <label>Password (min 6 chars)
              <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
            </label>
            <label>Role
              <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
                <option value="analyst">analyst</option>
                <option value="admin">admin</option>
              </select>
            </label>
            <button className="btn primary">Create</button>
          </form>
        </Card>

        <Card title={`Users (${users.length})`}>
          <table className="tbl">
            <thead><tr><th>Username</th><th>Role</th><th>Created</th><th></th></tr></thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.username}</td>
                  <td>
                    <select value={u.role} onChange={(e) => changeRole(u, e.target.value)}>
                      <option value="analyst">analyst</option>
                      <option value="admin">admin</option>
                    </select>
                  </td>
                  <td className="muted">{u.created_at}</td>
                  <td><button className="btn sm danger" onClick={() => del(u)}>delete</button></td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="muted dim">
            RBAC: analysts can run jobs, train models and view data; administrators additionally manage
            users, delete HDFS files and trigger backups.
          </p>
        </Card>
      </div>
    </div>
  );
}