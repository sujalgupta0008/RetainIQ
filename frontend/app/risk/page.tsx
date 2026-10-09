"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, Loading, Err, btnGhost } from "@/components/ui";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";

export default function Risk() {
  const [d, setD] = useState<any>(null);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const load = () => {
    Promise.all([api("/api/dashboard/risk-dist"), api("/api/predictions/metrics")])
      .then(([rd, m]) => setD({ rd, m })).catch((e) => setErr(e.message));
  };
  useEffect(load, []);
  async function retrain() {
    setMsg("Retraining…");
    try { await api("/api/predictions/retrain", { method: "POST" }); setMsg("Retrained & predictions refreshed."); load(); }
    catch (e: any) { setMsg(e.message); }
  }
  if (err) return <Err msg={err} retry={load} />;
  if (!d) return <Loading />;
  const m = d.m;
  const cm = m.confusion || [[0, 0], [0, 0]];
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold">Risk & Model</h1>
          <p className="text-sm text-slate-500">XGBoost primary (HistGradientBoosting fallback) + Logistic Regression baseline. Optimized for AUC, not just accuracy.</p></div>
        <button onClick={retrain} className={btnGhost}>Retrain model</button>
      </div>
      {msg && <p className="text-sm text-indigo-700">{msg}</p>}
      <div className="grid md:grid-cols-2 gap-4">
        <Card title="Risk distribution">
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={d.rd}><XAxis dataKey="band" /><YAxis /><Tooltip />
              <Bar dataKey="count" fill="#6366f1" radius={6} /></BarChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Model evaluation" sub={m.trained ? `Trained on ${m.n} customers` : "Fallback rules in use"}>
          {m.trained ? (
            <div>
              <div className="grid grid-cols-4 gap-2 text-center">
                {[["ROC-AUC", m.auc], ["Precision", m.precision], ["Recall", m.recall], ["F1", m.f1]].map(([l, v]: any) => (
                  <div key={l} className="bg-slate-50 rounded-lg p-3">
                    <div className="text-lg font-bold text-indigo-700">{(v * 1).toFixed(3)}</div>
                    <div className="text-xs text-slate-500">{l}</div>
                  </div>
                ))}
              </div>
              <p className="text-xs font-medium text-slate-500 mt-4 mb-1">CONFUSION MATRIX (threshold 0.5)</p>
              <div className="grid grid-cols-2 gap-2 text-center text-sm max-w-xs">
                <div className="bg-emerald-50 border rounded-lg p-2">TN<br /><b>{cm[0][0]}</b></div>
                <div className="bg-red-50 border rounded-lg p-2">FP<br /><b>{cm[0][1]}</b></div>
                <div className="bg-red-50 border rounded-lg p-2">FN<br /><b>{cm[1][0]}</b></div>
                <div className="bg-emerald-50 border rounded-lg p-2">TP<br /><b>{cm[1][1]}</b></div>
              </div>
            </div>
          ) : <p className="text-sm text-slate-500">{m.note}</p>}
        </Card>
      </div>
      <Card title="How prediction works" sub="Feature engineering → train/test split → XGBoost → SHAP-style explanations">
        <p className="text-sm text-slate-600">16 behavioral features (tenure, balances, trends, frequency, complaints, logins, inactivity, failed rate…). Risk bands: Low &lt;35%, Medium 35–60%, High ≥60%. Explanations compare each customer against the tenant median — never invented.</p>
      </Card>
    </div>
  );
}
