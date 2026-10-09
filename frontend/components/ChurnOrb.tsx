"use client";

/** Featured glowing churn-risk orb (CSS/SVG only — no WebGL cost on dashboard). */
export default function ChurnOrb({ highPct, total }: { highPct: number; total: number }) {
  const pct = Math.max(0, Math.min(100, highPct));
  const ring = 2 * Math.PI * 54;
  const off = ring * (1 - pct / 100);
  return (
    <div className="relative flex items-center gap-5">
      <div className="relative w-32 h-32 shrink-0">
        <div className="absolute inset-0 rounded-full animate-pulse-glow"
          style={{ background: "radial-gradient(circle, rgba(236,47,139,0.35), transparent 70%)" }} />
        <svg viewBox="0 0 128 128" className="relative w-full h-full -rotate-90">
          <circle cx="64" cy="64" r="54" fill="none" strokeWidth="10" stroke="rgba(255,255,255,0.08)" />
          <circle cx="64" cy="64" r="54" fill="none" strokeWidth="10" strokeLinecap="round"
            stroke="url(#orbGrad)" strokeDasharray={ring} strokeDashoffset={off}
            style={{ filter: "drop-shadow(0 0 10px rgba(236,47,139,0.7))", transition: "stroke-dashoffset 0.6s ease" }} />
          <defs>
            <linearGradient id="orbGrad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#C026D3" /><stop offset="55%" stopColor="#EC2F8B" /><stop offset="100%" stopColor="#FF4D6D" />
            </linearGradient>
          </defs>
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-extrabold tnum" style={{ color: "var(--text-1)" }}>{pct.toFixed(1)}%</span>
          <span className="text-[10px] font-bold uppercase tracking-[0.12em]" style={{ color: "var(--text-3)" }}>high risk</span>
        </div>
      </div>
      <div className="min-w-0">
        <div className="text-[11px] font-bold uppercase tracking-[0.12em] gradient-text">Churn Risk Orb</div>
        <p className="text-sm mt-1.5 leading-relaxed" style={{ color: "var(--text-2)" }}>
          <b className="tnum" style={{ color: "var(--text-1)" }}>{total.toLocaleString("en-IN")}</b> customers scored.
          High-risk share glows pink — act before it spreads.
        </p>
      </div>
    </div>
  );
}
