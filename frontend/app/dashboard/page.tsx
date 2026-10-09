"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { inr, num, pct } from "@/lib/format";
import {
  Card, Loading, Err, PageHeader, RiskBadge, Avatar, Badge,
  Table, THead, TH, TD, TRow, EmptyState, ChartTooltip, chartColors, ChartGradients,
} from "@/components/ui";
import { Reveal, Stagger, StaggerItem, Tilt } from "@/components/motion";
import {
  Users, ShieldAlert, IndianRupee, Phone, Mail, Eye, ArrowRight, Gauge,
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  PieChart, Pie, Cell, Line,
} from "recharts";

const SEG_PALETTE = ["#2563EB", "#3B82F6", "#14B8A6", "#6366F1", "#0EA5E9", "#8B5CF6"];

/** Display risk band from a churn probability (backend stores Low/Medium/High only). */
function bandOf(proba: number): "Low" | "Medium" | "High" | "Very High" {
  if (proba >= 0.8) return "Very High";
  if (proba >= 0.6) return "High";
  if (proba >= 0.35) return "Medium";
  return "Low";
}

/** Presentation mapping: intervention → outreach action shown in the priority queue. */
function outreach(action: string, priority: string): { label: string; icon: React.ReactNode } {
  if (priority === "Monitor") return { label: "Monitor", icon: <Eye size={13} /> };
  if (action === "rm_call" || action === "service_recovery") return { label: "Call now", icon: <Phone size={13} /> };
  return { label: "Email offer", icon: <Mail size={13} /> };
}

function MiniDonut({ shares }: { shares: Array<{ label: string; value: number; color: string }> }) {
  const total = Math.max(1, shares.reduce((s, x) => s + x.value, 0));
  const R = 15.5, C = 2 * Math.PI * R;
  let acc = 0;
  return (
    <svg viewBox="0 0 40 40" className="w-16 h-16 -rotate-90" role="img" aria-label="At-risk share">
      <circle cx="20" cy="20" r={R} fill="none" strokeWidth="7" stroke="rgba(100,116,139,0.15)" />
      {shares.map((s) => {
        const frac = s.value / total;
        const el = (
          <circle key={s.label} cx="20" cy="20" r={R} fill="none" stroke={s.color} strokeWidth="7"
            strokeDasharray={`${frac * C} ${C}`} strokeDashoffset={-acc * C} strokeLinecap="butt" />
        );
        acc += frac;
        return el;
      })}
    </svg>
  );
}

