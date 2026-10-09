"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, Loading, Err, inputCls, btnGhost } from "@/components/ui";

export default function Settings() {
  const [me, setMe] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [tid, setTid] = useState("");
  const load = () => {
    Promise.all([api("/api/auth/me"), api("/api/audit?limit=50")])
      .then(([m, l]) => { setMe(m); setLogs(l); }).catch((e) => setErr(e.message));
  };
  useEffect(load, []);
  async function sw() {
    try {
      const r = await api(`/api/auth/switch?tenant_id=${tid}`, { method: "POST" });
      localStorage.setItem("retainiq_token", r.token);
      setMsg(`Switched to ${r.tenant}. Reloading…`);
      setTimeout(() => window.location.href = "/dashboard", 600);
    } catch (e: any) { setMsg(e.message); }
  }
  if (err) return <Err msg={err} retry={load} />;
  if (!me) return <Loading />;
  return (
    <div className="space-y-4 max-w-3xl">
      <div><h1 className="text-2xl font-bold">Settings</h1><p className="text-sm text-slate-500">Tenant, access, and audit trail.</p></div>
      <Card title="Workspace">
        <div className="text-sm space-y-1">
          <p><span className="text-slate-500">User:</span> {me.email} ({me.role})</p>
          <p><span className="text-slate-500">Tenant:</span> {me.tenant}</p>
          <p className="text-xs text-slate-400">All data on screen is synthetic demo data. AI provider: {typeof window !== "undefined" ? "auto (LLM if key set, else deterministic fallback)" : ""}.</p>
        </div>
        <div className="flex gap-2 mt-3">
          <input className={inputCls + " max-w-24"} placeholder="Tenant ID" value={tid} onChange={(e) => setTid(e.target.value)} />
          <button className={btnGhost} onClick={sw}>Switch tenant (demo)</button>
        </div>
        {msg && <p className="text-sm text-indigo-700 mt-2">{msg}</p>}
      </Card>
      <Card title="Audit log" sub="Logins, simulations, campaigns, uploads, AI questions">
        <div className="space-y-1 text-sm max-h-96 overflow-y-auto">
          {logs.map((l: any, i: number) => (
            <div key={i} className="flex gap-3 border-b border-slate-50 py-1.5">
              <span className="text-slate-400 text-xs w-36 shrink-0">{l.ts}</span>
              <span className="font-medium">{l.action}</span>
              <span className="text-slate-500 text-xs truncate">{l.meta}</span>
            </div>
          ))}
          {logs.length === 0 && <p className="text-sm text-slate-400">No events yet.</p>}
        </div>
      </Card>
    </div>
  );
}
