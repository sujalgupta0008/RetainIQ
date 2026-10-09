"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { inr, num, pct } from "@/lib/format";
import { Card, MetricCard, Loading, Field, PageHeader, Button, Badge } from "@/components/ui";
import { ChartTooltip, chartColors, ChartGradients } from "@/components/ui";
import { Reveal, Stagger, StaggerItem } from "@/components/motion";
import { useRouter } from "next/navigation";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

export default function ROI() {
  const router = useRouter();
  const [filters, setFilters] = useState({ min_proba: 0.5, min_clv: 50000, intervention_cost: 1000, success_rate: 0.28, reach: 1.0 });
  const [result, setResult] = useState<any>(null);
  const update = (k: string, v: number) => setFilters({ ...filters, [k]: v });
  useEffect(() => {
    const timer = setTimeout(() => {
      api("/api/roi/simulate", { method: "POST", body: JSON.stringify(filters) }).then(setResult).catch(() => {});
    }, 300);
    return () => clearTimeout(timer);
  }, [JSON.stringify(filters)]);
  if (!result) return <Loading msg="Loading simulator…" />;
  const scenarios = [
    { name: "Conservative", ...result.scenarios.conservative },
    { name: "Expected", ...result.scenarios.expected },
    { name: "Optimistic", ...result.scenarios.optimistic },
  ];
  const slider = "w-full accent-[#2563EB]";
  return (
    <div className="space-y-4">
      <PageHeader eyebrow="Hero" title="ROI SIMULATOR" desc="Who should we save, what should we spend, will it be profitable? All outputs are estimates."
        actions={<Badge tone="brand">HERO FEATURE</Badge>} />
      <ChartGradients />
      <div className="grid md:grid-cols-[320px_1fr] gap-4 items-start">
        <Reveal>
          <Card glow title="Inputs" sub="Charts update live">
            <div className="space-y-4">
              <Field label={`Churn threshold: ${(filters.min_proba * 100).toFixed(0)}%`}>
                <input type="range" min={0.2} max={0.8} step={0.05} value={filters.min_proba} onChange={(e) => update("min_proba", Number(e.target.value))} className={slider} aria-label="Churn threshold" />
              </Field>
              <Field label={`Min CLV: ${inr(filters.min_clv)}`}>
                <input type="range" min={0} max={300000} step={10000} value={filters.min_clv} onChange={(e) => update("min_clv", Number(e.target.value))} className={slider} aria-label="Min CLV" />
              </Field>
              <Field label={`Intervention cost: ${inr(filters.intervention_cost)} / customer`}>
                <input type="range" min={0} max={3000} step={100} value={filters.intervention_cost} onChange={(e) => update("intervention_cost", Number(e.target.value))} className={slider} aria-label="Intervention cost" />
              </Field>
              <Field label={`Expected success rate: ${(filters.success_rate * 100).toFixed(0)}%`}>
                <input type="range" min={0.05} max={0.6} step={0.01} value={filters.success_rate} onChange={(e) => update("success_rate", Number(e.target.value))} className={slider} aria-label="Success rate" />
              </Field>
              <Field label={`Campaign reach: ${(filters.reach * 100).toFixed(0)}%`}>
                <input type="range" min={0.2} max={1} step={0.05} value={filters.reach} onChange={(e) => update("reach", Number(e.target.value))} className={slider} aria-label="Reach" />
              </Field>
              <p className="text-xs" style={{ color: "var(--text-2)" }}>Audience: <b className="tnum">{num(result.audience)}</b> customers · avg CLV {inr(result.avg_clv)} · break-even success {pct(result.break_even_rate)}</p>
            </div>
          </Card>
        </Reveal>
        <div className="space-y-4">
          <Stagger className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {[
              { label: "Customers targeted", value: `${num(result.targeted)}` },
              { label: "Expected retained", value: `${num(Math.round(result.retained))}` },
              { label: "Campaign cost", value: inr(result.cost) },
              { label: "Revenue protected", value: inr(result.revenue) },
              { label: "Net value", value: inr(result.net) },
              { label: "ROI", value: `${result.roi_pct}%` },
            ].map((m) => (
              <StaggerItem key={m.label}><MetricCard label={m.label + " (est.)"} value={m.value} tone={m.label === "Net value" || m.label === "ROI" ? (result.net >= 0 ? "green" : "red") : m.label === "Expected retained" || m.label === "Revenue protected" ? "green" : "slate"} /></StaggerItem>
            ))}
          </Stagger>
          <Reveal>
            <Card title="Sensitivity analysis" sub="Same audience, scaled success assumptions">
              <ResponsiveContainer width="100%" height={230}>
                <BarChart data={scenarios.map((row: any) => ({ name: row.name, roi: row.roi_pct, net: row.net }))}>
                  <XAxis dataKey="name" tick={{ fontSize: 12, fill: chartColors.tick }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 12, fill: chartColors.tick }} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
                  <Bar dataKey="roi" name="ROI %" radius={8} fill="url(#rq-bar)">
                    {scenarios.map((_: any, i: number) => <Cell key={i} fill="url(#rq-bar)" />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <div className="grid grid-cols-3 gap-2 mt-3 text-sm">
                {scenarios.map((row: any) => (
                  <div key={row.name} className="glass rounded-xl p-3">
                    <div className="font-bold" style={{ color: "var(--text-1)" }}>{row.name}</div>
                    <div className="text-xs" style={{ color: "var(--text-3)" }}>success {pct(row.success)} · retained {num(Math.round(row.retained))}</div>
                    <div className="font-bold tnum mt-1" style={{ color: "var(--text-1)" }}>{inr(row.net)} net · {row.roi_pct}% ROI</div>
                  </div>
                ))}
              </div>
            </Card>
          </Reveal>
          <Button onClick={() => router.push("/campaigns")}>Create campaign from this audience →</Button>
        </div>
      </div>
    </div>
  );
}
