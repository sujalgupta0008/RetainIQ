"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { inr, pct } from "@/lib/format";
import { Card, Loading, Err, Button, PageHeader, Badge } from "@/components/ui";
import { Reveal } from "@/components/motion";

export default function CampaignDetail({ params }: { params: { id: string } }) {
  const [camp, setCamp] = useState<any>(null);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);
  const load = () => api(`/api/campaigns/${params.id}`).then(setCamp).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);
  async function launch() {
    setMsg("Launching & simulating outcomes…"); setBusy(true);
    try { await api(`/api/campaigns/${params.id}/launch`, { method: "POST" }); setMsg("Launched."); load(); }
    catch (e: any) { setMsg(e.message); }
    finally { setBusy(false); }
  }
  if (err) return <Err msg={err} retry={load} />;
  if (!camp) return <Loading />;
  const result = camp.results;
  return (
    <div className="space-y-4">
      <PageHeader
        eyebrow={`Campaign #${camp.id} · ${camp.status}`}
        title={String(camp.name).toUpperCase()}
        desc={`${camp.intervention.replaceAll("_", " ")} · ${inr(camp.offer_cost)}/customer · expected success ${pct(camp.expected_success)}`}
        actions={<>{camp.status !== "completed" ? <Button loading={busy} onClick={launch}>Launch campaign</Button> : <Badge tone="success">completed</Badge>}</>}
      />
      {msg && <p className="text-[13px]" style={{ color: "var(--text-2)" }}>{msg}</p>}
      {!result ? (
        <Reveal><Card><p className="text-sm" style={{ color: "var(--text-2)" }}>Draft — launch to run the 80/20 treatment/control experiment (simulated outcomes for demo).</p></Card></Reveal>
      ) : (
        <div className="grid md:grid-cols-2 gap-4 items-start">
          <Reveal>
            <Card title="Control vs Treatment" sub="Simulated execution — incremental lift = treatment − control retention">
              <div className="grid grid-cols-2 gap-3 text-center">
                <div className="glass rounded-2xl p-4"><div className="text-2xl font-extrabold tnum" style={{ color: "var(--text-1)" }}>{pct(result.ctrl_ret)}</div>
                  <div className="text-[11px] mt-1" style={{ color: "var(--text-3)" }}>Control retention (n={result.ctrl_n})</div></div>
                <div className="rounded-2xl p-4 text-white" style={{ backgroundImage: "linear-gradient(135deg,#1D4ED8,#2563EB,#3B82F6)" }}><div className="text-2xl font-extrabold tnum">{pct(result.treat_ret)}</div>
                  <div className="text-[11px] mt-1 opacity-90">Treatment retention (n={result.treat_n})</div></div>
              </div>
              <p className="mt-3 text-sm" style={{ color: "var(--text-2)" }}>Incremental lift: <b className="text-semantic-success tnum">{pct(result.lift)}</b></p>
            </Card>
          </Reveal>
          <Reveal delay={0.05}>
            <Card glow title="Financial outcome" sub="Realized from experiment, not predicted">
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span style={{ color: "var(--text-3)" }}>Cost</span><b className="tnum" style={{ color: "var(--text-1)" }}>{inr(result.cost)}</b></div>
                <div className="flex justify-between"><span style={{ color: "var(--text-3)" }}>Revenue protected</span><b className="tnum text-semantic-success">{inr(result.revenue)}</b></div>
                <div className="flex justify-between text-base pt-2 border-t" style={{ borderColor: "var(--border)" }}><span style={{ color: "var(--text-3)" }}>ROI</span><b className="tnum gradient-text">{(result.roi * 100).toFixed(1)}%</b></div>
              </div>
            </Card>
          </Reveal>
        </div>
      )}
    </div>
  );
}
