"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { inr, pct } from "@/lib/format";
import { Card, Loading, Err } from "@/components/ui";

export default function Analytics() {
  const [d, setD] = useState<any>(null);
  const [err, setErr] = useState("");
  const load = () => {
    Promise.all([api("/api/analytics/products"), api("/api/analytics/deterioration"), api("/api/analytics/alerts")])
      .then(([p, det, al]) => setD({ p, det, al })).catch((e) => setErr(e.message));
  };
  useEffect(load, []);
  if (err) return <Err msg={err} retry={load} />;
  if (!d) return <Loading />;
  return (
    <div className="space-y-4">
      <div><h1 className="text-2xl font-bold">Analytics</h1>
        <p className="text-sm text-slate-500">Product risk, behavioral deterioration, and live alerts.</p></div>
      {d.al.length > 0 && (
        <Card title={`Alerts (${d.al.length})`}>
          <div className="space-y-1.5">
            {d.al.slice(0, 8).map((a: any, i: number) => (
              <div key={i} className="text-sm bg-red-50 border border-red-100 rounded-lg px-3 py-2">
                {a.id ? <Link href={`/customers/${a.id}`} className="font-medium text-indigo-700 hover:underline">{a.customer}</Link> : null} {a.msg}
              </div>
            ))}
          </div>
        </Card>
      )}
      <div className="grid md:grid-cols-2 gap-4">
        <Card title="Product analytics" sub="Customers, high-risk count, revenue at risk">
          <table className="w-full text-sm">
            <thead><tr className="text-left text-xs text-slate-500 border-b"><th className="py-1">Product</th><th className="text-right">Cust.</th><th className="text-right">High-risk</th><th className="text-right">RaR</th></tr></thead>
            <tbody>{d.p.map((p: any) => (
              <tr key={p.product} className="border-b border-slate-50"><td className="py-1.5 font-medium">{p.product}</td>
                <td className="text-right">{p.customers}</td><td className="text-right text-red-600">{p.high_risk}</td>
                <td className="text-right font-semibold">{inr(p.rar)}</td></tr>
            ))}</tbody>
          </table>
        </Card>
        <Card title="Behavioral deterioration" sub="Declining transactions, balances, engagement + rising complaints/failures">
          <div className="space-y-1.5 max-h-96 overflow-y-auto">
            {d.det.slice(0, 25).map((x: any) => (
              <div key={x.id} className="flex items-center gap-2 text-sm border-b border-slate-50 py-1.5">
                <Link href={`/customers/${x.id}`} className="font-medium text-indigo-700 hover:underline">{x.name}</Link>
                <span className="text-xs text-slate-500 truncate">{x.flags.join(", ")}</span>
                <span className="ml-auto font-bold text-amber-600">{x.score}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
