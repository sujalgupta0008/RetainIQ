"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { inr, pct } from "@/lib/format";
import { Card, Loading, Err } from "@/components/ui";

export default function Segments() {
  const [d, setD] = useState<any>(null);
  const [err, setErr] = useState("");
  const load = () => api("/api/segments/overview").then(setD).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);
  if (err) return <Err msg={err} retry={load} />;
  if (!d) return <Loading />;
  return (
    <div className="space-y-4">
      <div><h1 className="text-2xl font-bold">Segments</h1>
        <p className="text-sm text-slate-500">Value × risk quadrants split at median CLV {inr(d.median_clv)}. Save the high-value, high-risk box first.</p></div>
      <div className="grid md:grid-cols-2 gap-4">
        {d.segments.map((s: any) => (
          <Card key={s.segment} title={s.segment} right={<span className="text-sm font-bold text-red-600">{inr(s.rar)} at risk</span>}>
            <div className="flex gap-6 text-sm">
              <div><span className="text-slate-500">Customers:</span> <b>{s.count}</b></div>
              <div><span className="text-slate-500">Avg churn prob:</span> <b>{pct(s.avg_proba)}</b></div>
            </div>
            <div className="mt-2 bg-slate-100 rounded-full h-2">
              <div className="bg-indigo-500 h-2 rounded-full" style={{ width: `${Math.min(100, (s.rar / Math.max(1, d.segments[0].rar)) * 100)}%` }} />
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
