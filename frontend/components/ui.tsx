import React from "react";

export function Card({ title, sub, children, right }: { title?: string; sub?: string; children: React.ReactNode; right?: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
      {(title || right) && (
        <div className="flex items-start justify-between mb-3">
          <div>
            {title && <h3 className="font-semibold text-slate-900">{title}</h3>}
            {sub && <p className="text-xs text-slate-500 mt-0.5">{sub}</p>}
          </div>
          {right}
        </div>
      )}
      {children}
    </div>
  );
}

export function MetricCard({ label, value, hint, tone }: { label: string; value: string; hint?: string; tone?: "red" | "green" | "amber" | "slate" }) {
  const tones: Record<string, string> = {
    red: "text-red-600", green: "text-emerald-600", amber: "text-amber-600", slate: "text-slate-900",
  };
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
      <div className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</div>
      <div className={`text-2xl font-bold mt-1 ${tones[tone || "slate"]}`}>{value}</div>
      {hint && <div className="text-xs text-slate-400 mt-1">{hint}</div>}
    </div>
  );
}

export function RiskBadge({ band }: { band: string }) {
  const c = band === "High" ? "bg-red-100 text-red-700 border-red-200"
    : band === "Medium" ? "bg-amber-100 text-amber-700 border-amber-200"
    : "bg-emerald-100 text-emerald-700 border-emerald-200";
  return <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${c}`}>{band}</span>;
}

export function PrioBadge({ p }: { p: string }) {
  const c = p === "Critical" ? "bg-red-600 text-white"
    : p === "High Priority" ? "bg-orange-100 text-orange-700 border border-orange-200"
    : p === "Monitor" ? "bg-blue-100 text-blue-700 border border-blue-200"
    : "bg-slate-100 text-slate-600 border border-slate-200";
  return <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${c}`}>{p}</span>;
}

export function Loading({ msg }: { msg?: string }) {
  return <div className="py-16 text-center text-slate-500 text-sm animate-pulse">{msg || "Loading…"}</div>;
}

export function Err({ msg, retry }: { msg: string; retry?: () => void }) {
  return (
    <div className="py-10 text-center">
      <p className="text-sm text-red-600">{msg}</p>
      {retry && <button onClick={retry} className="mt-2 text-sm text-indigo-600 underline">Retry</button>}
    </div>
  );
}

export function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-xs font-medium text-slate-600">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  );
}

export const inputCls = "w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500";
export const btnPrimary = "bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg";
export const btnGhost = "border border-slate-300 hover:bg-slate-50 text-slate-700 text-sm font-medium px-4 py-2 rounded-lg";
