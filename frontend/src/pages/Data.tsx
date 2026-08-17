import { useEffect, useState } from "react";
import { api, fmtSize, uploadFile } from "../api";
import { Card } from "./Dashboard";

export default function Data({ role }: { role: string }) {
  const [files, setFiles] = useState<any[]>([]);
  const [info, setInfo] = useState<any>(null);
  const [selected, setSelected] = useState<any>(null);
  const [msg, setMsg] = useState("");

  const load = () => {
    api("/hdfs/files").then(setFiles).catch(() => {});
    api("/hdfs/info").then(setInfo).catch(() => {});
  };
  useEffect(load, []);

  async function generate() {
    setMsg("Generating synthetic datasets…");
    const r = await api("/ingest/generate", { method: "POST" });
    setMsg(`Generated ${Object.keys(r.generated).length} datasets with ${Object.values(r.generated).reduce((a: any, b: any) => a + b, 0)} rows → HDFS /raw/`);
    load();
  }

  async function onUpload(f: File | undefined) {
    if (!f) return;
    const r = await uploadFile("/ingest/upload", f);
    setMsg(`Uploaded ${r.file}: ${r.rows} rows, ${r.columns.length} columns → ${r.hdfs_path}`);
    load();
  }

  async function del(path: string) {
    await api(`/hdfs/files/${path}`, { method: "DELETE" });
    load();
  }

  async function corrupt(path: string) {
    const r = await api(`/hdfs/files/${path}/corrupt`, { method: "POST" });
    setMsg(`Corrupted a block of ${path}. Remaining replicas: ${r.remaining_replicas.join(", ")} — data still readable.`);
    load();
  }

  return (
    <div className="page">
      <h1>Climate Data — HDFS</h1>
      <p className="muted">Scalable, replicated storage for climate datasets (Hadoop Distributed File System emulation)</p>

      {msg && <div className="banner">{msg}</div>}

      <div className="stats">
        <Stat label="Files" value={`${info?.files ?? "—"}`} />
        <Stat label="Total size" value={fmtSize(info?.size_bytes || 0)} />
        <Stat label="Blocks" value={`${info?.blocks ?? "—"}`} />
        <Stat label="Replication" value={`${info?.replication ?? "—"}x`} />
      </div>

      <div className="actions">
        <button className="btn primary" onClick={generate}>Generate demo datasets</button>
        <label className="btn">Upload CSV/JSON
          <input type="file" accept=".csv,.json" hidden onChange={(e) => onUpload(e.target.files?.[0])} />
        </label>
      </div>

      <Card title="Files in HDFS">
        <table className="tbl">
          <thead>
            <tr><th>Path</th><th>Size</th><th>Blocks</th><th>Replication</th><th>Created</th><th></th></tr>
          </thead>
          <tbody>
            {files.map((f) => (
              <tr key={f.path}>
                <td>
                  <a href="#" onClick={(e) => { e.preventDefault(); setSelected(f); }}>{f.path}</a>
                </td>
                <td>{fmtSize(f.size)}</td>
                <td>{f.blocks}</td>
                <td>{f.replication}x</td>
                <td className="muted">{f.created}</td>
                <td className="row-actions">
                  {role === "admin" && (
                    <>
                      <button className="btn sm" title="Simulate DataNode failure (fault-tolerance demo)" onClick={() => corrupt(f.path.slice(1))}>corrupt</button>
                      <button className="btn sm danger" onClick={() => del(f.path.slice(1))}>delete</button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      {selected && (
        <Card title={`Preview: ${selected.path}`}>
          <pre className="preview">{selected.preview}</pre>
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