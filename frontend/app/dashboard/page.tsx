"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { inr, num } from "@/lib/format";
import { Card, MetricCard, Loading, Err } from "@/components/ui";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, CartesianGrid } from "recharts";

const COLORS = ["#ef4444", "#f59e0b", "#10b981", "#6366f1", "#8b5cf6", "#ec4899"];

export default function Dashboard() {
  const [d, setD] = useState<any>(null);
  const [err, setErr] = useState("");
  const load = () => {
    setErr("");
    Promise.all([
      api("/api/dashboard/summary"), api("/api/dashboard/risk-dist"),
      api("/api/dashboard/revenue-by-segment"), api("/api/dashboard/product-risk"),
      api("/api/dashboard/risk-trend"), api("/api/dashboard/quadrant"),
      api("/api/dashboard/campaign-perf"),
    ]).then(([s, rd, rs, pr, rt, q, cp]) => setD({ s, rd, rs, pr, rt, q, cp })).catch((e) => setErr(e.message));
  };
  useEffect(load, []);
  if (err) return <Err msg={err} retry={load} />;
  if (!d) return <Loading msg="Loading command center…" />;
  const { s } = d;
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Executive Command Center</h1>
        <p className="text-sm text-slate-500">Who to save, what to do, what it costs, and expected return. All figures computed live from the database; predictions are estimates.</p>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard label="Total customers" value={num(s.total)} />
        <MetricCard label="High risk" value={num(s.high)} tone="red" hint={`${num(s.medium)} medium`} />
        <MetricCard label="Revenue at risk (est.)" value={inr(s.revenue_at_risk)} tone="red" hint="Σ churn prob × CLV" />
        <MetricCard label="Expected protected" value={inr(s.expected_protected)} tone="green" hint="realized from campaigns" />
        <MetricCard label="Retention budget" value={inr(s.retention_budget)} hint="planning envelope" />
        <MetricCard label="Campaign cost" value={inr(s.campaign_cost)} hint="realized spend" />
        <MetricCard label="Expected ROI" value={`${s.expected_roi_pct}%`} tone={s.expected_roi_pct >= 0 ? "green" : "red"} hint="net / cost" />
        <MetricCard label="Targeted / retained" value={`${num(s.customers_targeted)} / ${num(s.expected_retained)}`} hint={`${num(s.campaigns)} campaigns`} />
      </div>
      <div className="grid md:grid-cols-3 gap-4">
        <Card title="Churn risk distribution" sub="Low <35% · Medium 35–60% · High ≥60%">
          <ResponsiveContainer width="100%" height={220}>
            <PieChart><Pie data={d.rd} dataKey="count" nameKey="band" outerRadius={80} label>
              {d.rd.map((_: any, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Pie><Tooltip /></PieChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Revenue at risk by segment (est.)">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={d.rs} layout="vertical">
              <XAxis type="number" hide /><YAxis type="category" dataKey="segment" width={80} tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v: any) => inr(Number(v))} /><Bar dataKey="rar" fill="#6366f1" radius={4} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Risk trend" sub="Average predicted risk over time">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={d.rt.map((x: any) => ({ ...x, label: x.point }))}>
              <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="label" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} /><Tooltip /><Line type="monotone" dataKey="avg_risk" stroke="#ef4444" strokeWidth={2} dot={false} name="avg risk %" />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>
      <div className="grid md:grid-cols-2 gap-4">
        <Card title="Product-wise risk" sub="Where is revenue at risk concentrated?">
          <div className="space-y-2">
            {d.pr.map((p: any) => (
              <div key={p.product} className="flex items-center gap-3 text-sm">
                <div className="w-44 truncate font-medium">{p.product}</div>
                <div className="flex-1 bg-slate-100 rounded-full h-2.5">
                  <div className="bg-indigo-500 h-2.5 rounded-full" style={{ width: `${Math.min(100, (p.rar / Math.max(1, d.pr[0].rar)) * 100)}%` }} />
                </div>
                <div className="w-28 text-right text-slate-600">{inr(p.rar)}</div>
                <div className="w-20 text-right text-red-600 text-xs">{p.high_risk} high-risk</div>
              </div>
            ))}
          </div>
        </Card>
        <Card title="Value × Risk quadrants" sub={`Split at median CLV ${inr(d.q.median_clv)}`}>
          <div className="grid grid-cols-2 gap-3 text-center">
            {[["High value · High risk", d.q.hv_hr, "bg-red-50 border-red-200 text-red-700"],
              ["High value · Low risk", d.q.hv_lr, "bg-emerald-50 border-emerald-200 text-emerald-700"],
              ["Low value · High risk", d.q.lv_hr, "bg-amber-50 border-amber-200 text-amber-700"],
              ["Low value · Low risk", d.q.lv_lr, "bg-slate-50 border-slate-200 text-slate-600"]].map(([l, v, c]) => (
              <div key={l as string} className={`border rounded-xl p-4 ${c}`}>
                <div className="text-2xl font-bold">{v as number}</div>
                <div className="text-xs font-medium mt-1">{l as string}</div>
              </div>
            ))}
          </div>
        </Card>
      </div>
      <Card title="Campaign performance" sub="Realized results from A/B experiments">
        <table className="w-full text-sm">
          <thead><tr className="text-left text-slate-500 text-xs">
            <th className="py-2">Campaign</th><th>Status</th><th className="text-right">Revenue</th><th className="text-right">Lift</th><th className="text-right">ROI</th>
          </tr></thead>
          <tbody>
            {d.cp.map((c: any) => (
              <tr key={c.id} className="border-t border-slate-100">
                <td className="py-2 font-medium">{c.name}</td><td className="text-slate-500">{c.status}</td>
                <td className="text-right">{inr(c.revenue)}</td><td className="text-right">{(c.lift * 100).toFixed(1)}%</td>
                <td className="text-right font-semibold">{c.roi_pct == null ? "—" : `${c.roi_pct}%`}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
