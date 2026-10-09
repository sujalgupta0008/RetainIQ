"use client";
import dynamic from "next/dynamic";

const OrbitScene = dynamic(() => import("@/components/OrbitScene"), { ssr: false });

const ORBITERS = [
  { x: "12%", y: "22%", c: "#34D399", d: "0s" },
  { x: "82%", y: "18%", c: "#FF4D6D", d: "1.2s" },
  { x: "20%", y: "72%", c: "#FBBF24", d: "0.6s" },
  { x: "74%", y: "70%", c: "#34D399", d: "1.8s" },
  { x: "88%", y: "46%", c: "#FBBF24", d: "2.4s" },
  { x: "8%", y: "48%", c: "#FF4D6D", d: "3s" },
];

/** Glowing customer-orbit hero: R3F canvas + CSS/SVG fallback underneath. */
export default function CustomerOrbit() {
  return (
    <div className="relative w-full h-full min-h-[380px] overflow-hidden" aria-hidden>
      {/* depth spotlight */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="w-[420px] h-[420px] rounded-full animate-pulse-glow"
          style={{ background: "radial-gradient(circle, #3b0d24 0%, #12060c 62%, transparent 72%)" }} />
      </div>
      {/* CSS fallback orbit (visible during SSR + reduced-motion + if WebGL fails) */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="relative w-[300px] h-[300px]">
          <div className="absolute inset-0 rounded-full"
            style={{ background: "radial-gradient(circle at 35% 30%, #FF4D6D, #EC2F8B 45%, #C026D3 75%)", boxShadow: "0 0 80px rgba(236,47,139,0.55), inset -18px -24px 60px rgba(0,0,0,0.45)" }} />
          <div className="absolute -inset-10 rounded-full border border-[rgba(236,47,139,0.3)] animate-float" />
          <div className="absolute -inset-20 rounded-full border border-[rgba(236,47,139,0.18)]" />
        </div>
      </div>
      {ORBITERS.map((o, i) => (
        <span key={i}
          className="absolute w-9 h-9 rounded-full flex items-center justify-center text-[10px] font-extrabold text-white animate-float"
          style={{
            left: o.x, top: o.y, animationDelay: o.d,
            background: "linear-gradient(135deg,#2a2a2e,#1b1b1e)",
            boxShadow: `0 0 0 2px ${o.c}66, 0 0 18px ${o.c}88`,
            border: "1px solid rgba(255,255,255,0.14)",
          }}>
          {["AR", "PS", "KM", "JT", "NE", "RS"][i]}
        </span>
      ))}
      {/* interactive 3D overlay */}
      <OrbitScene />
    </div>
  );
}
