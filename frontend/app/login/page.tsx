"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Landmark, ShieldCheck, FlaskConical, KeyRound, ArrowRight, Loader2, Play } from "lucide-react";
import { Button, Input } from "@/components/ui";
import { Reveal } from "@/components/motion";
import FloatingDash from "@/components/FloatingDash";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Login() {
  const [email, setEmail] = useState("admin@demobank.in");
  const [password, setPassword] = useState("demo123");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const router = useRouter();

  async function submit(e?: React.FormEvent, demoEmail?: string) {
    e?.preventDefault();
    setBusy(true); setErr("");
    try {
      const res = await fetch(`${BASE}/api/auth/login`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: demoEmail || email, password: demoEmail ? "demo123" : password }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail || "Login failed");
      localStorage.setItem("retainiq_token", body.token);
      router.replace("/dashboard");
    } catch (err: any) { setErr(err.message); } finally { setBusy(false); }
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2 items-center gap-8 px-5 md:px-12 py-10 max-w-[1280px] mx-auto w-full">
      {/* left: headline */}
      <Reveal>
        <div className="max-w-lg">
          <div className="flex items-center gap-2 mb-7">
            <span className="w-9 h-9 rounded-xl flex items-center justify-center text-white shadow-glow-sm"
              style={{ backgroundImage: "linear-gradient(135deg,#2563EB,#3B82F6)" }}>
              <Landmark size={18} />
            </span>
            <span className="font-extrabold tracking-tight text-lg" style={{ color: "var(--text-1)" }}>RetainIQ</span>
          </div>
          <p className="text-[11px] font-bold uppercase tracking-[0.18em] gradient-text mb-3">Retention ROI Intelligence</p>
          <h1 className="text-4xl md:text-[52px] leading-[1.04] font-extrabold tracking-tight" style={{ color: "#0B1A3A" }}>
            Stop churn<br />before it starts.
          </h1>
          <p className="mt-4 text-[15px] leading-relaxed" style={{ color: "var(--text-2)" }}>
            RetainIQ scores every customer for churn risk, prescribes the next best
            action, and proves the ROI — live on your own portfolio data.
          </p>
          <div className="mt-6 flex flex-wrap gap-2">
            {[
              { icon: <ShieldCheck size={14} />, t: "Live risk scoring" },
              { icon: <FlaskConical size={14} />, t: "80/20 experiments" },
              { icon: <KeyRound size={14} />, t: "Works without an API key" },
            ].map((c) => (
              <span key={c.t} className="inline-flex items-center gap-1.5 text-xs font-semibold rounded-full px-3 py-1.5 glass" style={{ color: "var(--text-1)" }}>
                <span style={{ color: "#2563EB" }}>{c.icon}</span>{c.t}
              </span>
            ))}
          </div>
          <div className="mt-7 flex flex-wrap gap-3">
            <Button size="lg" disabled={busy} onClick={() => submit(undefined, "admin@demobank.in")}>
              <Play size={15} /> Try the live demo
            </Button>
            <Button size="lg" variant="secondary" onClick={() => document.getElementById("email")?.focus()}>
              Sign in <ArrowRight size={15} />
            </Button>
          </div>
        </div>
      </Reveal>

      {/* right: 3D visual + form */}
      <div className="relative">
        <Reveal delay={0.1}>
          <FloatingDash />
        </Reveal>
        <Reveal delay={0.18}>
          <div className="glass rounded-3xl p-7 w-full max-w-md mx-auto mt-6 lg:-mt-4 relative shadow-card">
            <h2 className="text-lg font-extrabold tracking-tight" style={{ color: "var(--text-1)" }}>Welcome back</h2>
            <p className="text-[13px] mt-1 mb-5" style={{ color: "var(--text-2)" }}>Sign in to your retention dashboard.</p>
            <form onSubmit={(e) => submit(e)} className="space-y-3">
              <div>
                <label htmlFor="email" className="text-[11px] font-semibold uppercase tracking-[0.07em]" style={{ color: "var(--text-2)" }}>Email</label>
                <Input id="email" className="mt-1.5" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" autoComplete="email" />
              </div>
              <div>
                <label htmlFor="pw" className="text-[11px] font-semibold uppercase tracking-[0.07em]" style={{ color: "var(--text-2)" }}>Password</label>
                <Input id="pw" className="mt-1.5" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" autoComplete="current-password" />
              </div>
              {err && <p className="text-[13px] text-red-600 dark:text-red-400" role="alert">{err}</p>}
              <Button type="submit" className="w-full" size="lg" loading={busy}>
                {busy ? "Signing in…" : <>Sign in <ArrowRight size={16} /></>}
              </Button>
            </form>
            <div className="mt-5 pt-4 border-t" style={{ borderColor: "var(--border)" }}>
              <p className="text-[11px] font-bold uppercase tracking-[0.12em] mb-2" style={{ color: "var(--text-3)" }}>One-click demo login</p>
              <div className="grid grid-cols-2 gap-2">
                <Button variant="secondary" onClick={() => submit(undefined, "admin@demobank.in")} disabled={busy}>
                  {busy && <Loader2 size={14} className="animate-spin" />} Demo Bank
                </Button>
                <Button variant="secondary" onClick={() => submit(undefined, "admin@demofintech.in")} disabled={busy}>Demo Fintech</Button>
              </div>
              <p className="text-[11px] mt-2.5" style={{ color: "var(--text-3)" }}>Demo password: demo123 · Predictions shown are estimates.</p>
            </div>
          </div>
        </Reveal>
      </div>
    </div>
  );
}
