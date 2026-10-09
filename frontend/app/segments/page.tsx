"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { inr, pct } from "@/lib/format";
import { Card, Loading, Err, PageHeader } from "@/components/ui";
import { Reveal, Stagger, StaggerItem } from "@/components/motion";

export default function Segments() {
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState("");
  const load = () => api("/api/segments/overview").then(setData).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);
  if (err) return <Err msg={err} retry={load} />;
  if (!data) return <Loading />;
  return (
    <div className="space-y-4">
      <PageHeader eyebrow="Portfolio" title="SEGMENTS" desc={`Value × risk quadrants split at median CLV ${inr(data.median_clv)}. Save the high-value, high-risk box first.`} />
      <Stagger className="grid md:grid-cols-2 gap-4">
        {data.segments.map((seg: any) => (
          <StaggerItem key={seg.segment}>
            <Card hover title={seg.segment} right={<span className="text-sm font-extrabold tnum text-risk-high">{inr(seg.rar)} at risk</span>}>
              <div className="flex gap-6 text-[13px]">
                <div><span style={{ color: "var(--text-3)" }}>Customers:</span> <b className="tnum" style={{ color: "var(--text-1)" }}>{seg.count}</b></div>
                <div><span style={{ color: "var(--text-3)" }}>Avg churn prob:</span> <b className="tnum" style={{ color: "var(--text-1)" }}>{pct(seg.avg_proba)}</b></div>
              </div>
              <div className="mt-3 rounded-full h-2" style={{ background: "rgba(255,255,255,0.07)" }}>
                <div className="h-2 rounded-full" style={{ width: `${Math.min(100, (seg.rar / Math.max(1, data.segments[0].rar)) * 100)}%`, backgroundImage: "linear-gradient(90deg,#2563EB,#3B82F6)" }} />
              </div>
            </Card>
          </StaggerItem>
        ))}
      </Stagger>
      <Reveal><p className="text-[11px]" style={{ color: "var(--text-3)" }}>Bars are relative to the largest segment by revenue at risk.</p></Reveal>
    </div>
  );
}
