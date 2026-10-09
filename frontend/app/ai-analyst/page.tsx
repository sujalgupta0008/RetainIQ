"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, Loading, btnPrimary, inputCls } from "@/components/ui";

export default function AI() {
  const [sug, setSug] = useState<string[]>([]);
  const [q, setQ] = useState("How should we spend ₹10 lakh to maximize expected retention value?");
  const [log, setLog] = useState<{ q: string; a: string }[]>([]);
  const [busy, setBusy] = useState(false);
  useEffect(() => { api("/api/ai/suggested").then(setSug).catch(() => {}); }, []);
  async function ask(question: string) {
    if (!question.trim() || busy) return;
    setBusy(true);
    try {
      const r = await api("/api/ai/ask", { method: "POST", body: JSON.stringify({ question }) });
      setLog([{ q: question, a: r.answer }, ...log]);
      setQ("");
    } catch (e: any) { setLog([{ q: question, a: "Error: " + e.message }, ...log]); }
    finally { setBusy(false); }
  }
  return (
    <div className="space-y-4 max-w-3xl">
      <div><h1 className="text-2xl font-bold">AI Retention Analyst</h1>
        <p className="text-sm text-slate-500">Ask anything — budgets, segments, campaigns, products, model, or a specific customer in quotes e.g. Tell me about customer "Aarav Sharma". Grounded in live data, never invents numbers. Works without an API key.</p></div>
      <div className="flex flex-wrap gap-2">
        {sug.map((s) => <button key={s} onClick={() => ask(s)} className="text-xs border border-indigo-200 text-indigo-700 rounded-full px-3 py-1.5 hover:bg-indigo-50">{s}</button>)}
      </div>
      <Card>
        <div className="flex gap-2">
          <input className={inputCls} value={q} onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && ask(q)} placeholder="Ask about risk, segments, ROI, budgets…" />
          <button className={btnPrimary} disabled={busy} onClick={() => ask(q)}>{busy ? "…" : "Ask"}</button>
        </div>
      </Card>
      {log.length === 0 && <Loading msg="Ask a question above — e.g. which segment has the highest revenue at risk?" />}
      {log.map((m, i) => (
        <div key={i} className="space-y-2">
          <div className="bg-indigo-600 text-white rounded-xl px-4 py-2.5 text-sm ml-8">{m.q}</div>
          <div className="bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm mr-8 whitespace-pre-wrap">{m.a}</div>
        </div>
      ))}
    </div>
  );
}
