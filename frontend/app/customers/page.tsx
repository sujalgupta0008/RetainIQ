"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { inr, pct } from "@/lib/format";
import { Card, RiskBadge, PrioBadge, Loading, Err, inputCls } from "@/components/ui";

export default function Customers() {
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState("");
  const [search, setSearch] = useState("");
  const [risk, setRisk] = useState("");
  const [segment, setSegment] = useState("");
  const [sort, setSort] = useState("rar");
  const [page, setPage] = useState(1);

  const load = () => {
    const q = new URLSearchParams({ search, risk, segment, sort, page: String(page), page_size: "20" });
    api(`/api/customers?${q}`).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(() => { setErr(""); load(); }, [risk, segment, sort, page]);
  useEffect(() => { const t = setTimeout(() => { setPage(1); setErr(""); load(); }, 400); return () => clearTimeout(t); }, [search]);

  return (
    <div className="space-y-4">
      <div><h1 className="text-2xl font-bold">Customers</h1>
        <p className="text-sm text-slate-500">Ranked by revenue at risk. Click any row for the 360° view.</p></div>
      <Card>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
          <input className={inputCls} placeholder="Search name…" value={search} onChange={(e) => setSearch(e.target.value)} />
          <select className={inputCls} value={risk} onChange={(e) => setRisk(e.target.value)}>
            <option value="">All risk</option><option>High</option><option>Medium</option><option>Low</option>
          </select>
          <select className={inputCls} value={segment} onChange={(e) => setSegment(e.target.value)}>
            <option value="">All segments</option><option>Mass</option><option>Affluent</option><option>HNI</option><option>SME</option>
          </select>
          <select className={inputCls} value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="rar">Sort: Revenue at risk</option><option value="proba">Sort: Churn prob</option>
            <option value="clv">Sort: CLV</option><option value="name">Sort: Name</option>
          </select>
          <div className="text-sm text-slate-500 self-center">{data ? `${data.total} customers` : ""}</div>
        </div>
      </Card>
      {err ? <Err msg={err} retry={load} /> : !data ? <Loading /> : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="text-left text-xs text-slate-500 border-b">
                <th className="py-2 pr-2">Customer</th><th>Segment</th><th>Risk</th><th className="text-right">Churn prob</th>
                <th className="text-right">CLV</th><th className="text-right">Revenue at risk</th><th>Next action</th><th>Priority</th>
              </tr></thead>
              <tbody>
                {data.items.map((c: any) => (
                  <tr key={c.id} className="border-b border-slate-50 hover:bg-indigo-50/40">
                    <td className="py-2 pr-2"><Link href={`/customers/${c.id}`} className="font-medium text-indigo-700 hover:underline">{c.name}</Link></td>
                    <td className="text-slate-500">{c.segment}</td>
                    <td><RiskBadge band={c.band} /></td>
                    <td className="text-right">{pct(c.proba)}</td>
                    <td className="text-right">{inr(c.clv)}</td>
                    <td className="text-right font-semibold">{inr(c.rar)}</td>
                    <td className="text-slate-600 text-xs">{c.action.replaceAll("_", " ")}</td>
                    <td><PrioBadge p={c.priority} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between mt-3 text-sm">
            <span className="text-slate-500">Page {data.page} of {Math.max(1, Math.ceil(data.total / data.page_size))}</span>
            <div className="flex gap-2">
              <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="border rounded-lg px-3 py-1 disabled:opacity-40">Prev</button>
              <button disabled={page * data.page_size >= data.total} onClick={() => setPage(page + 1)} className="border rounded-lg px-3 py-1 disabled:opacity-40">Next</button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
