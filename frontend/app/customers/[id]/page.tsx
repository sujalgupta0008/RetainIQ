"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { inr, pct, num } from "@/lib/format";
import { Card, RiskBadge, PrioBadge, Loading, Err } from "@/components/ui";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

export default function CustomerDetail({ params }: { params: { id: string } }) {
  const [c, setC] = useState<any>(null);
  const [err, setErr] = useState("");
  const load = () => api(`/api/customers/${params.id}`).then(setC).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);
  if (err) return <Err msg={err} retry={load} />;
  if (!c) return <Loading msg="Loading customer 360…" />;
  const traj = ["d90", "d60", "d30", "today"].map((k) => ({ point: k === "today" ? "Today" : k.replace("d", "") + "d ago", risk: (c.trajectory?.[k] || 0) * 100 }));
  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between flex-wrap gap-2">
        <div>
          <h1 className="text-2xl font-bold">{c.name} <span className="text-sm font-normal text-slate-400">#{c.id}</span></h1>
          <p className="text-sm text-slate-500">{c.age}y · {c.region} · {c.segment} · tenure {c.tenure} mo · income {inr(c.income)}</p>
        </div>
        <div className="flex items-center gap-2"><RiskBadge band={c.band} /><PrioBadge p={c.priority} /></div>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          ["Churn probability", pct(c.proba)], ["CLV (est.)", inr(c.clv)],
          ["Revenue at risk (est.)", inr(c.rar)], ["Deterioration score", `${c.deterioration}/100`],
        ].map(([l, v]) => (
          <div key={l} className="bg-white rounded-xl border p-4"><div className="text-xs text-slate-500 uppercase">{l}</div>
            <div className="text-xl font-bold mt-1">{v}</div></div>
        ))}
      </div>
      <div className="grid md:grid-cols-2 gap-4">
        <Card title="Why is this customer at risk?" sub="Top drivers computed from real behavior vs tenant typical">
          <p className="text-sm bg-amber-50 border border-amber-200 rounded-lg p-3 mb-3">{c.explanation}</p>
          <div className="space-y-2">
            {c.drivers.map((d: any, i: number) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <span className={`w-2 h-2 rounded-full ${d.impact > 0 ? "bg-red-500" : "bg-emerald-500"}`} />
                <span className="font-medium w-44">{d.label}</span>
                <span className="text-slate-500 text-xs">value {num(d.value)} · typical {num(d.typical)}</span>
                <span className={`ml-auto text-xs font-semibold ${d.impact > 0 ? "text-red-600" : "text-emerald-600"}`}>
                  {d.impact > 0 ? "↑ risk" : "protective"}</span>
              </div>
            ))}
          </div>
          {c.det_flags?.length > 0 && <p className="text-xs text-slate-500 mt-3">Deterioration flags: {c.det_flags.join(", ")}</p>}
        </Card>
        <Card title="Risk trajectory" sub="Predicted churn probability over 90 days">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={traj}><CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="point" tick={{ fontSize: 12 }} /><YAxis tick={{ fontSize: 12 }} /><Tooltip />
              <Line type="monotone" dataKey="risk" stroke="#ef4444" strokeWidth={2} name="risk %" /></LineChart>
          </ResponsiveContainer>
        </Card>
      </div>
      <div className="grid md:grid-cols-2 gap-4">
        <Card title="Recommended next best action" sub="Max expected net = success × CLV − cost">
          {c.action && (
            <div>
              <div className="text-lg font-bold capitalize">{c.action.key.replaceAll("_", " ")}</div>
              <p className="text-sm text-slate-600 mt-1">{c.action.reason}</p>
              <div className="grid grid-cols-3 gap-2 mt-3 text-sm">
                <div className="bg-slate-50 rounded-lg p-2"><div className="text-xs text-slate-500">Cost</div><div className="font-bold">{inr(c.action.cost)}</div></div>
                <div className="bg-slate-50 rounded-lg p-2"><div className="text-xs text-slate-500">Success</div><div className="font-bold">{pct(c.action.success)}</div></div>
                <div className="bg-slate-50 rounded-lg p-2"><div className="text-xs text-slate-500">Exp. ROI</div><div className="font-bold">{(c.action.roi * 100).toFixed(0)}%</div></div>
              </div>
            </div>
          )}
        </Card>
        <Card title="Profile & activity" sub={`${c.product_count} products · balance ${inr(c.total_balance)}`}>
          <div className="text-sm space-y-1.5">
            <p><span className="text-slate-500">Products:</span> {c.products.join(", ") || "—"}</p>
            <p><span className="text-slate-500">Balances:</span> {c.balances.map((b: any) => `${b.type} ${inr(b.balance)}`).join(" · ")}</p>
            <p><span className="text-slate-500">Txn:</span> {c.txn_freq}/mo × {inr(c.avg_txn)} avg · logins {c.logins}/mo · complaints {c.complaints}</p>
            <p><span className="text-slate-500">Annual contribution (est.):</span> {inr(c.annual_contrib)}</p>
          </div>
          <div className="mt-3">
            <p className="text-xs font-medium text-slate-500 mb-1">RECENT TRANSACTIONS</p>
            <div className="space-y-1 max-h-36 overflow-y-auto text-xs">
              {c.transactions.map((t: any, i: number) => (
                <div key={i} className="flex justify-between border-b border-slate-50 py-1">
                  <span className="text-slate-500">{t.ts.slice(0, 10)} · {t.type}</span><span className="font-medium">{inr(t.amount)}</span>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
