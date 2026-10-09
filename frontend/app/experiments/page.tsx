"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { inr, pct } from "@/lib/format";
import { Card, Loading, Err } from "@/components/ui";

export default function Experiments() {
  const [rows, setRows] = useState<any[]>([]);
  const [err, setErr] = useState("");
  const load = () => api("/api/experiments").then(setRows).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);
  if (err) return <Err msg={err} retry={load} />;
  if (!rows) return <Loading />;
  return (
    <div className="space-y-4">
      <div><h1 className="text-2xl font-bold">Experiments</h1>
        <p className="text-sm text-slate-500">Every campaign runs an A/B test: 80% treatment, 20% control. Outcomes simulated for demo.</p></div>
      <Card>
        <table className="w-full text-sm">
          <thead><tr className="text-left text-xs text-slate-500 border-b">
            <th className="py-2">Experiment</th><th className="text-right">Treat / Ctrl n</th>
            <th className="text-right">Treat ret.</th><th className="text-right">Ctrl ret.</th>
            <th className="text-right">Lift</th><th className="text-right">Revenue</th><th className="text-right">ROI</th>
          </tr></thead>
          <tbody>
            {rows.map((e: any) => (
              <tr key={e.id} className="border-b border-slate-50">
                <td className="py-2 font-medium">{e.name}<div className="text-xs text-slate-400">{e.campaign}</div></td>
                {e.results ? (<>
                  <td className="text-right">{e.results.treat_n} / {e.results.ctrl_n}</td>
                  <td className="text-right">{pct(e.results.treat_ret)}</td>
                  <td className="text-right">{pct(e.results.ctrl_ret)}</td>
                  <td className="text-right font-bold text-emerald-600">{pct(e.results.lift)}</td>
                  <td className="text-right">{inr(e.results.revenue)}</td>
                  <td className="text-right font-bold">{(e.results.roi * 100).toFixed(1)}%</td>
                </>) : <td colSpan={6} className="text-right text-slate-400">pending launch</td>}
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
