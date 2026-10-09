"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, Loading, Err, Button, PageHeader } from "@/components/ui";
import { ChartTooltip, chartColors, ChartGradients } from "@/components/ui";
import { Reveal, Stagger, StaggerItem } from "@/components/motion";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export default function Risk() {
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);
  const load = () => {
    Promise.all([api("/api/dashboard/risk-dist"), api("/api/predictions/metrics")])
      .then(([riskDist, metrics]) => setData({ riskDist, metrics })).catch((e) => setErr(e.message));
  };
  useEffect(load, []);
  async function retrain() {
    setMsg("Retraining…"); setBusy(true);
    try { await api("/api/predictions/retrain", { method: "POST" }); setMsg("Retrained & predictions refreshed."); load(); }
    catch (e: any) { setMsg(e.message); }
    finally { setBusy(false); }
  }
  if (err) return <Err msg={err} retry={load} />;
  if (!data) return <Loading />;
  const metrics = data.metrics;
  const confusion = metrics.confusion || [[0, 0], [0, 0]];
  const barData = data.riskDist.map((r: any) => ({ ...r, fill: r.band === "High" ? "#F97316" : r.band === "Medium" ? "#F59E0B" : "#22C55E" }));
  return (
    <div className="space-y-4">
      <PageHeader eyebrow="Model" title="RISK & MODEL" desc="XGBoost primary (HistGradientBoosting fallback) + Logistic Regression baseline. Optimized for AUC, not just accuracy."
        actions={<Button variant="secondary" loading={busy} onClick={retrain}>Retrain model</Button>} />
      {msg && <p className="text-[13px]" style={{ color: "var(--text-2)" }}>{msg}</p>}
      <ChartGradients />
      <div className="grid md:grid-cols-2 gap-4 items-start">
        <Reveal>
          <Card title="Risk distribution">
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={barData}>
                <XAxis dataKey="band" tick={{ fontSize: 12, fill: chartColors.tick }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 12, fill: chartColors.tick }} axisLine={false} tickLine={false} />
                <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
                <Bar dataKey="count" radius={8} fill="url(#rq-bar)" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Reveal>
        <Reveal delay={0.05}>
          <Card title="Model evaluation" sub={metrics.trained ? `Trained on ${metrics.n} customers` : "Fallback rules in use"}>
            {metrics.trained ? (
              <div>
                <Stagger className="grid grid-cols-4 gap-2 text-center">
                  {[["ROC-AUC", metrics.auc], ["Precision", metrics.precision], ["Recall", metrics.recall], ["F1", metrics.f1]].map(([label, value]: any) => (
                    <StaggerItem key={label}>
                      <div className="glass rounded-xl p-3">
                        <div className="text-lg font-extrabold tnum gradient-text">{(value * 1).toFixed(3)}</div>
                        <div className="text-[11px] mt-0.5" style={{ color: "var(--text-3)" }}>{label}</div>
                      </div>
                    </StaggerItem>
                  ))}
                </Stagger>
                <p className="text-[11px] font-bold uppercase tracking-[0.1em] mt-4 mb-2" style={{ color: "var(--text-3)" }}>Confusion matrix (threshold 0.5)</p>
                <div className="grid grid-cols-2 gap-2 text-center text-sm max-w-xs">
                  <div className="rounded-xl border border-emerald-500/25 bg-emerald-500/10 p-2.5">TN<br /><b className="tnum"> {confusion[0][0]}</b></div>
                  <div className="rounded-xl border border-rose-500/25 bg-rose-500/10 p-2.5">FP<br /><b className="tnum">{confusion[0][1]}</b></div>
                  <div className="rounded-xl border border-rose-500/25 bg-rose-500/10 p-2.5">FN<br /><b className="tnum">{confusion[1][0]}</b></div>
                  <div className="rounded-xl border border-emerald-500/25 bg-emerald-500/10 p-2.5">TP<br /><b className="tnum">{confusion[1][1]}</b></div>
                </div>
              </div>
            ) : <p className="text-sm" style={{ color: "var(--text-2)" }}>{metrics.note}</p>}
          </Card>
        </Reveal>
      </div>
      <Reveal>
        <Card title="How prediction works" sub="Feature engineering → train/test split → XGBoost → SHAP-style explanations">
          <p className="text-sm leading-relaxed" style={{ color: "var(--text-2)" }}>16 behavioral features (tenure, balances, trends, frequency, complaints, logins, inactivity, failed rate…). Risk bands: Low &lt;35%, Medium 35–60%, High ≥60%. Explanations compare each customer against the tenant median — never invented.</p>
          <div className="grid grid-cols-3 gap-2 mt-3">
            {[["Low", "#22C55E", "< 35%"], ["Medium", "#F59E0B", "35–60%"], ["High", "#F97316", "≥ 60%"]].map(([b, c, r]) => (
              <div key={b} className="glass rounded-xl p-3 text-center">
                <span className="inline-block w-2.5 h-2.5 rounded-full mb-1" style={{ background: c, boxShadow: `0 0 10px ${c}` }} />
                <div className="text-sm font-bold" style={{ color: "var(--text-1)" }}>{b}</div>
                <div className="text-[11px] tnum" style={{ color: "var(--text-3)" }}>{r}</div>
              </div>
            ))}
          </div>
        </Card>
      </Reveal>
    </div>
  );
}
