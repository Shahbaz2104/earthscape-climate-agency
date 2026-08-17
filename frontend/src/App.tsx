import { useState } from "react";
import { Routes, Route, NavLink, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Data from "./pages/Data";
import Processing from "./pages/Processing";
import ML from "./pages/ML";
import Alerts from "./pages/Alerts";
import Monitoring from "./pages/Monitoring";
import Support from "./pages/Support";
import Admin from "./pages/Admin";

export default function App() {
  const [user, setUser] = useState<any>(() => {
    try { return JSON.parse(localStorage.getItem("user") || "null"); } catch { return null; }
  });

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
  };

  if (!user) return <Login onLogin={setUser} />;

  return (
    <div className="layout">
      <Sidebar role={user.role} user={user} onLogout={logout} />
      <main className="content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/data" element={<Data role={user.role} />} />
          <Route path="/processing" element={<Processing />} />
          <Route path="/ml" element={<ML />} />
          <Route path="/alerts" element={<Alerts role={user.role} />} />
          <Route path="/monitoring" element={<Monitoring />} />
          <Route path="/support" element={<Support role={user.role} />} />
          <Route path="/admin" element={user.role === "admin" ? <Admin /> : <Navigate to="/" />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
    </div>
  );
}

function Sidebar({ role, user, onLogout }: { role: string; user: any; onLogout: () => void }) {
  return (
    <aside className="sidebar">
      <div className="brand">🌍 <span>EarthScape</span></div>
      <div className="brand-sub">Climate Agency</div>
      <nav>
        <NavLink to="/" end>📊 Dashboard</NavLink>
        <NavLink to="/data">🗄️ Climate Data</NavLink>
        <NavLink to="/processing">⚙️ Processing</NavLink>
        <NavLink to="/ml">🧠 ML Lab</NavLink>
        <NavLink to="/alerts">🔔 Alerts</NavLink>
        <NavLink to="/monitoring">📈 Monitoring</NavLink>
        <NavLink to="/support">💬 Support</NavLink>
        {role === "admin" && <NavLink to="/admin">🛡️ Admin</NavLink>}
      </nav>
      <div className="sidebar-foot">
        <div className="user-chip">
          <div className="avatar">{user.username[0].toUpperCase()}</div>
          <div>
            <div className="uname">{user.username}</div>
            <div className="urole">{role}</div>
          </div>
        </div>
        <button className="btn sm" onClick={onLogout}>Sign out</button>
      </div>
    </aside>
  );
}