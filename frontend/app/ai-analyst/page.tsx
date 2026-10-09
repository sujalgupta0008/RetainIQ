"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, Input, Button, PageHeader, EmptyState } from "@/components/ui";
import { Reveal } from "@/components/motion";
import { Bot, Send, Sparkles } from "lucide-react";

export default function AIAnalyst() {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [question, setQuestion] = useState("How should we spend ₹10 lakh to maximize expected retention value?");
  const [chat, setChat] = useState<{ q: string; a: string }[]>([]);
  const [busy, setBusy] = useState(false);
  useEffect(() => { api("/api/ai/suggested").then(setSuggestions).catch(() => {}); }, []);
  async function ask(text: string) {
    if (!text.trim() || busy) return;
    setBusy(true);
    const q = text;
    try {
      const resp = await api("/api/ai/ask", { method: "POST", body: JSON.stringify({ question: q }) });
      setChat((prev) => [{ q, a: resp.answer }, ...prev]);
      setQuestion("");
    } catch (e: any) { setChat((prev) => [{ q, a: "Error: " + e.message }, ...prev]); }
    finally { setBusy(false); }
  }
  return (
    <div className="space-y-4 max-w-3xl">
      <PageHeader eyebrow="Assistant" title="AI ANALYST" desc="Ask anything — budgets, segments, campaigns, products, model, or a specific customer in quotes e.g. Tell me about customer &quot;Aarav Sharma&quot;. Grounded in live data, never invents numbers. Works without an API key." />
      <div className="flex flex-wrap gap-2">
        {suggestions.map((item) => (
          <button key={item} onClick={() => ask(item)}
            className="text-xs font-medium rounded-full px-3.5 py-2 glass glass-hover transition-all" style={{ color: "var(--text-1)" }}>
            <span className="mr-1.5" style={{ color: "#2563EB" }}>✦</span>{item}
          </button>
        ))}
      </div>
      <Reveal>
        <Card glow>
          <div className="flex gap-2">
            <Input value={question} onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && ask(question)} placeholder="Ask about risk, segments, ROI, budgets…" aria-label="Ask analyst" />
            <Button disabled={busy} loading={busy} onClick={() => ask(question)} aria-label="Send question"><Send size={15} /></Button>
          </div>
        </Card>
      </Reveal>
      {chat.length === 0 && (
        <EmptyState icon={<Bot size={20} />} title="Ask your first question" hint="Try: which segment has the highest revenue at risk?" />
      )}
      {chat.map((msg, i) => (
        <Reveal key={i} delay={Math.min(i * 0.03, 0.15)}>
          <div className="space-y-2">
            <div className="rounded-2xl px-4 py-3 text-sm ml-8 text-white" style={{ backgroundImage: "linear-gradient(135deg,#1D4ED8,#2563EB 60%,#3B82F6)" }}>{msg.q}</div>
            <div className="glass rounded-2xl px-4 py-3.5 text-sm mr-8 whitespace-pre-wrap leading-relaxed flex gap-2.5" style={{ color: "var(--text-1)" }}>
              <Sparkles size={15} className="shrink-0 mt-0.5" style={{ color: "#2563EB" }} />
              <span>{msg.a}</span>
            </div>
          </div>
        </Reveal>
      ))}
    </div>
  );
}
