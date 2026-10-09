"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { num } from "@/lib/format";
import { Card, Loading, Err, btnPrimary, btnGhost } from "@/components/ui";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function postFile(path: string, file: File): Promise<any> {
  const fd = new FormData();
  fd.append("f", file);
  const t = localStorage.getItem("retainiq_token");
  const res = await fetch(`${BASE}${path}`, { method: "POST", headers: { Authorization: `Bearer ${t}` }, body: fd });
  const d = await res.json();
  if (!res.ok) throw new Error(d.detail || "Request failed");
  return d;
}

export default function Data() {
  const [st, setSt] = useState<any>(null);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [pv, setPv] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const load = () => {
    setErr("");
    api("/api/data/status").then(setSt).catch((e) => setErr(e.message));
  };
  useEffect(() => { load(); }, []);

  async function onChoose(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f); setPv(null); setMsg("Detecting dataset…");
    try {
      const p = await postFile("/api/data/preview", f);
      setPv(p);
      setMsg("");
    } catch (ex: any) { setMsg(ex.message); }
  }
  async function doImport() {
    if (!file) return;
    setBusy(true); setMsg("Importing & normalizing…");
    try {
      const d = await postFile("/api/data/upload", file);
      setMsg(`${num(d.added)} customers imported successfully (${d.dataset_type}). ` +
        (d.rejected ? `${num(d.rejected)} rows rejected. ` : "") +
        (d.errors?.length ? `e.g. ${d.errors.slice(0, 2).join(" | ")} ` : "") +
        "Press Retrain so the model learns the new churn labels.");
      setPv(null); setFile(null); load();
    } catch (ex: any) { setMsg(ex.message); }
    finally { setBusy(false); }
  }
  async function retrain() {
    setMsg("Retraining model…");
    try { const r = await api("/api/predictions/retrain", { method: "POST" }); setMsg(`Retrained — ${r.updated} predictions refreshed. Dashboard, Risk, ROI and Campaigns now reflect the new data.`); }
    catch (e: any) { setMsg(e.message); }
  }
  if (err) return <Err msg={err} retry={load} />;
  if (!st) return <Loading />;
  return (
    <div className="space-y-4 max-w-2xl">
      <div><h1 className="text-2xl font-bold">Data</h1>
        <p className="text-sm text-slate-500">{st.customers} customers · {st.features} feature rows. Upload a CSV to add customers, or retrain after changes.</p></div>
      <Card title="Upload customers (CSV)">
        <p className="text-xs text-slate-500 mb-2">Accepted: RetainIQ banking sample <b>or</b> IBM Telco Customer Churn CSV (CustomerID, Monthly Charges, Churn Value…). Duplicates are skipped and reported.</p>
        <div className="flex gap-2 flex-wrap">
          <label className={btnPrimary + " cursor-pointer"}>Choose CSV<input type="file" accept=".csv" className="hidden" onChange={onChoose} /></label>
          <a href={`${BASE}/api/data/sample`} className={btnGhost} download>Download sample CSV</a>
          <button onClick={retrain} className={btnGhost}>Retrain model</button>
        </div>
        {msg && <p className="text-sm text-indigo-700 mt-2">{msg}</p>}
      </Card>
      {pv && (
        <Card title={`Dataset detected: ${pv.dataset_type === "telco" ? "IBM Telco Customer Churn" : pv.dataset_type}`}
          sub={`Rows detected: ${num(pv.rows_detected)} · importable: ${num(pv.rows_importable)} · rejected: ${num(pv.rows_rejected)} · churn labels: ${num(pv.churn_labels)}`}>
          {pv.telco_note && <p className="text-xs bg-amber-50 border border-amber-200 rounded-lg p-2.5 mb-3">{pv.telco_note}</p>}
          <table className="w-full text-sm mb-3">
            <thead><tr className="text-left text-xs text-slate-500 border-b">
              <th className="py-1">Original column</th><th>RetainIQ feature</th>
            </tr></thead>
            <tbody>
              {pv.mapping.slice(0, 8).map((m: any, i: number) => (
                <tr key={i} className="border-b border-slate-50">
                  <td className="py-1 text-slate-600">{m.from}</td>
                  <td className="py-1 font-medium">{m.to}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {pv.issues?.length > 0 && <p className="text-xs text-slate-500 mb-2">e.g. {pv.issues.slice(0, 2).join(" | ")}</p>}
          <button className={btnPrimary} disabled={busy} onClick={doImport}>
            {busy ? "Importing…" : `Import & Normalize (${num(pv.rows_importable)} rows)`}
          </button>
        </Card>
      )}
    </div>
  );
}
