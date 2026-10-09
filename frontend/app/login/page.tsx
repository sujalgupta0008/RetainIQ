"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Landmark, ShieldCheck, Sparkles, TrendingUp, ArrowRight, Loader2 } from "lucide-react";
import { Button, Input } from "@/components/ui";
import CustomerOrbit from "@/components/CustomerOrbit";

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
    <div className="min-h-screen grid lg:grid-cols-2 -m-0">
      {/* hero */}
      <div className="relative hidden lg:flex flex-col justify-center px-14 py-12 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <CustomerOrbit />
        </div>
        <div className="relative max-w-lg">
          <div className="flex items-center gap-2 mb-8">
            <span className="w-9 h-9 rounded-xl flex items-center justify-center text-white shadow-glow-sm"
              style={{ backgroundImage: "linear-gradient(135deg,#C026D3,#EC2F8B 50%,#FF4D6D)" }}>
              <Landmark size={18} />
            </span>
            <span className="font-extrabold tracking-tight text-lg" style={{ color: "var(--text-1)" }}>RetainIQ</span>
          </div>
          <p className="text-[11px] font-bold uppercase tracking-[0.18em] gradient-text mb-3">Retention ROI Intelligence</p>
          <h1 className="page-title text-5xl leading-[1.02]">SAVE THE RIGHT<br />CUSTOMERS.</h1>
          <p className="mt-4 text-[15px] leading-relaxed" style={{ color: "var(--text-2)" }}>
            AI-powered churn prediction, next-best-actions and live ROI simulation
            for financial institutions. Every number grounded in live data.
          </p>
          <div className="mt-8 grid grid-cols-3 gap-3">
            {[
              { icon: <ShieldCheck size={16} />, t: "Live risk scoring", s: "Low / Med / High" },
              { icon: <Sparkles size={16} />, t: "Next best action", s: "Max expected net" },
              { icon: <TrendingUp size={16} />, t: "ROI simulator", s: "Conservative → brave" },
            ].map((f) => (
              <div key={f.t} className="glass rounded-2xl p-3.5">
                <span style={{ color: "#EC2F8B" }}>{f.icon}</span>
                <div className="text-[13px] font-bold mt-2" style={{ color: "var(--text-1)" }}>{f.t}</div>
                <div className="text-[11px]" style={{ color: "var(--text-3)" }}>{f.s}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* form */}
      <div className="flex items-center justify-center px-5 py-10">
        <div className="glass gradient-ring rounded-3xl p-8 w-full max-w-md shadow-card">
          <div className="lg:hidden flex items-center gap-2 mb-6">
            <span className="w-9 h-9 rounded-xl flex items-center justify-center text-white"
              style={{ backgroundImage: "linear-gradient(135deg,#C026D3,#EC2F8B 50%,#FF4D6D)" }}>
              <Landmark size={18} />
            </span>
            <span className="font-extrabold text-lg" style={{ color: "var(--text-1)" }}>RetainIQ</span>
          </div>
          <h2 className="page-title text-2xl">WELCOME BACK</h2>
          <p className="text-[13px] mt-1.5 mb-6" style={{ color: "var(--text-2)" }}>Sign in to your retention command center.</p>
          <form onSubmit={(e) => submit(e)} className="space-y-3">
            <div>
              <label htmlFor="email" className="text-[11px] font-semibold uppercase tracking-[0.07em]" style={{ color: "var(--text-2)" }}>Email</label>
              <Input id="email" className="mt-1.5" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" autoComplete="email" />
            </div>
            <div>
              <label htmlFor="pw" className="text-[11px] font-semibold uppercase tracking-[0.07em]" style={{ color: "var(--text-2)" }}>Password</label>
              <Input id="pw" className="mt-1.5" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" autoComplete="current-password" />
            </div>
            {err && <p className="text-[13px] text-semantic-danger" role="alert">{err}</p>}
            <Button type="submit" className="w-full" size="lg" loading={busy}>
              {busy ? "Signing in…" : <>Sign in <ArrowRight size={16} /></>}
            </Button>
          </form>
          <div className="mt-6 pt-5 border-t" style={{ borderColor: "var(--border)" }}>
            <p className="text-[11px] font-bold uppercase tracking-[0.12em] mb-2.5" style={{ color: "var(--text-3)" }}>One-click demo login</p>
            <div className="grid grid-cols-2 gap-2">
              <Button variant="secondary" onClick={() => submit(undefined, "admin@demobank.in")} disabled={busy}>
                {busy && <Loader2 size={14} className="animate-spin" />} Demo Bank
              </Button>
              <Button variant="secondary" onClick={() => submit(undefined, "admin@demofintech.in")} disabled={busy}>Demo Fintech</Button>
            </div>
            <p className="text-[11px] mt-3" style={{ color: "var(--text-3)" }}>Demo password: demo123 · Predictions shown are estimates.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
