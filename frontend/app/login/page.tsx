"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Landmark, ShieldCheck, FlaskConical, KeyRound, ArrowRight, Loader2, Play } from "lucide-react";
import { Button, Input } from "@/components/ui";
import { Reveal } from "@/components/motion";
import FloatingDash from "@/components/FloatingDash";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
// Optional Google Identity client ID. When unset (default), the Google button
// shows a clear message instead of a broken flow. Server exchange lives at
// POST /api/auth/google (backend-owned; not part of this UI).
const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";

function GoogleIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" aria-hidden>
      <path fill="#4285F4" d="M23.5 12.3c0-.9-.1-1.5-.3-2.3H12v4.3h6.5c-.1 1.1-.8 2.7-2.4 3.8l-.1.1 3.5 2.7.2.1c2.2-2 3.8-5 3.8-8.7z" />
      <path fill="#34A853" d="M12 24c3.2 0 5.9-1.1 7.9-2.9l-3.8-2.9c-1 .7-2.4 1.2-4.1 1.2-3.1 0-5.8-2.1-6.8-5l-.1.1-3.6 2.8v.1C3.5 21.4 7.4 24 12 24z" />
      <path fill="#FBBC05" d="M5.2 14.4c-.2-.8-.4-1.6-.4-2.4s.1-1.6.4-2.4l-.1-.1-3.6-2.8-.1.1C.5 8.6 0 10.2 0 12s.5 3.4 1.4 4.9l3.8-2.5z" />
      <path fill="#EA4335" d="M12 4.6c1.8 0 3 .8 3.7 1.4l3.3-3.2C17.9 1.1 15.2 0 12 0 7.4 0 3.5 2.6 1.4 6.7l3.8 2.9c1-2.9 3.7-5 6.8-5z" />
    </svg>
  );
}

