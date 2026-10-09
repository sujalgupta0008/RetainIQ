"use client";
import { ShieldCheck, FileBarChart, Users } from "lucide-react";

/**
 * Tilted 3D "floating dashboard" — pure CSS/SVG (no WebGL, no images).
 * Respects prefers-reduced-motion via the global animation guard.
 */
export default function FloatingDash() {
  return (
    <div className="relative w-full max-w-[520px] mx-auto" style={{ perspective: "1100px" }} aria-hidden>
      {/* isometric platform glow */}
      <div className="absolute left-1/2 -translate-x-1/2 -bottom-8 w-[78%] h-16 rounded-[100%]"
        style={{ background: "radial-gradient(ellipse, rgba(37,99,235,0.28), transparent 70%)" }} />

      {/* main tilted board */}
      <div className="relative rounded-3xl bg-white border border-[#E6ECF5] p-5 shadow-card"
        style={{
          transform: "rotateY(-13deg) rotateX(9deg)",
          transformStyle: "preserve-3d",
          boxShadow: "0 30px 60px -20px rgba(37,99,235,0.3), 0 2px 6px rgba(11,26,58,0.08)",
        }}>
        <div className="flex items-center gap-2 mb-4">
          <span className="w-7 h-7 rounded-lg flex items-center justify-center text-white text-xs font-extrabold"
            style={{ backgroundImage: "linear-gradient(135deg,#2563EB,#3B82F6)" }}>R</span>
          <div>
            <div className="h-2 w-24 rounded bg-slate-200" />
            <div className="h-1.5 w-16 rounded bg-slate-100 mt-1" />
          </div>
          <span className="ml-auto text-[10px] font-bold px-2 py-0.5 rounded-full bg-teal-500/10 text-teal-700">● Live</span>
        </div>
        <div className="grid grid-cols-3 gap-2.5 mb-4">
          {[
            ["7,443", "Customers", "#2563EB"],
            ["31.7%", "High risk", "#F97316"],
            ["₹21.5L", "Protected", "#14B8A6"],
          ].map(([v, l, c]) => (
            <div key={l} className="rounded-2xl border border-[#E6ECF5] bg-[#F8FAFF] p-2.5" style={{ transform: "translateZ(30px)" }}>
              <div className="text-[15px] font-extrabold tnum" style={{ color: c }}>{v}</div>
              <div className="text-[10px] font-medium text-slate-500">{l}</div>
            </div>
          ))}
        </div>
        <div className="rounded-2xl border border-[#E6ECF5] bg-white p-3" style={{ transform: "translateZ(55px)" }}>
          <div className="h-2 w-28 rounded bg-slate-200 mb-2" />
          <svg viewBox="0 0 300 90" className="w-full h-[86px]">
            <defs>
              <linearGradient id="fd-area" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.45" />
                <stop offset="100%" stopColor="#3B82F6" stopOpacity="0.02" />
              </linearGradient>
            </defs>
            {[18, 38, 58, 78].map((y) => (
              <line key={y} x1="0" y1={y} x2="300" y2={y} stroke="#EEF2F7" strokeWidth="1" />
            ))}
            <path d="M0,70 C30,66 45,58 70,60 C95,62 110,40 140,42 C170,44 185,55 210,48 C235,41 260,22 300,18 L300,90 L0,90 Z" fill="url(#fd-area)" />
            <path d="M0,70 C30,66 45,58 70,60 C95,62 110,40 140,42 C170,44 185,55 210,48 C235,41 260,22 300,18" fill="none" stroke="#2563EB" strokeWidth="2.5" strokeLinecap="round" />
            <path d="M0,78 C40,76 80,70 120,72 C170,74 220,60 300,55" fill="none" stroke="#14B8A6" strokeWidth="2" strokeDasharray="5 4" strokeLinecap="round" />
          </svg>
        </div>
        <div className="mt-3 space-y-1.5">
          {[["Aarav Sharma", "Call now", "#2563EB"], ["Priya Nair", "Email offer", "#3B82F6"]].map(([n, a]) => (
            <div key={n} className="flex items-center gap-2 rounded-xl border border-[#E6ECF5] bg-white px-2.5 py-1.5">
              <span className="w-6 h-6 rounded-full text-[8px] font-extrabold text-white flex items-center justify-center"
                style={{ backgroundImage: "linear-gradient(135deg,#2563EB,#3B82F6)" }}>{n.split(" ").map((w: string) => w[0]).join("")}</span>
              <span className="text-[11px] font-bold text-navy">{n}</span>
              <span className="ml-auto text-[10px] font-bold text-[#2563EB]">{a} →</span>
            </div>
          ))}
        </div>
      </div>

      {/* floating glass cards */}
      <div className="absolute -top-2 right-2 rounded-2xl bg-white/85 border border-[#E6ECF5] px-3.5 py-2.5 flex items-center gap-2.5 animate-float shadow-card"
        style={{ backdropFilter: "blur(10px)", transform: "translateZ(90px)" }}>
        <span className="w-8 h-8 rounded-xl flex items-center justify-center text-white" style={{ backgroundImage: "linear-gradient(135deg,#2563EB,#3B82F6)" }}>
          <ShieldCheck size={16} />
        </span>
        <span>
          <span className="block text-[11px] font-extrabold text-navy">Protected</span>
          <span className="block text-[10px] text-slate-500">32 saved today</span>
        </span>
      </div>
      <div className="absolute top-[38%] left-0 rounded-2xl bg-white/85 border border-[#E6ECF5] px-3.5 py-2.5 flex items-center gap-2.5 animate-float shadow-card"
        style={{ backdropFilter: "blur(10px)", animationDelay: "1.4s" }}>
        <span className="w-8 h-8 rounded-xl flex items-center justify-center text-white" style={{ backgroundImage: "linear-gradient(135deg,#14B8A6,#3B82F6)" }}>
          <FileBarChart size={16} />
        </span>
        <span>
          <span className="block text-[11px] font-extrabold text-navy">ROI +2,220%</span>
          <span className="block text-[10px] text-slate-500">this quarter</span>
        </span>
      </div>
      <div className="absolute bottom-8 right-2 rounded-2xl bg-white/85 border border-[#E6ECF5] px-3.5 py-2.5 flex items-center gap-2.5 animate-float shadow-card"
        style={{ backdropFilter: "blur(10px)", animationDelay: "2.6s" }}>
        <span className="w-8 h-8 rounded-xl flex items-center justify-center text-white" style={{ backgroundImage: "linear-gradient(135deg,#0B1A3A,#2563EB)" }}>
          <Users size={16} />
        </span>
        <span>
          <span className="block text-[11px] font-extrabold text-navy">2,358 at risk</span>
          <span className="block text-[10px] text-slate-500">act this week</span>
        </span>
      </div>
    </div>
  );
}
