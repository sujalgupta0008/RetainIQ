"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { inr, num, pct } from "@/lib/format";
import { Card, MetricCard, Loading, Field, inputCls, btnPrimary } from "@/components/ui";
import { useRouter } from "next/navigation";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

export default function ROI() {
  const router = useRouter();
  const [f, setF] = useState({ min_proba: 0.5, min_clv: 50000, intervention_cost: 1000, success_rate: 0.28, reach: 1.0 });
  const [r, setR] = useState<any>(null);
  const set = (k: string, v: number) => setF({ ...f, [k]: v });
  useEffect(() => {
    const t = setTimeout(() => {
      api("/api/roi/simulate", { method: "POST", body: JSON.stringify(f) }).then(setR).catch(() => {});
    }, 300);
    return () => clearTimeout(t);
  }, [JSON.stringify(f)]);
  if (!r) return <Loading msg="Loading simulator…" />;
  const sc = [
    { name: "Conservative", ...r.scenarios.conservative },
    { name: "Expected", ...r.scenarios.expected },
    { name: "Optimistic", ...r.scenarios.optimistic },
  ];
  return (
    <div className="space-y-4">
      <div><h1 className="text-2xl font-bold">Retention ROI Simulator <span className="text-xs font-normal bg-indigo-100 text-indigo-700 px-2 py-1 rounded-full ml-2">HERO FEATURE</span></h1>
        <p className="text-sm text-slate-500">Who should we save, what should we spend, will it be profitable? All outputs are <b>estimates</b>.</p></div>
      <div className="grid md:grid-cols-[320px_1fr] gap-4">
        <Card title="Inputs" sub="Charts update live">
          <div className="space-y-4">
            <Field label={`Churn threshold: ${(f.min_proba * 100).toFixed(0)}%`}>
              <input type="range" min={0.2} max={0.8} step={0.05} value={f.min_proba} onChange={(e) => set("min_proba", Number(e.target.value))} className="w-full" />
            </Field>
            <Field label={`Min CLV: ${inr(f.min_clv)}`}>
              <input type="range" min={0} max={300000} step={10000} value={f.min_clv} onChange={(e) => set("min_clv", Number(e.target.value))} className="w-full" />
            </Field>
            <Field label={`Intervention cost: ${inr(f.intervention_cost)} / customer`}>
              <input type="range" min={0} max={3000} step={100} value={f.intervention_cost} onChange={(e) => set("intervention_cost", Number(e.target.value))} className="w-full" />
            </Field>
            <Field label={`Expected success rate: ${(f.success_rate * 100).toFixed(0)}%`}>
              <input type="range" min={0.05} max={0.6} step={0.01} value={f.success_rate} onChange={(e) => set("success_rate", Number(e.target.value))} className="w-full accent-indigo-600" />
            </Field>
            <Field label={`Campaign reach: ${(f.reach * 100).toFixed(0)}%`}>
              <input type="range" min={0.2} max={1} step={0.05} value={f.reach} onChange={(e) => set("reach", Number(e.target.value))} className="w-full" />
            </Field>
            <p className="text-xs text-slate-500">Audience: <b>{num(r.audience)}</b> customers · avg CLV {inr(r.avg_clv)} · break-even success {pct(r.break_even_rate)}</p>
          </div>
        </Card>
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <MetricCard label="Customers targeted (est.)" value={num(r.targeted)} />
            <MetricCard label="Expected retained (est.)" value={num(Math.round(r.retained))} tone="green" />
            <MetricCard label="Campaign cost (est.)" value={inr(r.cost)} />
            <MetricCard label="Revenue protected (est.)" value={inr(r.revenue)} tone="green" />
            <MetricCard label="Net value (est.)" value={inr(r.net)} tone={r.net >= 0 ? "green" : "red"} />
            <MetricCard label="ROI (est.)" value={`${r.roi_pct}%`} tone={r.roi_pct >= 0 ? "green" : "red"} hint={`retained = targeted × success · revenue = retained × avg CLV`} />
          </div>
          <Card title="Sensitivity analysis" sub="Same audience, scaled success assumptions">
            <ResponsiveContainer width="100%" height={230}>
              <BarChart data={sc.map((s: any) => ({ name: s.name, roi: s.roi_pct, net: s.net }))}>
                <XAxis dataKey="name" /><YAxis /><Tooltip />
                <Bar dataKey="roi" name="ROI %" radius={6}>
                  {sc.map((_: any, i: number) => <Cell key={i} fill={["#f59e0b", "#6366f1", "#10b981"][i]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="grid grid-cols-3 gap-2 mt-2 text-sm">
              {sc.map((s: any) => (
                <div key={s.name} className="bg-slate-50 rounded-lg p-3">
                  <div className="font-semibold">{s.name}</div>
                  <div className="text-xs text-slate-500">success {pct(s.success)} · retained {num(Math.round(s.retained))}</div>
                  <div className="font-bold">{inr(s.net)} net · {s.roi_pct}% ROI</div>
                </div>
              ))}
            </div>
          </Card>
          <button className={btnPrimary} onClick={() => router.push("/campaigns")}>Create campaign from this audience →</button>
        </div>
      </div>
    </div>
  );
}
