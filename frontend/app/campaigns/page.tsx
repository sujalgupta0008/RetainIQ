"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { inr } from "@/lib/format";
import { Card, Loading, Err, Field, Input, Select, Button, PageHeader, Badge, Table, THead, TH, TD, TRow, EmptyState } from "@/components/ui";
import { Reveal } from "@/components/motion";
import { Megaphone } from "lucide-react";

const ACTS = ["fee_waiver", "cashback", "personalized_offer", "loan_offer", "premium_upgrade", "rm_call", "service_recovery"];

export default function Campaigns() {
  const [list, setList] = useState<any[]>([]);
  const [err, setErr] = useState("");
  const [form, setForm] = useState({ name: "Q4 Priority Save", intervention: "rm_call", min_proba: 0.5, min_clv: 50000, offer_cost: 1000, expected_success: 0.3, duration_days: 30 });
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);
  const load = () => api("/api/campaigns").then(setList).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);
  async function create() {
    setMsg("Creating…"); setBusy(true);
    try {
      const resp = await api("/api/campaigns", { method: "POST", body: JSON.stringify(form) });
      setMsg(`Projected: ${resp.audience} customers, ${inr(resp.projected.revenue)} revenue, ${resp.projected.roi_pct}% ROI (est.)`);
      load();
    } catch (e: any) { setMsg(e.message); }
    finally { setBusy(false); }
  }
  if (err) return <Err msg={err} retry={load} />;
  if (!list) return <Loading />;
  return (
    <div className="space-y-4">
      <PageHeader eyebrow="Studio" title="CAMPAIGNS" desc="Define audience → see projected ROI → launch with control/treatment split." />
      <div className="grid md:grid-cols-[340px_1fr] gap-4 items-start">
        <Reveal>
          <Card glow title="New campaign">
            <div className="space-y-2.5">
              <Field label="Name"><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></Field>
              <div className="grid grid-cols-2 gap-2.5">
                <Field label="Intervention">
                  <Select value={form.intervention} onChange={(e) => setForm({ ...form, intervention: e.target.value })}>
                    {ACTS.map((action) => <option key={action} value={action}>{action.replaceAll("_", " ")}</option>)}
                  </Select>
                </Field>
                <Field label="Min churn prob"><Input type="number" step={0.05} min={0} max={1} value={form.min_proba} onChange={(e) => setForm({ ...form, min_proba: Number(e.target.value) })} /></Field>
                <Field label="Min CLV (₹)"><Input type="number" value={form.min_clv} onChange={(e) => setForm({ ...form, min_clv: Number(e.target.value) })} /></Field>
                <Field label="Offer cost (₹)"><Input type="number" value={form.offer_cost} onChange={(e) => setForm({ ...form, offer_cost: Number(e.target.value) })} /></Field>
                <Field label="Expected success"><Input type="number" step={0.01} value={form.expected_success} onChange={(e) => setForm({ ...form, expected_success: Number(e.target.value) })} /></Field>
                <Field label="Duration (days)"><Input type="number" value={form.duration_days} onChange={(e) => setForm({ ...form, duration_days: Number(e.target.value) })} /></Field>
              </div>
              <Button className="w-full" loading={busy} onClick={create}>Create & project ROI</Button>
              {msg && <p className="text-xs" style={{ color: "var(--text-2)" }}>{msg}</p>}
            </div>
          </Card>
        </Reveal>
        <Reveal delay={0.05}>
          <Card title="All campaigns">
            {list.length === 0 ? (
              <EmptyState icon={<Megaphone size={20} />} title="No campaigns yet" hint="Create your first audience on the left." />
            ) : (
              <Table>
                <THead><TH>Name</TH><TH>Intervention</TH><TH>Status</TH><TH right>Targets</TH><TH /></THead>
                <tbody>
                  {list.map((camp: any) => (
                    <TRow key={camp.id}>
                      <TD><span className="font-semibold">{camp.name}</span></TD>
                      <TD><span className="capitalize" style={{ color: "var(--text-2)" }}>{camp.intervention.replaceAll("_", " ")}</span></TD>
                      <TD><Badge tone={camp.status === "completed" ? "success" : "neutral"}>{camp.status}</Badge></TD>
                      <TD right>{camp.targets}</TD>
                      <TD right><Link href={`/campaigns/${camp.id}`} className="text-xs font-bold hover:underline" style={{ color: "#EC2F8B" }}>Open →</Link></TD>
                    </TRow>
                  ))}
                </tbody>
              </Table>
            )}
          </Card>
        </Reveal>
      </div>
    </div>
  );
}
