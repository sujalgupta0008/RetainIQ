"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { inr, pct, num } from "@/lib/format";
import { Card, RiskBadge, PrioBadge, Loading, Err, PageHeader, StatCard, Avatar } from "@/components/ui";
import { ChartTooltip, chartColors, ChartGradients } from "@/components/ui";
import { Reveal, Stagger, StaggerItem } from "@/components/motion";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Area } from "recharts";

export default function CustomerDetail({ params }: { params: { id: string } }) {
  const [cust, setCust] = useState<any>(null);
  const [err, setErr] = useState("");
  const load = () => api(`/api/customers/${params.id}`).then(setCust).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);
  if (err) return <Err msg={err} retry={load} />;
  if (!cust) return <Loading msg="Loading customer 360…" />;
  const traj = ["d90", "d60", "d30", "today"].map((point) => ({ point: point === "today" ? "Today" : point.replace("d", "") + "d ago", risk: (cust.trajectory?.[point] || 0) * 100 }));
  return (
    <div className="space-y-4">
      <PageHeader
        eyebrow={`Customer #${cust.id} · ${cust.segment}`}
        title={String(cust.name).toUpperCase()}
        desc={`${cust.age}y · ${cust.region} · tenure ${cust.tenure} mo · income ${inr(cust.income)}`}
        actions={<><RiskBadge band={cust.band} /><PrioBadge p={cust.priority} /></>}
      />
      <ChartGradients />
      <Reveal>
        <div className="flex items-center gap-3 glass rounded-2xl p-4">
          <Avatar name={cust.name} size={52} risk={cust.band} />
          <div className="min-w-0">
            <div className="font-extrabold text-lg tracking-tight" style={{ color: "var(--text-1)" }}>{cust.name}</div>
            <div className="text-xs tnum" style={{ color: "var(--text-2)" }}>{pct(cust.proba)} churn · {inr(cust.rar)} at risk · score {cust.deterioration}/100</div>
          </div>
        </div>
      </Reveal>
      <Stagger className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          ["Churn probability", cust.proba, (n: number) => pct(n)],
          ["CLV (est.)", cust.clv, (n: number) => inr(n)],
          ["Revenue at risk (est.)", cust.rar, (n: number) => inr(n)],
          ["Deterioration", cust.deterioration, (n: number) => `${Math.round(n)}/100`],
        ].map(([label, v, fmt]: any) => (
          <StaggerItem key={label}><StatCard label={label} value={v} format={fmt} /></StaggerItem>
        ))}
      </Stagger>
      <div className="grid md:grid-cols-2 gap-4 items-start">
        <Reveal>
          <Card title="Why is this customer at risk?" sub="Top drivers computed from real behavior vs tenant typical">
            <p className="text-[13px] rounded-xl p-3 mb-3 border border-amber-500/25 bg-amber-500/10 leading-relaxed" style={{ color: "var(--text-1)" }}>{cust.explanation}</p>
            <div className="space-y-2">
              {cust.drivers.map((driver: any, i: number) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  <span className="w-2 h-2 rounded-full shrink-0" style={{ background: driver.impact > 0 ? "#FF4D6D" : "#34D399", boxShadow: `0 0 8px ${driver.impact > 0 ? "#FF4D6D" : "#34D399"}` }} />
                  <span className="font-semibold w-44 truncate" style={{ color: "var(--text-1)" }}>{driver.label}</span>
                  <span className="text-xs tnum truncate" style={{ color: "var(--text-3)" }}>value {num(driver.value)} · typical {num(driver.typical)}</span>
                  <span className={`ml-auto text-[11px] font-bold shrink-0 ${driver.impact > 0 ? "text-risk-high" : "text-semantic-success"}`}>
                    {driver.impact > 0 ? "↑ risk" : "protective"}</span>
                </div>
              ))}
            </div>
            {cust.det_flags?.length > 0 && <p className="text-xs mt-3" style={{ color: "var(--text-3)" }}>Deterioration flags: {cust.det_flags.join(", ")}</p>}
          </Card>
        </Reveal>
        <Reveal delay={0.05}>
          <Card title="Risk trajectory" sub="Predicted churn probability over 90 days">
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={traj}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="point" tick={{ fontSize: 12, fill: chartColors.tick }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 12, fill: chartColors.tick }} axisLine={false} tickLine={false} />
                <Tooltip content={<ChartTooltip />} />
                <Area type="monotone" dataKey="risk" stroke="none" fill="url(#rq-fill)" name="risk %" />
                <Line type="monotone" dataKey="risk" stroke="url(#rq-line)" strokeWidth={2.5} dot={{ r: 3, fill: "#FF4D6D", strokeWidth: 0 }} name="risk %" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Reveal>
      </div>
      <div className="grid md:grid-cols-2 gap-4 items-start">
        <Reveal>
          <Card glow title="Recommended next best action" sub="Max expected net = success × CLV − cost">
            {cust.action && (
              <div>
                <div className="text-lg font-extrabold capitalize tracking-tight" style={{ color: "var(--text-1)" }}>{cust.action.key.replaceAll("_", " ")}</div>
                <p className="text-sm mt-1 leading-relaxed" style={{ color: "var(--text-2)" }}>{cust.action.reason}</p>
                <div className="grid grid-cols-3 gap-2 mt-3 text-sm">
                  <div className="glass rounded-xl p-2.5"><div className="text-[11px]" style={{ color: "var(--text-3)" }}>Cost</div><div className="font-extrabold tnum" style={{ color: "var(--text-1)" }}>{inr(cust.action.cost)}</div></div>
                  <div className="glass rounded-xl p-2.5"><div className="text-[11px]" style={{ color: "var(--text-3)" }}>Success</div><div className="font-extrabold tnum" style={{ color: "var(--text-1)" }}>{pct(cust.action.success)}</div></div>
                  <div className="glass rounded-xl p-2.5"><div className="text-[11px]" style={{ color: "var(--text-3)" }}>Exp. ROI</div><div className="font-extrabold tnum text-semantic-success">{(cust.action.roi * 100).toFixed(0)}%</div></div>
                </div>
              </div>
            )}
          </Card>
        </Reveal>
        <Reveal delay={0.05}>
          <Card title="Profile & activity" sub={`${cust.product_count} products · balance ${inr(cust.total_balance)}`}>
            <div className="text-sm space-y-1.5" style={{ color: "var(--text-1)" }}>
              <p><span style={{ color: "var(--text-3)" }}>Products:</span> {cust.products.join(", ") || "—"}</p>
              <p><span style={{ color: "var(--text-3)" }}>Balances:</span> {cust.balances.map((acct: any) => `${acct.type} ${inr(acct.balance)}`).join(" · ")}</p>
              <p><span style={{ color: "var(--text-3)" }}>Txn:</span> <span className="tnum">{cust.txn_freq}/mo · {inr(cust.avg_txn)} avg · logins {cust.logins}/mo · complaints {cust.complaints}</span></p>
              <p><span style={{ color: "var(--text-3)" }}>Annual contribution (est.):</span> {inr(cust.annual_contrib)}</p>
            </div>
            <div className="mt-3">
              <p className="text-[11px] font-bold uppercase tracking-[0.1em] mb-1.5" style={{ color: "var(--text-3)" }}>Recent transactions</p>
              <div className="space-y-1 max-h-36 overflow-y-auto text-xs pr-1">
                {cust.transactions.map((txn: any, i: number) => (
                  <div key={i} className="flex justify-between py-1.5 border-b" style={{ borderColor: "var(--border)" }}>
                    <span style={{ color: "var(--text-3)" }}>{txn.ts.slice(0, 10)} · {txn.type}</span><span className="font-semibold tnum" style={{ color: "var(--text-1)" }}>{inr(txn.amount)}</span>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </Reveal>
      </div>
    </div>
  );
}
