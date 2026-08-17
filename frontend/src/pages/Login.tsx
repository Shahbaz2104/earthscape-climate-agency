import { useState } from "react";
import { api } from "../api";

export default function Login({ onLogin }: { onLogin: (u: { username: string; role: string }) => void }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const r = await api("/auth/login", { method: "POST", body: { username, password } });
      localStorage.setItem("token", r.token);
      localStorage.setItem("user", JSON.stringify(r.user));
      onLogin(r.user);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div className="login-wrap">
      <form className="login-card" onSubmit={submit}>
        <div className="login-logo">🌍</div>
        <h1>EarthScape Climate Agency</h1>
        <p className="muted">Sign in to the climate analytics platform</p>
        <label>Username
          <input value={username} onChange={(e) => setUsername(e.target.value)} />
        </label>
        <label>Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
        {error && <div className="error">{error}</div>}
        <button type="submit" className="btn primary">Sign in</button>
        <p className="hint muted">Demo accounts: admin/admin123 · analyst/analyst123</p>
      </form>
    </div>
  );
}