function AucGauge({ auc }: { auc: number }) {
  const R = 34, C = 2 * Math.PI * R;
  const frac = Math.max(0, Math.min(1, auc));
  return (
    <div className="relative w-28 h-28 mx-auto">
      <svg viewBox="0 0 84 84" className="w-full h-full -rotate-90">
        <circle cx="42" cy="42" r={R} fill="none" strokeWidth="9" stroke="rgba(100,116,139,0.15)" />
        <circle cx="42" cy="42" r={R} fill="none" stroke="#2563EB" strokeWidth="9" strokeLinecap="round"
          strokeDasharray={`${frac * C} ${C}`} style={{ transition: "stroke-dasharray 0.6s ease" }} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-extrabold tnum" style={{ color: "var(--text-1)" }}>{auc.toFixed(2)}</span>
        <span className="text-[9px] font-bold uppercase tracking-[0.12em]" style={{ color: "var(--text-3)" }}>AUC</span>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState("");
  const load = () => {
    setErr("");
    Promise.all([
      api("/api/dashboard/summary"), api("/api/dashboard/risk-dist"),
      api("/api/dashboard/risk-trend"), api("/api/segments/overview"),
      api("/api/dashboard/product-risk"), api("/api/predictions/metrics"),
      api("/api/recommendations?priority=&limit=100"), api("/api/dashboard/campaign-perf"),
    ]).then(([summary, riskDist, riskTrend, segments, productRisk, metrics, recs, campPerf]) =>
      setData({ summary, riskDist, riskTrend, segments, productRisk, metrics, recs, campPerf })
    ).catch((e) => setErr(e.message));
  };
  useEffect(load, []);
  if (err) return <Err msg={err} retry={load} />;
  if (!data) return <Loading msg="Loading retention dashboard…" />;
  const { summary } = data;
  const total = Math.max(1, summary.total);
  const atRisk = summary.high + summary.medium;
  const atRiskPct = ((atRisk / total) * 100).toFixed(1);
  const countOf = (b: string) => data.riskDist.find((r: any) => r.band === b)?.count || 0;

  const trend = data.riskTrend.map((x: any) => ({
    label: x.point === "today" ? "Today" : x.point.replace("d", "") + "d ago",
    highPct: +(((x.high || 0) / total) * 100).toFixed(1),
    avg: x.avg_risk,
  }));

  const segTotal = Math.max(1, data.segments.segments.reduce((s: number, g: any) => s + g.count, 0));
  const segDonut = data.segments.segments.map((g: any, i: number) => ({
    ...g, fill: SEG_PALETTE[i % SEG_PALETTE.length], share: (g.count / segTotal) * 100,
  }));

  const rarTotal = Math.max(1, data.productRisk.reduce((s: number, r: any) => s + (r.rar || 0), 0));
  const drivers = [...data.productRisk].sort((a: any, b: any) => b.rar - a.rar).slice(0, 6);

  const prioRank = (p: string) => p === "Critical" ? 0 : p === "High Priority" ? 1 : p === "Monitor" ? 2 : 3;
  const queue = [...(data.recs || [])].sort((a: any, b: any) => prioRank(a.priority) - prioRank(b.priority)).slice(0, 5);
  const callTop3 = [...(data.recs || [])].sort((a: any, b: any) => prioRank(a.priority) - prioRank(b.priority)).slice(0, 3);

  const kpi = "flex items-center gap-3";
  const chip = "w-10 h-10 rounded-xl flex items-center justify-center shrink-0";

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Overview"
        title="RETENTION DASHBOARD"
        desc="Live churn risk, retention priorities and expected return — computed from the database; predictions are estimates."
        actions={<Link href="/roi-simulator" className="inline-flex items-center gap-2 text-white text-sm font-semibold px-4 py-2 rounded-full shadow-glow-sm hover:-translate-y-px transition-all" style={{ backgroundImage: "linear-gradient(135deg,#2563EB,#3B82F6)" }}>Open ROI Simulator <ArrowRight size={15} /></Link>}
      />
      <ChartGradients />

      {/* KPI row */}
      <Stagger className="grid md:grid-cols-3 gap-4">
        <StaggerItem><Tilt>
          <Card hover>
            <div className={kpi}>
              <span className={chip} style={{ background: "rgba(37,99,235,0.12)", color: "#2563EB" }}><Users size={19} /></span>
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.08em]" style={{ color: "var(--text-3)" }}>Total Customers</div>
                <div className="text-[26px] leading-8 font-extrabold tnum tracking-tight" style={{ color: "var(--text-1)" }}>{num(summary.total)}</div>
              </div>
            </div>
            <div className="text-xs mt-2 tnum" style={{ color: "var(--text-2)" }}>across {data.segments.segments.length} segments · median CLV {inr(data.segments.median_clv)}</div>
          </Card>
        </Tilt></StaggerItem>
        <StaggerItem><Tilt>
          <Card hover>
            <div className="flex items-center gap-4">
              <MiniDonut shares={[
                { label: "High", value: countOf("High"), color: "#F97316" },
                { label: "Medium", value: countOf("Medium"), color: "#F59E0B" },
                { label: "Low", value: countOf("Low"), color: "#22C55E" },
              ]} />
              <div>
                <div className="flex items-center gap-2">
                  <span className={chip} style={{ background: "rgba(249,115,22,0.12)", color: "#F97316" }}><ShieldAlert size={19} /></span>
                  <span className="text-[11px] font-semibold uppercase tracking-[0.08em]" style={{ color: "var(--text-3)" }}>At Risk</span>
                </div>
                <div className="text-[26px] leading-8 font-extrabold tnum tracking-tight" style={{ color: "var(--text-1)" }}>{num(atRisk)}</div>
              </div>
              <div className="ml-auto text-right">
                <div className="text-xl font-extrabold tnum text-orange-600 dark:text-orange-400">{atRiskPct}%</div>
                <div className="text-[11px]" style={{ color: "var(--text-3)" }}>of total</div>
              </div>
            </div>
            <div className="flex gap-3 mt-2 text-[11px]" style={{ color: "var(--text-2)" }}>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#F97316]" />High {num(countOf("High"))}</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#F59E0B]" />Med {num(countOf("Medium"))}</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#22C55E]" />Low {num(countOf("Low"))}</span>
            </div>
          </Card>
        </Tilt></StaggerItem>
        <StaggerItem><Tilt>
          <Card hover>
            <div className={kpi}>
              <span className={chip} style={{ background: "rgba(20,184,166,0.12)", color: "#14B8A6" }}><IndianRupee size={19} /></span>
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.08em]" style={{ color: "var(--text-3)" }}>Retention Opportunity</div>
                <div className="text-[26px] leading-8 font-extrabold tnum tracking-tight text-teal-600 dark:text-teal-300">{inr(summary.expected_protected)}</div>
              </div>
            </div>
            <div className="text-xs mt-2 tnum" style={{ color: "var(--text-2)" }}>expected protected · {num(summary.campaigns)} campaigns · ROI {summary.expected_roi_pct}%</div>
          </Card>
        </Tilt></StaggerItem>
      </Stagger>

      {/* main grid + floating call card */}
      <div className="relative">
        <div className="grid lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 space-y-4">
            <Reveal>
              <Card title="Churn Risk Trend" sub="Share of customers at high risk over the last 90 days">
                <ResponsiveContainer width="100%" height={240}>
                  <AreaChart data={trend} margin={{ left: -14, right: 8, top: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
                    <XAxis dataKey="label" tick={{ fontSize: 11, fill: chartColors.tick }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: chartColors.tick }} axisLine={false} tickLine={false} tickFormatter={(v: number) => `${v}%`} />
                    <Tooltip content={<ChartTooltip />} />
                    <Area type="monotone" dataKey="highPct" name="High %" stroke="#2563EB" strokeWidth={2.5} fill="url(#rq-fill)" />
                    <Line type="monotone" dataKey="avg" name="Avg risk %" stroke="#14B8A6" strokeWidth={2} dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
                <p className="text-[11px] mt-1" style={{ color: "var(--text-3)" }}>
                  High = trajectory ≥ 60% (live). The Very High (≥ 80%) band isn’t stored by the model yet — bands are Low / Medium / High.
                </p>
              </Card>
            </Reveal>
            <Reveal delay={0.05}>
              <Card title="Retention Priority" sub="Top customers to act on now — ranked by expected net value">
                {queue.length === 0 ? (
                  <EmptyState title="Queue is clear" hint="No recommendations right now." />
                ) : (
                  <div className="divide-y" style={{ borderColor: "var(--border)" }}>
                    {queue.map((row: any) => {
                      const out = outreach(row.action, row.priority);
                      return (
                        <Link key={row.customer_id} href={`/customers/${row.customer_id}`}
                          className="flex items-center gap-3 py-2.5 rounded-xl px-2 -mx-2 transition-colors hover:bg-[#2563EB]/[0.05]">
                          <Avatar name={row.name} size={34} risk={bandOf(row.proba)} />
                          <span className="min-w-0 flex-1">
                            <span className="block text-sm font-bold truncate" style={{ color: "var(--text-1)" }}>{row.name}</span>
                            <span className="block text-[11px] tnum truncate" style={{ color: "var(--text-3)" }}>{pct(row.proba)} risk · {inr(row.rar)} at risk</span>
                          </span>
                          <RiskBadge band={bandOf(row.proba)} />
                          <span className="hidden sm:inline-flex items-center gap-1.5 text-[11px] font-bold px-2.5 py-1 rounded-full text-white shrink-0"
                            style={{ backgroundImage: "linear-gradient(135deg,#2563EB,#3B82F6)" }}>
                            {out.icon}{out.label}
                          </span>
                        </Link>
                      );
                    })}
                  </div>
                )}
              </Card>
            </Reveal>
          </div>
          <div className="space-y-4 pb-0 lg:pb-16">
            <Reveal delay={0.03}>
              <Card title="Customer Segments" sub="Share of customers by segment">
                {segDonut.length === 0 ? (
                  <EmptyState title="No segments" hint="Segment data will appear here." />
                ) : (
                  <>
                    <ResponsiveContainer width="100%" height={190}>
                      <PieChart>
                        <Pie data={segDonut} dataKey="count" nameKey="segment" outerRadius={72} innerRadius={48} paddingAngle={3} strokeWidth={0}>
                          {segDonut.map((g: any, i: number) => <Cell key={i} fill={g.fill} />)}
                        </Pie>
                        <Tooltip content={<ChartTooltip />} />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="space-y-1.5 mt-1">
                      {segDonut.map((g: any) => (
                        <div key={g.segment} className="flex items-center gap-2 text-[13px]">
                          <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: g.fill }} />
                          <span className="font-medium" style={{ color: "var(--text-1)" }}>{g.segment}</span>
                          <span className="ml-auto font-bold tnum" style={{ color: "var(--text-1)" }}>{g.share.toFixed(1)}%</span>
                          <span className="tnum w-12 text-right" style={{ color: "var(--text-3)" }}>{num(g.count)}</span>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </Card>
            </Reveal>
            <Reveal delay={0.06}>
              <Card title="Top Churn Drivers" sub="Products by share of revenue at risk">
                {drivers.length === 0 ? (
                  <EmptyState title="No driver data" hint="Product risk will appear here." />
                ) : (
                  <div className="space-y-2.5">
                    {drivers.map((row: any) => (
                      <div key={row.product}>
                        <div className="flex items-center justify-between text-[13px] mb-1">
                          <span className="font-medium truncate" style={{ color: "var(--text-1)" }}>{row.product}</span>
                          <span className="font-bold tnum ml-2" style={{ color: "var(--text-1)" }}>{((row.rar / rarTotal) * 100).toFixed(1)}%</span>
                        </div>
                        <div className="rounded-full h-2" style={{ background: "rgba(100,116,139,0.15)" }}>
                          <div className="h-2 rounded-full" style={{ width: `${Math.min(100, (row.rar / Math.max(1, drivers[0].rar)) * 100)}%`, backgroundImage: "linear-gradient(90deg,#2563EB,#3B82F6)" }} />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </Reveal>
            <Reveal delay={0.09}>
              <Card title="Model Performance" sub="Churn classifier evaluation">
                {data.metrics?.trained ? (
                  <div className="text-center">
                    <AucGauge auc={data.metrics.auc} />
                    <div className="grid grid-cols-3 gap-2 mt-3 text-center">
                      {[["Precision", data.metrics.precision], ["Recall", data.metrics.recall], ["F1", data.metrics.f1]].map(([l, v]: any) => (
                        <div key={l} className="rounded-xl border px-2 py-1.5" style={{ borderColor: "var(--border)" }}>
                          <div className="text-sm font-extrabold tnum" style={{ color: "var(--text-1)" }}>{(v * 1).toFixed(3)}</div>
                          <div className="text-[10px]" style={{ color: "var(--text-3)" }}>{l}</div>
                        </div>
                      ))}
                    </div>
                    <p className="text-[11px] mt-2.5" style={{ color: "var(--text-3)" }}>Trained on {num(data.metrics.n)} customers</p>
                  </div>
                ) : (
                  <EmptyState icon={<Gauge size={20} />} title="Model not trained" hint={data.metrics?.note || "Rule-based fallback in use."} />
                )}
              </Card>
            </Reveal>
          </div>
        </div>

        {/* floating call-prioritization mini card */}
        {callTop3.length > 0 && (
          <div className="mt-4 lg:mt-0 lg:absolute lg:-bottom-2 lg:right-6 lg:w-[340px] glass rounded-2xl p-4 shadow-card gradient-ring">
            <div className="text-[11px] font-bold uppercase tracking-[0.12em] gradient-text mb-2">Call prioritization</div>
            <div className="space-y-2">
              {callTop3.map((row: any, i: number) => (
                <Link key={row.customer_id} href={`/customers/${row.customer_id}`} className="flex items-center gap-2.5 rounded-xl px-2 py-1.5 -mx-1 transition-colors hover:bg-[#2563EB]/[0.06]">
                  <span className="w-5 h-5 rounded-full text-[10px] font-extrabold text-white flex items-center justify-center shrink-0"
                    style={{ backgroundImage: "linear-gradient(135deg,#2563EB,#3B82F6)" }}>{i + 1}</span>
                  <Avatar name={row.name} size={28} risk={bandOf(row.proba)} />
                  <span className="min-w-0 flex-1">
                    <span className="block text-[13px] font-bold truncate" style={{ color: "var(--text-1)" }}>{row.name}</span>
                    <span className="block text-[11px] tnum" style={{ color: "var(--text-3)" }}>{pct(row.proba)} · {inr(row.rar)}</span>
                  </span>
                  <Phone size={14} style={{ color: "#2563EB" }} />
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>

      <Reveal>
        <Card title="Campaign performance" sub="Realized results from A/B experiments">
          {data.campPerf.length === 0 ? (
            <EmptyState title="No campaigns yet" hint="Create one in Campaign Studio." />
          ) : (
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
          )}
        </Card>
      </Reveal>
    </div>
  );
}
