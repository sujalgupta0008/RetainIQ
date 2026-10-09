"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { inr, pct } from "@/lib/format";
import { Card, PrioBadge, Loading, Err, inputCls } from "@/components/ui";

export default function Recs() {
  const [rows, setRows] = useState<any[]>([]);
  const [err, setErr] = useState("");
  const [pr, setPr] = useState("");
  const load = () => {
    setErr("");
    api(`/api/recommendations?priority=${pr}&limit=100`).then(setRows).catch((e) => setErr(e.message));
  };
  useEffect(load, [pr]);
  if (err) return <Err msg={err} retry={load} />;
  if (!rows) return <Loading />;
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold">Next Best Actions</h1>
          <p className="text-sm text-slate-500">Prioritized retention queue — each recommendation maximizes expected net value.</p></div>
        <select className={inputCls + " max-w-48"} value={pr} onChange={(e) => setPr(e.target.value)}>
          <option value="">All priorities</option><option>Critical</option><option>High Priority</option><option>Monitor</option><option>Low Priority</option>
        </select>
      </div>
      <Card>
        <table className="w-full text-sm">
          <thead><tr className="text-left text-xs text-slate-500 border-b">
            <th className="py-2">Customer</th><th>Priority</th><th>Action</th><th>Why</th>
            <th className="text-right">Cost</th><th className="text-right">Success</th><th className="text-right">Exp. ROI</th>
          </tr></thead>
          <tbody>
            {rows.map((r: any) => (
              <tr key={r.customer_id} className="border-b border-slate-50">
                <td className="py-2"><Link href={`/customers/${r.customer_id}`} className="font-medium text-indigo-700 hover:underline">{r.name}</Link>
                  <div className="text-xs text-slate-400">{pct(r.proba)} risk · {inr(r.rar)} RaR</div></td>
                <td><PrioBadge p={r.priority} /></td>
                <td className="capitalize font-medium">{r.action.replaceAll("_", " ")}</td>
                <td className="text-xs text-slate-500 max-w-64">{r.reason}</td>
                <td className="text-right">{inr(r.cost)}</td>
                <td className="text-right">{pct(r.success)}</td>
                <td className="text-right font-bold text-emerald-600">{(r.roi * 100).toFixed(0)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
