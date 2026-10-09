"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { inr } from "@/lib/format";
import { Card, Loading, Err, Field, inputCls, btnPrimary } from "@/components/ui";

const ACTS = ["fee_waiver", "cashback", "personalized_offer", "loan_offer", "premium_upgrade", "rm_call", "service_recovery"];

export default function Campaigns() {
  const [list, setList] = useState<any[]>([]);
  const [err, setErr] = useState("");
  const [form, setForm] = useState({ name: "Q4 Priority Save", intervention: "rm_call", min_proba: 0.5, min_clv: 50000, offer_cost: 1000, expected_success: 0.3, duration_days: 30 });
  const [msg, setMsg] = useState("");
  const load = () => api("/api/campaigns").then(setList).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);
  async function create() {
    setMsg("Creating…");
    try {
      const r = await api("/api/campaigns", { method: "POST", body: JSON.stringify(form) });
      setMsg(`Projected: ${r.audience} customers, ${inr(r.projected.revenue)} revenue, ${r.projected.roi_pct}% ROI (est.)`);
      load();
    } catch (e: any) { setMsg(e.message); }
  }
  if (err) return <Err msg={err} retry={load} />;
  if (!list) return <Loading />;
  return (
    <div className="space-y-4">
      <div><h1 className="text-2xl font-bold">Campaign Studio</h1>
        <p className="text-sm text-slate-500">Define audience → see projected ROI → launch with control/treatment split.</p></div>
      <div className="grid md:grid-cols-[340px_1fr] gap-4">
        <Card title="New campaign">
          <div className="space-y-2">
            <Field label="Name"><input className={inputCls} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></Field>
            <div className="grid grid-cols-2 gap-2">
              <Field label="Intervention">
                <select className={inputCls} value={form.intervention} onChange={(e) => setForm({ ...form, intervention: e.target.value })}>
                  {ACTS.map((a) => <option key={a} value={a}>{a.replaceAll("_", " ")}</option>)}
                </select>
              </Field>
              <Field label="Min churn prob"><input type="number" step={0.05} min={0} max={1} className={inputCls} value={form.min_proba} onChange={(e) => setForm({ ...form, min_proba: Number(e.target.value) })} /></Field>
              <Field label="Min CLV (₹)"><input type="number" className={inputCls} value={form.min_clv} onChange={(e) => setForm({ ...form, min_clv: Number(e.target.value) })} /></Field>
              <Field label="Offer cost (₹)"><input type="number" className={inputCls} value={form.offer_cost} onChange={(e) => setForm({ ...form, offer_cost: Number(e.target.value) })} /></Field>
              <Field label="Expected success"><input type="number" step={0.01} className={inputCls} value={form.expected_success} onChange={(e) => setForm({ ...form, expected_success: Number(e.target.value) })} /></Field>
              <Field label="Duration (days)"><input type="number" className={inputCls} value={form.duration_days} onChange={(e) => setForm({ ...form, duration_days: Number(e.target.value) })} /></Field>
            </div>
            <button className={btnPrimary + " w-full"} onClick={create}>Create & project ROI</button>
            {msg && <p className="text-xs text-indigo-700">{msg}</p>}
          </div>
        </Card>
        <Card title="All campaigns">
          <table className="w-full text-sm">
            <thead><tr className="text-left text-xs text-slate-500 border-b">
              <th className="py-2">Name</th><th>Intervention</th><th>Status</th><th className="text-right">Targets</th><th></th>
            </tr></thead>
            <tbody>
              {list.map((c: any) => (
                <tr key={c.id} className="border-b border-slate-50">
                  <td className="py-2 font-medium">{c.name}</td>
                  <td className="text-slate-500 capitalize">{c.intervention.replaceAll("_", " ")}</td>
                  <td><span className={`text-xs px-2 py-0.5 rounded-full ${c.status === "completed" ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>{c.status}</span></td>
                  <td className="text-right">{c.targets}</td>
                  <td className="text-right"><Link href={`/campaigns/${c.id}`} className="text-indigo-600 hover:underline text-xs font-medium">Open →</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
    </div>
  );
}