export default function Login() {
  const [email, setEmail] = useState("admin@demobank.in");
  const [password, setPassword] = useState("demo123");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [gmsg, setGmsg] = useState("");
  const [gbusy, setGbusy] = useState(false);
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

  async function googleLogin() {
    setGmsg(""); setGbusy(true);
    try {
      const g: any = (window as any).google?.accounts?.id;
      if (!GOOGLE_CLIENT_ID || !g) {
        throw new Error("Google sign-in isn't connected yet (no client ID). Use email or one-click demo login.");
      }
      const credential = await new Promise<string>((resolve, reject) => {
        try {
          g.initialize({
            client_id: GOOGLE_CLIENT_ID,
            callback: (r: any) => (r?.credential ? resolve(r.credential) : reject(new Error("Google sign-in was cancelled."))),
          });
          g.prompt((n: any) => {
            if (n?.isNotDisplayed?.() || n?.isSkippedMoment?.()) {
              reject(new Error("Google prompt was blocked by the browser. Use email or demo login."));
            }
          });
        } catch (e: any) { reject(e); }
      });
      const res = await fetch(`${BASE}/api/auth/google`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ credential }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.detail || "Google sign-in failed on the server.");
      localStorage.setItem("retainiq_token", body.token);
      router.replace("/dashboard");
    } catch (e: any) { setGmsg(e.message); } finally { setGbusy(false); }
  }

  return (
    <div className="min-h-[100dvh] lg:h-[100dvh] lg:overflow-hidden grid lg:grid-cols-[1fr_1.05fr] items-center gap-4 lg:gap-8 px-5 md:px-10 py-4 lg:py-6 max-w-[1280px] mx-auto w-full">
      {/* left: headline */}
      <Reveal>
        <div className="max-w-lg">
          <div className="flex items-center gap-2 mb-4">
            <span className="w-8 h-8 rounded-xl flex items-center justify-center text-white shadow-glow-sm"
              style={{ backgroundImage: "linear-gradient(135deg,#2563EB,#3B82F6)" }}>
              <Landmark size={16} />
            </span>
            <span className="font-extrabold tracking-tight text-base" style={{ color: "var(--text-1)" }}>RetainIQ</span>
          </div>
          <p className="text-[11px] font-bold uppercase tracking-[0.18em] gradient-text mb-2">Retention ROI Intelligence</p>
          <h1 className="hero-title" style={{ color: "var(--text-1)" }}>
            Stop churn<br />before it starts.
          </h1>
          <p className="mt-3 text-sm leading-relaxed" style={{ color: "var(--text-2)" }}>
            RetainIQ scores every customer for churn risk, prescribes the next best
            action, and proves the ROI — live on your own portfolio data.
          </p>
          <div className="hide-short mt-4 hidden md:flex flex-wrap gap-2">
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
          <div className="mt-5 hidden md:flex flex-wrap gap-3">
            <Button size="lg" disabled={busy} onClick={() => submit(undefined, "admin@demobank.in")}>
              <Play size={15} /> Try the live demo
            </Button>
            <Button size="lg" variant="secondary" onClick={() => document.getElementById("email")?.focus()}>
              Sign in <ArrowRight size={15} />
            </Button>
          </div>
        </div>
      </Reveal>

      {/* right: 3D hero preview + form (hero never overlaps the card) */}
      <div className="relative min-w-0 lg:max-h-[100dvh] lg:overflow-hidden flex flex-col justify-center gap-3 py-1">
        <Reveal delay={0.1}>
          <div className="hidden lg:block hide-short login-hero">
            <FloatingDash />
          </div>
        </Reveal>
        <Reveal delay={0.18}>
          <div className="glass rounded-3xl p-4 md:p-5 w-full max-w-md mx-auto relative shadow-card">
            <h2 className="text-base font-extrabold tracking-tight" style={{ color: "var(--text-1)" }}>Welcome back</h2>
            <p className="text-[13px] mt-0.5 mb-3" style={{ color: "var(--text-2)" }}>Sign in to your retention dashboard.</p>
            <form onSubmit={(e) => submit(e)} className="space-y-2.5">
              <div>
                <label htmlFor="email" className="text-[11px] font-semibold uppercase tracking-[0.07em]" style={{ color: "var(--text-2)" }}>Email</label>
                <Input id="email" className="mt-1 min-h-[2.75rem]" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" autoComplete="email" />
              </div>
              <div>
                <label htmlFor="pw" className="text-[11px] font-semibold uppercase tracking-[0.07em]" style={{ color: "var(--text-2)" }}>Password</label>
                <Input id="pw" className="mt-1 min-h-[2.75rem]" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" autoComplete="current-password" />
              </div>
              {err && <p className="text-[13px] text-red-600 dark:text-red-400" role="alert">{err}</p>}
              <Button type="submit" className="w-full min-h-[2.75rem]" size="lg" loading={busy}>
                {busy ? "Signing in…" : <>Sign in <ArrowRight size={16} /></>}
              </Button>
            </form>
            <div className="flex items-center gap-3 my-3" aria-hidden>
              <span className="flex-1 h-px" style={{ background: "var(--border)" }} />
              <span className="text-[11px] font-semibold uppercase tracking-[0.1em]" style={{ color: "var(--text-3)" }}>or</span>
              <span className="flex-1 h-px" style={{ background: "var(--border)" }} />
            </div>
            <Button variant="secondary" className="w-full bg-white min-h-[2.75rem]" size="lg" loading={gbusy} onClick={googleLogin}>
              <GoogleIcon /> Continue with Google
            </Button>
            {gmsg && <p className="text-xs mt-2 text-center" role="status" style={{ color: "var(--text-2)" }}>{gmsg}</p>}
            <div className="mt-3 pt-3 border-t" style={{ borderColor: "var(--border)" }}>
              <p className="text-[11px] font-bold uppercase tracking-[0.12em] mb-2" style={{ color: "var(--text-3)" }}>One-click demo login</p>
              <div className="grid grid-cols-2 gap-2">
                <Button variant="secondary" onClick={() => submit(undefined, "admin@demobank.in")} disabled={busy}>
                  {busy && <Loader2 size={14} className="animate-spin" />} Demo Bank
                </Button>
                <Button variant="secondary" onClick={() => submit(undefined, "admin@demofintech.in")} disabled={busy}>Demo Fintech</Button>
              </div>
              <p className="text-[11px] mt-2" style={{ color: "var(--text-3)" }}>Demo password: demo123 · Predictions shown are estimates.</p>
            </div>
          </div>
        </Reveal>
      </div>
    </div>
  );
}
