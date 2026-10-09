"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Landmark } from "lucide-react";
import { btnPrimary, inputCls } from "@/components/ui";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Login() {
  const [email, setEmail] = useState("admin@demobank.in");
  const [password, setPassword] = useState("demo123");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const router = useRouter();

  async function submit(e?: React.FormEvent, em?: string) {
    e?.preventDefault();
    setBusy(true); setErr("");
    try {
      // FIX (S11): the typed password must be sent for normal sign-in; the hardcoded
      // demo password is used ONLY for the one-click demo buttons.
      const res = await fetch(`${BASE}/api/auth/login`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: em || email, password: em ? "demo123" : password }),
      });
      const d = await res.json();
      if (!res.ok) throw new Error(d.detail || "Login failed");
      localStorage.setItem("retainiq_token", d.token);
      router.replace("/dashboard");
    } catch (ex: any) { setErr(ex.message); } finally { setBusy(false); }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 px-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
        <div className="flex items-center gap-2 mb-1"><Landmark className="text-indigo-600" /><h1 className="text-xl font-bold">RetainIQ</h1></div>
        <p className="text-sm text-slate-500 mb-6">AI-powered retention & ROI intelligence for financial institutions.</p>
        <form onSubmit={(e) => submit(e)} className="space-y-3">
          <input className={inputCls} value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
          <input className={inputCls} type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" />
          {err && <p className="text-sm text-red-600">{err}</p>}
          <button className={btnPrimary + " w-full"} disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
        </form>
        <div className="mt-5 pt-4 border-t border-slate-100">
          <p className="text-xs text-slate-500 mb-2 font-medium">ONE-CLICK DEMO LOGIN</p>
          <div className="grid grid-cols-2 gap-2">
            <button onClick={() => submit(undefined, "admin@demobank.in")} className="border border-slate-200 rounded-lg px-3 py-2 text-sm hover:bg-slate-50">🏦 Demo Bank</button>
            <button onClick={() => submit(undefined, "admin@demofintech.in")} className="border border-slate-200 rounded-lg px-3 py-2 text-sm hover:bg-slate-50">💳 Demo Fintech</button>
          </div>
          <p className="text-[11px] text-slate-400 mt-3">Demo password: demo123 · Predictions shown are estimates.</p>
        </div>
      </div>
    </div>
  );
}
