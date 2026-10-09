"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { inr, num } from "@/lib/format";
import { Card, Loading, Err, PageHeader, StatCard, Table, THead, TH, TD, TRow, Badge } from "@/components/ui";
import { BrandDefs, ChartTooltip, chartColors } from "@/components/ui";
import { Reveal, Stagger, StaggerItem, Tilt } from "@/components/motion";
import ChurnOrb from "@/components/ChurnOrb";
import { Users, ShieldAlert, IndianRupee, Target, Wallet, Receipt, Percent, Crosshair } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, CartesianGrid, Area } from "recharts";

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState("");
  const load = () => {
    setErr("");
    Promise.all([
      api("/api/dashboard/summary"), api("/api/dashboard/risk-dist"),
      api("/api/dashboard/revenue-by-segment"), api("/api/dashboard/product-risk"),
      api("/api/dashboard/risk-trend"), api("/api/dashboard/quadrant"),
      api("/api/dashboard/campaign-perf"),
    ]).then(([summary, riskDist, revenueBySeg, productRisk, riskTrend, quadrants, campPerf]) =>
      setData({ summary, riskDist, revenueBySeg, productRisk, riskTrend, quadrants, campPerf })
    ).catch((e) => setErr(e.message));
  };
  useEffect(load, []);
  if (err) return <Err msg={err} retry={load} />;
  if (!data) return <Loading msg="Loading command center…" />;
  const { summary } = data;
  const total = Math.max(1, summary.total);
  const highPct = (summary.high / total) * 100;
  const riskColor = (b: string) => b === "High" ? "#FF4D6D" : b === "Medium" ? "#FBBF24" : "#34D399";

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Executive"
        title="COMMAND CENTER"
        desc="Who to save, what to do, what it costs, and expected return. All figures computed live from the database; predictions are estimates."
        actions={<Link href="/roi-simulator" className="inline-flex items-center gap-2 text-white text-sm font-semibold px-4 py-2 rounded-full shadow-glow-sm hover:-translate-y-px transition-all" style={{ backgroundImage: "linear-gradient(135deg,#C026D3,#EC2F8B 50%,#FF4D6D)" }}>Open ROI Simulator</Link>}
      />

      <Stagger className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: "Total customers", value: summary.total, fmt: (n: number) => num(Math.round(n)), icon: <Users size={15} /> },
          { label: "High risk", value: summary.high, fmt: (n: number) => num(Math.round(n)), hint: `${num(summary.medium)} medium`, icon: <ShieldAlert size={15} /> },
          { label: "Revenue at risk", value: summary.revenue_at_risk, fmt: (n: number) => inr(n), hint: "Σ churn prob × CLV", icon: <IndianRupee size={15} /> },
          { label: "Expected protected", value: summary.expected_protected, fmt: (n: number) => inr(n), hint: "realized from campaigns", icon: <Target size={15} /> },
          { label: "Retention budget", value: summary.retention_budget, fmt: (n: number) => inr(n), hint: "planning envelope", icon: <Wallet size={15} /> },
          { label: "Campaign cost", value: summary.campaign_cost, fmt: (n: number) => inr(n), hint: "realized spend", icon: <Receipt size={15} /> },
          { label: "Expected ROI", value: summary.expected_roi_pct, fmt: (n: number) => `${n.toFixed(1)}%`, hint: "net / cost", delta: `${summary.expected_roi_pct >= 0 ? "▲" : "▼"} live`, deltaTone: summary.expected_roi_pct >= 0 ? "up" : "down", icon: <Percent size={15} /> },
          { label: "Targeted / retained", value: summary.expected_retained, fmt: (n: number) => `${num(summary.customers_targeted)} / ${num(Math.round(n))}`, hint: `${num(summary.campaigns)} campaigns`, icon: <Crosshair size={15} /> },
        ].map((k: any) => (
          <StaggerItem key={k.label}><Tilt><StatCard label={k.label} value={k.value} format={k.fmt} hint={k.hint} delta={k.delta} deltaTone={k.deltaTone} icon={k.icon} /></Tilt></StaggerItem>
        ))}
      </Stagger>

      <Reveal>
        <Card glow title="Portfolio risk orb" sub="High-risk share of the customer base">
          <ChurnOrb highPct={highPct} total={summary.total} />
        </Card>
      </Reveal>

      <div className="grid md:grid-cols-3 gap-4">
        <Reveal delay={0.02}>
          <Card title="Churn risk distribution" sub="Low <35% · Medium 35–60% · High ≥60%">
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <BrandDefs id="dash" />
                <Pie data={data.riskDist} dataKey="count" nameKey="band" outerRadius={80} innerRadius={46} paddingAngle={3} strokeWidth={0}>
                  {data.riskDist.map((r: any, i: number) => <Cell key={i} fill={riskColor(r.band)} />)}
                </Pie>
                <Tooltip content={<ChartTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex justify-center gap-3 mt-1">
              {data.riskDist.map((r: any) => (
                <span key={r.band} className="flex items-center gap-1.5 text-xs" style={{ color: "var(--text-2)" }}>
                  <span className="w-2 h-2 rounded-full" style={{ background: riskColor(r.band) }} />{r.band} <b className="tnum">{r.count}</b>
                </span>
              ))}
            </div>
          </Card>
        </Reveal>
        <Reveal delay={0.06}>
          <Card title="Revenue at risk by segment (est.)">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={data.revenueBySeg} layout="vertical" margin={{ left: 8, right: 12 }}>
                <BrandDefs id="seg" />
                <XAxis type="number" hide /><YAxis type="category" dataKey="segment" width={80} tick={{ fontSize: 12, fill: chartColors.tick }} axisLine={false} tickLine={false} />
                <Tooltip content={<ChartTooltip formatter={(v: any) => inr(Number(v))} />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
                <Bar dataKey="rar" fill="url(#seg-bar)" radius={6} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Reveal>
        <Reveal delay={0.1}>
          <Card title="Risk trend" sub="Average predicted risk over time">
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={data.riskTrend.map((x: any) => ({ ...x, label: x.point }))} margin={{ left: -12, right: 8 }}>
                <BrandDefs id="trend" />
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="label" tick={{ fontSize: 11, fill: chartColors.tick }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: chartColors.tick }} axisLine={false} tickLine={false} />
                <Tooltip content={<ChartTooltip />} />
                <Area type="monotone" dataKey="avg_risk" stroke="none" fill="url(#trend-fill)" name="avg risk %" />
                <Line type="monotone" dataKey="avg_risk" stroke="url(#trend-line)" strokeWidth={2.5} dot={false} name="avg risk %" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Reveal>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <Reveal>
          <Card title="Product-wise risk" sub="Where is revenue at risk concentrated?">
            <div className="space-y-2.5">
              {data.productRisk.map((row: any) => (
                <div key={row.product} className="flex items-center gap-3 text-sm">
                  <div className="w-40 truncate font-medium" style={{ color: "var(--text-1)" }}>{row.product}</div>
                  <div className="flex-1 rounded-full h-2" style={{ background: "rgba(255,255,255,0.07)" }}>
                    <div className="h-2 rounded-full" style={{ width: `${Math.min(100, (row.rar / Math.max(1, data.productRisk[0].rar)) * 100)}%`, backgroundImage: "linear-gradient(90deg,#C026D3,#EC2F8B,#FF4D6D)" }} />
                  </div>
                  <div className="w-24 text-right tnum" style={{ color: "var(--text-2)" }}>{inr(row.rar)}</div>
                  <div className="w-20 text-right text-[11px] font-bold text-risk-high tnum">{row.high_risk} high-risk</div>
                </div>
              ))}
            </div>
          </Card>
        </Reveal>
        <Reveal delay={0.05}>
          <Card title="Value × Risk quadrants" sub={`Split at median CLV ${inr(data.quadrants.median_clv)}`}>
            <div className="grid grid-cols-2 gap-3 text-center">
              {[
                ["High value · High risk", data.quadrants.hv_hr, "text-risk-high border-rose-500/25 bg-rose-500/10"],
                ["High value · Low risk", data.quadrants.hv_lr, "text-semantic-success border-emerald-500/25 bg-emerald-500/10"],
                ["Low value · High risk", data.quadrants.lv_hr, "text-semantic-warning border-amber-500/25 bg-amber-500/10"],
                ["Low value · Low risk", data.quadrants.lv_lr, "", true],
              ].map(([label, value, cls, neutral]: any) => (
                <div key={label} className={`border rounded-2xl p-4 ${cls}`} style={neutral ? { borderColor: "var(--border)" } : undefined}>
                  <div className="text-2xl font-extrabold tnum" style={neutral ? { color: "var(--text-1)" } : undefined}>{value}</div>
                  <div className="text-[11px] font-semibold mt-1" style={neutral ? { color: "var(--text-2)" } : undefined}>{label}</div>
                </div>
              ))}
            </div>
          </Card>
        </Reveal>
      </div>

      <Reveal>
        <Card title="Campaign performance" sub="Realized results from A/B experiments">
          <Table>
            <THead><TH>Campaign</TH><TH>Status</TH><TH right>Revenue</TH><TH right>Lift</TH><TH right>ROI</TH></THead>
            <tbody>
              {data.campPerf.map((camp: any) => (
                <TRow key={camp.id}>
                  <TD><span className="font-semibold">{camp.name}</span></TD>
                  <TD><Badge tone={camp.status === "completed" ? "success" : "neutral"}>{camp.status}</Badge></TD>
                  <TD right>{inr(camp.revenue)}</TD>
                  <TD right>{(camp.lift * 100).toFixed(1)}%</TD>
                  <TD right><b>{camp.roi_pct == null ? "—" : `${camp.roi_pct}%`}</b></TD>
                </TRow>
              ))}
            </tbody>
          </Table>
        </Card>
      </Reveal>
    </div>
  );
}
