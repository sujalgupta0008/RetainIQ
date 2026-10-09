"use client";
import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { Loader2 } from "lucide-react";

/* ---------- utils ---------- */
export function cn(...xs: Array<string | false | null | undefined>) {
  return xs.filter(Boolean).join(" ");
}

export function useCountUp(target: number, opts?: { duration?: number; enabled?: boolean }) {
  const duration = opts?.duration ?? 700;
  const enabled = opts?.enabled ?? true;
  const [val, setVal] = useState(0);
  const raf = useRef<number>(0);
  const reduced = useRef(false);
  useEffect(() => {
    try { reduced.current = window.matchMedia("(prefers-reduced-motion: reduce)").matches; } catch { reduced.current = true; }
  }, []);
  useEffect(() => {
    if (!enabled || !Number.isFinite(target)) { setVal(target || 0); return; }
    if (reduced.current) { setVal(target); return; }
    const t0 = performance.now();
    const tick = (t: number) => {
      const p = Math.min(1, (t - t0) / duration);
      const e = 1 - Math.pow(1 - p, 3);
      setVal(target * e);
      if (p < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [target, duration, enabled]);
  return val;
}

/* ---------- Card ---------- */
export function Card({ title, sub, children, right, className, glow, hover }: {
  title?: string; sub?: string; children: React.ReactNode; right?: React.ReactNode;
  className?: string; glow?: boolean; hover?: boolean;
}) {
  return (
    <section className={cn("glass rounded-2xl p-4 shadow-card", hover && "glass-hover", glow && "shadow-glow", className)}>
      {(title || right) && (
        <div className="flex items-start justify-between gap-3 mb-4">
          <div className="min-w-0">
            {title && <h3 className="font-semibold text-[15px] tracking-tight" style={{ color: "var(--text-1)" }}>{title}</h3>}
            {sub && <p className="text-xs mt-1" style={{ color: "var(--text-2)" }}>{sub}</p>}
          </div>
          {right && <div className="shrink-0">{right}</div>}
        </div>
      )}
      {children}
    </section>
  );
}

/* Compat MetricCard — restyled, same props */
export function MetricCard({ label, value, hint, tone }: {
  label: string; value: string; hint?: string; tone?: "red" | "green" | "amber" | "slate";
}) {
  const tones: Record<string, string> = {
    red: "text-red-600 dark:text-red-400", green: "text-teal-600 dark:text-teal-300", amber: "text-amber-600 dark:text-amber-300", slate: "",
  };
  return (
    <div className="glass glass-hover rounded-2xl p-4">
      <div className="text-[11px] font-semibold uppercase tracking-[0.08em]" style={{ color: "var(--text-3)" }}>{label}</div>
      <div className={cn("text-2xl font-bold mt-1.5 tnum tracking-tight", tones[tone || "slate"])} style={tone === "slate" || !tone ? { color: "var(--text-1)" } : undefined}>{value}</div>
      {hint && <div className="text-xs mt-1" style={{ color: "var(--text-3)" }}>{hint}</div>}
    </div>
  );
}

/* ---------- StatCard (count-up + sparkline + delta) ---------- */
export function StatCard({ label, value, format, hint, delta, deltaTone, spark, icon, featured }: {
  label: string; value: number; format?: (n: number) => string;
  hint?: string; delta?: string; deltaTone?: "up" | "down" | "neutral";
  spark?: number[]; icon?: React.ReactNode; featured?: boolean;
}) {
  const animated = useCountUp(value);
  const fmt = format || ((n: number) => n.toLocaleString("en-IN", { maximumFractionDigits: 0 }));
  const pts = spark && spark.length > 1 ? spark : null;
  const sparkPath = pts ? (() => {
    const w = 96, h = 28, min = Math.min(...pts), max = Math.max(...pts);
    const rng = max - min || 1;
    return pts.map((v, i) => `${i === 0 ? "M" : "L"}${(i / (pts.length - 1)) * w},${h - 3 - ((v - min) / rng) * (h - 6)}`).join(" ");
  })() : null;
  return (
    <div className={cn("glass rounded-2xl p-4 relative overflow-hidden", featured && "gradient-ring")} data-tilt>
      {featured && <div className="absolute -top-16 -right-16 w-48 h-48 rounded-full pointer-events-none" style={{ background: "radial-gradient(circle, rgba(37,99,235,0.16), transparent 70%)" }} />}
      <div className="flex items-center justify-between gap-2">
        <div className="text-[11px] font-semibold uppercase tracking-[0.08em]" style={{ color: "var(--text-3)" }}>{label}</div>
        {icon && <div style={{ color: "var(--text-3)" }}>{icon}</div>}
      </div>
      <div className="text-[22px] leading-7 font-extrabold mt-1.5 tnum tracking-tight" style={{ color: "var(--text-1)" }}>{fmt(animated)}</div>
      <div className="flex items-center justify-between gap-2 mt-2">
        <div className="flex items-center gap-2 min-w-0">
          {delta && (
            <span className={cn("text-[11px] font-bold px-1.5 py-0.5 rounded-full tnum",
              deltaTone === "up" && "bg-teal-500/12 text-teal-700 dark:text-teal-300",
              deltaTone === "down" && "bg-red-500/12 text-red-600 dark:text-red-400",
              (!deltaTone || deltaTone === "neutral") && "border")}
              style={(!deltaTone || deltaTone === "neutral") ? { color: "var(--text-2)" } : undefined}>{delta}</span>
          )}
          {hint && <span className="text-[11px] truncate" style={{ color: "var(--text-3)" }}>{hint}</span>}
        </div>
        {sparkPath && (
          <svg width="96" height="28" className="shrink-0 opacity-90" aria-hidden>
            <defs><linearGradient id={`sg-${label.replace(/\W/g, "")}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.9" /><stop offset="100%" stopColor="#3B82F6" stopOpacity="0.1" />
            </linearGradient></defs>
            <path d={sparkPath} fill="none" stroke="#2563EB" strokeWidth="1.8" strokeLinecap="round" />
          </svg>
        )}
      </div>
    </div>
  );
}

/* ---------- Button ---------- */
type BtnVariant = "primary" | "secondary" | "ghost" | "danger";
export function Button({ variant, size, loading, className, children, ...rest }: {
  variant?: BtnVariant; size?: "sm" | "md" | "lg"; loading?: boolean;
  children: React.ReactNode; className?: string;
} & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const v: Record<BtnVariant, string> = {
    primary: "text-white border-transparent shadow-glow-sm hover:-translate-y-px hover:shadow-glow",
    secondary: "glass hover:border-[rgba(37,99,235,0.45)]",
    ghost: "border-transparent hover:bg-slate-500/10",
    danger: "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/30 hover:bg-red-500/20",
  };
  const s = { sm: "px-3 py-1.5 text-xs", md: "px-4 py-2 text-sm", lg: "px-5 py-2.5 text-sm" }[size || "md"];
  const vt = variant || "primary";
  const bg = vt === "primary"
    ? { backgroundImage: "linear-gradient(135deg,#2563EB,#3B82F6)" }
    : undefined;
  return (
    <button
      {...rest}
      disabled={loading || rest.disabled}
      style={{ color: vt === "primary" ? "#fff" : "var(--text-1)", borderWidth: 1, ...bg }}
      className={cn("inline-flex items-center justify-center gap-2 font-semibold rounded-full transition-all duration-200",
        "disabled:opacity-60 disabled:pointer-events-none focus-visible:outline-none", v[vt], s, className)}>
      {loading && <Loader2 size={15} className="animate-spin" />}
      {children}
    </button>
  );
}

/* ---------- Badge ---------- */
export function Badge({ tone, children, className }: {
  tone?: "success" | "warning" | "danger" | "info" | "neutral" | "brand";
  children: React.ReactNode; className?: string;
}) {
  const m: Record<string, string> = {
    success: "bg-teal-500/10 text-teal-700 dark:text-teal-300 border-teal-500/25",
    warning: "bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/25",
    danger: "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/25",
    info: "bg-blue-500/10 text-blue-700 dark:text-blue-300 border-blue-500/25",
    neutral: "border",
    brand: "text-white border-transparent",
  };
  const t = tone || "neutral";
  const neutralStyle = t === "neutral"
    ? { color: "var(--text-2)", background: "color-mix(in srgb, var(--text-2) 10%, transparent)" }
    : undefined;
  return (
    <span
      className={cn("inline-flex items-center text-[11px] font-bold px-2 py-0.5 rounded-full border", m[t], className)}
      style={t === "brand" ? { backgroundImage: "linear-gradient(135deg,#2563EB,#3B82F6)" } : neutralStyle}>
      {children}
    </span>
  );
}

/* 4-level risk scale: Very High #EF4444 · High #F97316 · Medium #F59E0B · Low #22C55E */
export function RiskBadge({ band }: { band: string }) {
  if (band === "Very High") return (
    <span className="inline-flex items-center text-[11px] font-bold px-2 py-0.5 rounded-full border bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/25">Very High</span>
  );
  if (band === "High") return (
    <span className="inline-flex items-center text-[11px] font-bold px-2 py-0.5 rounded-full border bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/25">High</span>
  );
  if (band === "Medium") return (
    <span className="inline-flex items-center text-[11px] font-bold px-2 py-0.5 rounded-full border bg-amber-500/10 text-amber-600 dark:text-amber-300 border-amber-500/25">Medium</span>
  );
  return (
    <span className="inline-flex items-center text-[11px] font-bold px-2 py-0.5 rounded-full border bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/25">Low</span>
  );
}

export function PrioBadge({ p }: { p: string }) {
  if (p === "Critical") return <Badge tone="danger">Critical</Badge>;
  if (p === "High Priority") return (
    <span className="inline-flex items-center text-[11px] font-bold px-2 py-0.5 rounded-full border bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/25">High Priority</span>
  );
  if (p === "Monitor") return <Badge tone="info">Monitor</Badge>;
  return <Badge tone="neutral">{p}</Badge>;
}

/* ---------- Tabs ---------- */
export function Tabs<T extends string>({ options, value, onChange }: {
  options: Array<{ v: T; label: string }>; value: T; onChange: (v: T) => void;
}) {
  return (
    <div className="glass rounded-full p-1 inline-flex gap-1" role="tablist">
      {options.map((o) => (
        <button key={o.v} role="tab" aria-selected={value === o.v} onClick={() => onChange(o.v)}
          className={cn("px-3.5 py-1.5 text-xs font-semibold rounded-full transition-all",
            value === o.v ? "text-white shadow-glow-sm" : "hover:bg-[#2563EB]/10")}
          style={value === o.v ? { backgroundImage: "linear-gradient(135deg,#2563EB,#3B82F6)" } : { color: "var(--text-2)" }}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

/* ---------- Table ---------- */
export function Table({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("overflow-x-auto rounded-xl border", className)} style={{ borderColor: "var(--border)" }}>
      <table className="w-full text-[13px]">{children}</table>
    </div>
  );
}
export function THead({ children }: { children: React.ReactNode }) {
  return <thead className="sticky top-0 z-10" style={{ background: "var(--elevated)" }}><tr className="text-left text-[11px] uppercase tracking-[0.07em]" style={{ color: "var(--text-3)" }}>{children}</tr></thead>;
}
export function TH({ children, right, className }: { children?: React.ReactNode; right?: boolean; className?: string }) {
  return <th className={cn("px-3 py-2.5 font-semibold whitespace-nowrap", right && "text-right", className)}>{children}</th>;
}
export function TD({ children, right, className, colSpan }: { children: React.ReactNode; right?: boolean; className?: string; colSpan?: number }) {
  return <td colSpan={colSpan} className={cn("px-3 py-2.5 border-t whitespace-nowrap", right && "text-right tnum", className)} style={{ borderColor: "var(--border)", color: "var(--text-1)" }}>{children}</td>;
}
export function TRow({ children, className }: { children: React.ReactNode; className?: string }) {
  return <tr className={cn("transition-colors hover:bg-[#2563EB]/[0.05]", className)}>{children}</tr>;
}

export function Pagination({ page, total, pageSize, onPage }: {
  page: number; total: number; pageSize: number; onPage: (p: number) => void;
}) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <div className="flex items-center justify-between mt-3 text-xs" style={{ color: "var(--text-2)" }}>
      <span className="tnum">Page {page} of {pages} · {total.toLocaleString("en-IN")} total</span>
      <div className="flex gap-2">
        <Button variant="secondary" size="sm" disabled={page <= 1} onClick={() => onPage(page - 1)}>Prev</Button>
        <Button variant="secondary" size="sm" disabled={page >= pages} onClick={() => onPage(page + 1)}>Next</Button>
      </div>
    </div>
  );
}

/* ---------- Modal / Drawer ---------- */
export function Modal({ open, onClose, title, children, wide }: {
  open: boolean; onClose: () => void; title?: string; children: React.ReactNode; wide?: boolean;
}) {
  useEffect(() => {
    if (!open) return;
    const fn = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", fn);
    return () => window.removeEventListener("keydown", fn);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className={cn("glass rounded-2xl p-6 relative w-full shadow-card animate-rise", wide ? "max-w-3xl" : "max-w-lg")}>
        {title && <h3 className="font-bold text-lg mb-4" style={{ color: "var(--text-1)" }}>{title}</h3>}
        {children}
      </div>
    </div>
  );
}

export function Drawer({ open, onClose, title, children }: {
  open: boolean; onClose: () => void; title?: string; children: React.ReactNode;
}) {
  useEffect(() => {
    if (!open) return;
    const fn = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", fn);
    return () => window.removeEventListener("keydown", fn);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50" role="dialog" aria-modal="true">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <aside className="absolute right-0 top-0 h-full w-full max-w-md glass border-l p-6 overflow-y-auto animate-rise" style={{ borderColor: "var(--border)" }}>
        {title && <h3 className="font-bold text-lg mb-4" style={{ color: "var(--text-1)" }}>{title}</h3>}
        {children}
      </aside>
    </div>
  );
}

/* ---------- Inputs ---------- */
export const inputCls = "w-full rounded-xl px-3.5 py-2.5 text-sm glass placeholder:text-slate-400 focus:border-[rgba(37,99,235,0.55)] focus:outline-none transition-colors";
export const btnPrimary = "inline-flex items-center justify-center gap-2 bg-[#2563EB] hover:bg-[#1D4ED8] text-white text-sm font-semibold px-4 py-2 rounded-full transition-all hover:-translate-y-px shadow-glow-sm";
export const btnGhost = "inline-flex items-center justify-center gap-2 text-sm font-semibold px-4 py-2 rounded-full glass transition-all hover:border-[rgba(37,99,235,0.45)]";

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={cn(inputCls, props.className)} style={{ color: "var(--text-1)", ...props.style }} />;
}
export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select {...props} className={cn(inputCls, "appearance-none cursor-pointer", props.className)}
      style={{ color: "var(--text-1)", background: "var(--elevated)", ...props.style }}>
      {props.children}
    </select>
  );
}
export function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-[11px] font-semibold uppercase tracking-[0.07em]" style={{ color: "var(--text-2)" }}>{label}</span>
      <div className="mt-1.5">{children}</div>
    </label>
  );
}

/* ---------- Toast ---------- */
type Toast = { id: number; msg: string; tone?: "success" | "error" | "info" };
const ToastCtx = createContext<(msg: string, tone?: Toast["tone"]) => void>(() => {});
export const useToast = () => useContext(ToastCtx);
export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]);
  const push = useCallback((msg: string, tone: Toast["tone"] = "info") => {
    const id = Date.now() + Math.random();
    setItems((p) => [...p.slice(-3), { id, msg, tone }]);
    setTimeout(() => setItems((p) => p.filter((t) => t.id !== id)), 3800);
  }, []);
  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div className="fixed bottom-5 right-5 z-[60] space-y-2 w-[320px]" aria-live="polite">
        {items.map((t) => (
          <div key={t.id} className="glass rounded-xl px-4 py-3 text-sm shadow-card animate-rise border-l-2"
            style={{
              color: "var(--text-1)",
              borderLeftColor: t.tone === "success" ? "#14B8A6" : t.tone === "error" ? "#EF4444" : "#2563EB",
            }}>{t.msg}</div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}

/* ---------- Skeleton / Empty / Loading / Err ---------- */
export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("skeleton rounded-lg", className || "h-4 w-full")} />;
}
export function SkeletonCard() {
  return <div className="glass rounded-2xl p-5 space-y-3"><Skeleton className="h-4 w-1/3" /><Skeleton className="h-8 w-2/3" /><Skeleton className="h-4 w-full" /></div>;
}
export function TableSkeleton({ rows = 6 }: { rows?: number }) {
  return <div className="space-y-2 py-2">{Array.from({ length: rows }).map((_, i) => <Skeleton key={i} className="h-9 w-full" />)}</div>;
}

export function EmptyState({ icon, title, hint, action }: {
  icon?: React.ReactNode; title: string; hint?: string; action?: React.ReactNode;
}) {
  return (
    <div className="py-12 text-center">
      {icon && <div className="mx-auto w-12 h-12 rounded-2xl glass flex items-center justify-center mb-3" style={{ color: "var(--text-2)" }}>{icon}</div>}
      <p className="font-semibold" style={{ color: "var(--text-1)" }}>{title}</p>
      {hint && <p className="text-sm mt-1" style={{ color: "var(--text-2)" }}>{hint}</p>}
      {action && <div className="mt-4 flex justify-center">{action}</div>}
    </div>
  );
}

export function Loading({ msg }: { msg?: string }) {
  return (
    <div className="py-14 grid gap-3">
      <div className="flex items-center justify-center gap-2 text-sm animate-pulse" style={{ color: "var(--text-2)" }}>
        <Loader2 size={16} className="animate-spin" /> {msg || "Loading…"}
      </div>
      <div className="grid md:grid-cols-3 gap-3"><SkeletonCard /><SkeletonCard /><SkeletonCard /></div>
    </div>
  );
}

export function Err({ msg, retry }: { msg: string; retry?: () => void }) {
  return (
    <div className="py-10 text-center">
      <p className="text-sm text-semantic-danger">{msg}</p>
      {retry && <Button variant="secondary" size="sm" className="mt-3" onClick={retry}>Retry</Button>}
    </div>
  );
}

/* ---------- Tooltip (CSS-only) ---------- */
export function Tooltip({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <span className="relative group inline-flex" tabIndex={0} aria-label={label}>
      {children}
      <span className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-2 whitespace-nowrap rounded-lg px-2.5 py-1.5 text-[11px] font-medium opacity-0 group-hover:opacity-100 group-focus-visible:opacity-100 transition-opacity z-30"
        style={{ background: "var(--tooltip-bg)", color: "var(--text-1)", border: "1px solid var(--border)" }}>{label}</span>
    </span>
  );
}

/* ---------- Avatar ---------- */
const AV = ["#2563EB,#3B82F6", "#3B82F6,#14B8A6", "#0B1A3A,#2563EB", "#F59E0B,#F97316", "#14B8A6,#3B82F6", "#6366F1,#3B82F6"];
export function Avatar({ name, size = 36, risk }: { name: string; size?: number; risk?: "Low" | "Medium" | "High" | "Very High" }) {
  const initials = name.split(/\s+/).map((w) => w[0]).slice(0, 2).join("").toUpperCase() || "?";
  const g = AV[(name.charCodeAt(0) || 0) % AV.length];
  const halo = risk === "Very High" ? "0 0 0 2px rgba(239,68,68,0.55), 0 0 16px rgba(239,68,68,0.45)"
    : risk === "High" ? "0 0 0 2px rgba(249,115,22,0.5), 0 0 16px rgba(249,115,22,0.45)"
    : risk === "Medium" ? "0 0 0 2px rgba(245,158,11,0.5), 0 0 14px rgba(245,158,11,0.4)"
    : risk === "Low" ? "0 0 0 2px rgba(34,197,94,0.45), 0 0 14px rgba(34,197,94,0.35)"
    : "0 0 14px rgba(37,99,235,0.35)";
  return (
    <span className="avatar-orb inline-flex shrink-0" title={name} style={{ width: size + 4, height: size + 4 }}>
      <span className="rounded-full w-full h-full flex items-center justify-center text-xs font-extrabold text-white"
        style={{ width: size, height: size, background: `linear-gradient(135deg, ${g})`, boxShadow: halo }}>
        {initials}
      </span>
    </span>
  );
}

/* ---------- PageHeader ---------- */
export function PageHeader({ eyebrow, title, desc, actions }: {
  eyebrow?: string; title: string; desc?: string; actions?: React.ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3 mb-5">
      <div className="min-w-0">
        {eyebrow && <div className="text-[11px] font-bold uppercase tracking-[0.14em] gradient-text mb-1">{eyebrow}</div>}
        <h1 className="page-title leading-tight" style={{ color: "var(--text-1)" }}>{title}</h1>
        {desc && <p className="text-[13px] mt-1.5 max-w-2xl" style={{ color: "var(--text-2)" }}>{desc}</p>}
      </div>
      {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
    </div>
  );
}

/* ---------- Charts ---------- */
export const chartColors = {
  brand: ["#2563EB", "#3B82F6", "#14B8A6"],
  risk: ["#22C55E", "#F59E0B", "#F97316", "#EF4444"],
  grid: "#EEF2F7",
  tick: "#94A3B8",
};
/** NOTE: in-chart <defs> via a wrapper component are dropped by recharts — use ChartGradients instead. */
/**
 * Document-wide gradient defs. Render once per page OUTSIDE recharts charts
 * (recharts drops custom wrapper components placed inside charts, which made
 * gradient fills silently transparent). Charts reference url(#rq-bar) etc.
 */
export function ChartGradients() {
  return (
    <svg width="0" height="0" className="absolute" aria-hidden focusable="false">
      <defs>
        <linearGradient id="rq-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#3B82F6" stopOpacity={0.45} />
          <stop offset="100%" stopColor="#3B82F6" stopOpacity={0.02} />
        </linearGradient>
        <linearGradient id="rq-bar" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#2563EB" /><stop offset="100%" stopColor="#3B82F6" />
        </linearGradient>
        <linearGradient id="rq-line" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#2563EB" /><stop offset="100%" stopColor="#14B8A6" />
        </linearGradient>
      </defs>
    </svg>
  );
}
export function ChartTooltip({ active, payload, label, formatter }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rq-tooltip">
      {label != null && label !== "" && <div className="font-bold mb-1">{String(label)}</div>}
      {payload.map((p: any, i: number) => (
        <div key={i} className="flex items-center gap-2 tnum">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color || p.payload?.fill || "#2563EB" }} />
          <span style={{ color: "var(--text-2)" }}>{p.name}:</span>
          <b>{formatter ? formatter(p.value, p) : p.value}</b>
        </div>
      ))}
    </div>
  );
}
