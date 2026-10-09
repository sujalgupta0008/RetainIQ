"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { num } from "@/lib/format";
import { Card, Loading, Err, Button, PageHeader } from "@/components/ui";
import { Reveal } from "@/components/motion";
import { Upload, FileDown, RefreshCw } from "lucide-react";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function postFile(path: string, file: File): Promise<any> {
  const form = new FormData();
  form.append("f", file);
  const tok = localStorage.getItem("retainiq_token");
  const res = await fetch(`${BASE}${path}`, { method: "POST", headers: { Authorization: `Bearer ${tok}` }, body: form });
  const body = await res.json();
  if (!res.ok) throw new Error(body.detail || "Request failed");
  return body;
}

export default function Data() {
  const [status, setStatus] = useState<any>(null);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [replace, setReplace] = useState(true);
  const load = () => {
    setErr("");
    api("/api/data/status").then(setStatus).catch((e) => setErr(e.message));
  };
  useEffect(() => { load(); }, []);

  async function onChoose(e: React.ChangeEvent<HTMLInputElement>) {
    const picked = e.target.files?.[0];
    if (!picked) return;
    setFile(picked); setPreview(null); setMsg("Analyzing file and detecting dataset type…");
    try {
      const data = await postFile("/api/data/preview", picked);
      setPreview(data);
      setMsg("");
    } catch (ex: any) { setMsg(ex.message); }
  }
  async function doImport() {
    if (!file) return;
    setBusy(true); setMsg("Importing and validating records…");
    try {
      const data = await postFile(`/api/data/upload?replace=${replace ? "true" : "false"}`, file);
      setMsg(`${num(data.added)} customers imported successfully (${data.dataset_type}). ` +
        (data.replaced ? `${num(data.replaced)} existing records removed. ` : "") +
        (data.rejected ? `${num(data.rejected)} rows rejected. ` : "") +
        (data.errors?.length ? `e.g. ${data.errors.slice(0, 2).join(" | ")} ` : "") +
        "Select Retrain so the model learns from the new churn labels.");
      setPreview(null); setFile(null); load();
    } catch (ex: any) { setMsg(ex.message); }
    finally { setBusy(false); }
  }
  async function clearWorkspace() {
    if (!confirm(`This will permanently delete all ${status?.customers ?? 0} customers in this workspace. Continue?`)) return;
    setMsg("Clearing workspace…");
    try { const resp = await api("/api/data/clear", { method: "DELETE" }); setMsg(`${num(resp.removed)} records removed. You can now upload a new CSV.`); load(); }
    catch (e: any) { setMsg(e.message); }
  }
  async function retrain() {
    setMsg("Retraining model… This may take a few seconds.");
    try { const resp = await api("/api/predictions/retrain", { method: "POST" }); setMsg(`Model retrained — ${resp.updated} predictions refreshed. Dashboard, Risk, ROI and Campaigns now reflect the latest data.`); }
    catch (e: any) { setMsg(e.message); }
  }
  if (err) return <Err msg={err} retry={load} />;
  if (!status) return <Loading />;
  return (
    <div className="space-y-4 max-w-2xl">
      <PageHeader eyebrow="Data Ingestion" title="Customer Data" desc={`${status.customers} customers · ${status.features} feature rows. Upload a CSV to add customers, or retrain the model after making changes.`} />
      <Reveal>
        <Card glow title="Upload customers (CSV)">
          <p className="text-xs leading-relaxed mb-3" style={{ color: "var(--text-2)" }}>Accepted: RetainIQ banking sample <b>or</b> IBM Telco Customer Churn CSV (CustomerID, Monthly Charges, Churn Value…). Duplicates are skipped and reported.</p>
          <label className="flex items-start gap-2 text-[13px] mb-3 cursor-pointer select-none" style={{ color: "var(--text-1)" }}>
            <input type="checkbox" checked={replace} onChange={(e) => setReplace(e.target.checked)} className="mt-1 accent-blue-600" />
            <span><b>Replace existing data (remove current records)</b><br /><span style={{ color: "var(--text-2)" }}>When enabled, all {num(status.customers)} existing customers will be removed and only the new import will be kept. When disabled, new records will be added to the existing data.</span></span>
          </label>
          <div className="flex gap-2 flex-wrap">
            <label className="inline-flex items-center gap-2 text-white text-sm font-semibold px-4 py-2 rounded-full cursor-pointer shadow-glow-sm hover:-translate-y-px transition-all" style={{ backgroundImage: "linear-gradient(135deg,#2563EB,#3B82F6)" }}>
              <Upload size={15} /> Choose CSV<input type="file" accept=".csv" className="hidden" onChange={onChoose} />
            </label>
            <a href={`${BASE}/api/data/sample`} download className="inline-flex items-center gap-2 text-sm font-semibold px-4 py-2 rounded-full glass transition-all hover:border-[rgba(37,99,235,0.45)]" style={{ color: "var(--text-1)" }}>
              <FileDown size={15} /> Download sample CSV
            </a>
            <Button variant="secondary" onClick={retrain}><RefreshCw size={15} /> Retrain model</Button>
            <Button variant="secondary" onClick={clearWorkspace}>Clear workspace</Button>
          </div>
          {msg && <p className="text-[13px] mt-3" style={{ color: "var(--text-2)" }}>{msg}</p>}
        </Card>
      </Reveal>
      {preview && (
        <Reveal>
          <Card title={`Dataset detected: ${preview.dataset_type === "telco" ? "IBM Telco Customer Churn" : preview.dataset_type}`}
            sub={`Rows detected: ${num(preview.rows_detected)} · importable: ${num(preview.rows_importable)} · rejected: ${num(preview.rows_rejected)} · churn labels: ${num(preview.churn_labels)}`}>
            {preview.telco_note && <p className="text-xs rounded-xl p-3 mb-3 border border-amber-500/25 bg-amber-500/10" style={{ color: "var(--text-1)" }}>{preview.telco_note}</p>}
            <div className="grid grid-cols-2 gap-2 mb-3 text-[13px]">
              {preview.mapping.slice(0, 8).map((row: any, i: number) => (
                <div key={i} className="glass rounded-xl px-3 py-2 flex items-center gap-2">
                  <span className="truncate" style={{ color: "var(--text-3)" }}>{row.from}</span>
                  <span style={{ color: "#2563EB" }}>→</span>
                  <b className="truncate" style={{ color: "var(--text-1)" }}>{row.to}</b>
                </div>
              ))}
            </div>
            {preview.issues?.length > 0 && <p className="text-xs mb-3" style={{ color: "var(--text-3)" }}>e.g. {preview.issues.slice(0, 2).join(" | ")}</p>}
            <p className="text-xs mb-3" style={{ color: "var(--text-2)" }}>{replace ? `Importing will remove ${num(status.customers)} existing customers — only the ${num(preview.rows_importable)} new records will remain.` : `New records will be added to your existing ${num(status.customers)} customers.`}</p>
            <Button loading={busy} onClick={doImport}>
              {busy ? "Importing…" : replace ? `Replace & Import (${num(preview.rows_importable)} rows)` : `Import & Normalize (${num(preview.rows_importable)} rows)`}
            </Button>
          </Card>
        </Reveal>
      )}
      <Reveal>
        <Card title="How uploads work" sub="Preview first, import second, retrain third">
          <ol className="text-[13px] space-y-1.5 list-decimal ml-4" style={{ color: "var(--text-2)" }}>
            <li>Choose a CSV — we detect banking vs telco automatically.</li>
            <li>Review the column mapping and rejected rows.</li>
            <li>Import, then press Retrain so predictions refresh everywhere.</li>
          </ol>
        </Card>
      </Reveal>
    </div>
  );
}
