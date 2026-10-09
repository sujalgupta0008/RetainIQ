"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, Loading, Err, Input, Button, PageHeader, Avatar, EmptyState } from "@/components/ui";
import { Reveal } from "@/components/motion";

export default function Settings() {
  const [me, setMe] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [tenantId, setTenantId] = useState("");
  const load = () => {
    Promise.all([api("/api/auth/me"), api("/api/audit?limit=50")])
      .then(([profile, auditLogs]) => { setMe(profile); setLogs(auditLogs); }).catch((e) => setErr(e.message));
  };
  useEffect(load, []);
  async function switchTenant() {
    if (me?.role !== "admin") { setMsg("Tenant switching requires an admin account. Please sign in as an admin to use this demo action."); return; }
    const id = Number(tenantId);
    if (!Number.isInteger(id) || id <= 0) { setMsg("Enter a valid numeric Tenant ID."); return; }
    try {
      const resp = await api(`/api/auth/switch?tenant_id=${encodeURIComponent(String(id))}`, { method: "POST" });
      localStorage.setItem("retainiq_token", resp.token);
      setMsg(`Switched to ${resp.tenant}. Reloading…`);
      setTimeout(() => window.location.href = "/dashboard", 600);
    } catch (e: any) { setMsg(e.message); }
  }
  if (err) return <Err msg={err} retry={load} />;
  if (!me) return <Loading />;
  return (
    <div className="space-y-4 max-w-3xl">
      <PageHeader eyebrow="Workspace" title="SETTINGS" desc="Tenant, access, and audit trail." />
      <Reveal>
        <Card glow title="Workspace">
          <div className="flex items-center gap-3 mb-4">
            <Avatar name={me.tenant || me.email} size={44} />
            <div>
              <div className="font-bold" style={{ color: "var(--text-1)" }}>{me.tenant}</div>
              <div className="text-[13px]" style={{ color: "var(--text-2)" }}>{me.email} ({me.role})</div>
            </div>
          </div>
          <p className="text-xs" style={{ color: "var(--text-3)" }}>All data on screen is synthetic demo data. AI provider: auto (LLM if key set, else deterministic fallback).</p>
          <div className="flex gap-2 mt-3">
            <Input className="!max-w-32" placeholder="Tenant ID" aria-label="Tenant ID" value={tenantId} onChange={(e) => setTenantId(e.target.value)} disabled={me?.role !== "admin"} />
            <Button variant="secondary" onClick={switchTenant} disabled={me?.role !== "admin"}>Switch tenant (demo)</Button>
          </div>
          {me?.role !== "admin" && <p className="text-xs mt-2" style={{ color: "var(--text-3)" }}>Signed in as {me?.role} — tenant switching is admin-only.</p>}
          {msg && <p className="text-[13px] mt-2" style={{ color: "var(--text-2)" }}>{msg}</p>}
        </Card>
      </Reveal>
      <Reveal delay={0.05}>
        <Card title="Audit log" sub="Logins, simulations, campaigns, uploads, AI questions">
          <div className="space-y-1 text-sm max-h-96 overflow-y-auto pr-1">
            {logs.map((entry: any, i: number) => (
              <div key={i} className="flex gap-3 py-2 border-b" style={{ borderColor: "var(--border)" }}>
                <span className="text-xs w-36 shrink-0 tnum" style={{ color: "var(--text-3)" }}>{entry.ts}</span>
                <span className="font-semibold shrink-0" style={{ color: "var(--text-1)" }}>{entry.action}</span>
                <span className="text-xs truncate" style={{ color: "var(--text-2)" }}>{entry.meta}</span>
              </div>
            ))}
            {logs.length === 0 && <EmptyState title="No events yet" hint="Actions across the app will appear here." />}
          </div>
        </Card>
      </Reveal>
    </div>
  );
}
