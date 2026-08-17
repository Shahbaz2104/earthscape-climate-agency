export const API = (import.meta.env.VITE_API_URL as string | undefined) || "http://localhost:8000";
export const WS_URL = API.replace(/^http/, "ws");

export async function api(path: string, opts: { method?: string; body?: unknown } = {}) {
  const token = localStorage.getItem("token");
  const res = await fetch(`${API}${path}`, {
    method: opts.method || "GET",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function uploadFile(path: string, file: File) {
  const token = localStorage.getItem("token");
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: fd,
  });
  if (!res.ok) throw new Error((await res.json()).detail || "Upload failed");
  return res.json();
}

export function fmtSize(b: number) {
  if (b > 1e6) return `${(b / 1e6).toFixed(1)} MB`;
  if (b > 1e3) return `${(b / 1e3).toFixed(1)} KB`;
  return `${b} B`;
}

export function fmtNum(n: number) {
  return (n ?? 0).toLocaleString();
}

export function severityColor(s: string) {
  return s === "critical" ? "#ff5c5c" : s === "warning" ? "#ffb020" : "#4da3ff";
}