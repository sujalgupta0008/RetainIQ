"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { inr, pct } from "@/lib/format";
import { Card, Loading, Err, btnPrimary } from "@/components/ui";

export default function CampaignDetail({ params }: { params: { id: string } }) {
  const [c, setC] = useState<any>(null);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const load = () => api(`/api/campaigns/${params.id}`).then(setC).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);
  async function launch() {
    setMsg("Launching & simulating outcomes…");
    try { await api(`/api/campaigns/${params.id}/launch`, { method: "POST" }); setMsg("Launched."); load(); }
    catch (e: any) { setMsg(e.message); }
  }
  if (err) return <Err msg={err} retry={load} />;
  if (!c) return <Loading />;
  const r = c.results;
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold">{c.name}</h1>
          <p className="text-sm text-slate-500 capitalize">{c.intervention.replaceAll("_", " ")} · {inr(c.offer_cost)}/customer · expected success {pct(c.expected_success)} · {c.status}</p></div>
        {c.status !== "completed" && <button className={btnPrimary} onClick={launch}>Launch campaign</button>}
      </div>
      {msg && <p className="text-sm text-indigo-700">{msg}</p>}
      {!r ? <Card><p className="text-sm text-slate-500">Draft — launch to run the 80/20 treatment/control experiment (simulated outcomes for demo).</p></Card> : (
        <div className="grid md:grid-cols-2 gap-4">
          <Card title="Control vs Treatment" sub="Simulated execution — incremental lift = treatment − control retention">
            <div className="grid grid-cols-2 gap-3 text-center">
              <div className="bg-slate-50 rounded-xl p-4"><div className="text-2xl font-bold">{pct(r.ctrl_ret)}</div>
                <div className="text-xs text-slate-500">Control retention (n={r.ctrl_n})</div></div>
              <div className="bg-indigo-50 rounded-xl p-4"><div className="text-2xl font-bold text-indigo-700">{pct(r.treat_ret)}</div>
                <div className="text-xs text-slate-500">Treatment retention (n={r.treat_n})</div></div>
            </div>
            <p className="mt-3 text-sm">Incremental lift: <b className="text-emerald-600">{pct(r.lift)}</b></p>
          </Card>
          <Card title="Financial outcome" sub="Realized from experiment, not predicted">
            <div className="space-y-1.5 text-sm">
              <div className="flex justify-between"><span className="text-slate-500">Cost</span><b>{inr(r.cost)}</b></div>
              <div className="flex justify-between"><span className="text-slate-500">Revenue protected</span><b className="text-emerald-600">{inr(r.revenue)}</b></div>
              <div className="flex justify-between text-base"><span className="text-slate-500">ROI</span><b>{(r.roi * 100).toFixed(1)}%</b></div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
