"use client";
import { motion, useReducedMotion } from "framer-motion";
import React, { useRef, useState } from "react";

export function Reveal({ children, delay = 0, className }: {
  children: React.ReactNode; delay?: number; className?: string;
}) {
  const reduce = useReducedMotion();
  if (reduce) return <div className={className}>{children}</div>;
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.32, delay, ease: [0.22, 1, 0.36, 1] }}>
      {children}
    </motion.div>
  );
}

export function Stagger({ children, className }: { children: React.ReactNode; className?: string }) {
  const reduce = useReducedMotion();
  if (reduce) return <div className={className}>{children}</div>;
  return (
    <motion.div
      className={className}
      initial="hidden" animate="show"
      variants={{ hidden: {}, show: { transition: { staggerChildren: 0.06 } } }}>
      {children}
    </motion.div>
  );
}

export function StaggerItem({ children, className }: { children: React.ReactNode; className?: string }) {
  const reduce = useReducedMotion();
  if (reduce) return <div className={className}>{children}</div>;
  return (
    <motion.div
      className={className}
      variants={{ hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.22, 1, 0.36, 1] } } }}>
      {children}
    </motion.div>
  );
}

/** CSS 3D tilt + mouse-follow glow. Disabled on touch / reduced-motion. */
export function Tilt({ children, className, max = 7 }: {
  children: React.ReactNode; className?: string; max?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [style, setStyle] = useState<React.CSSProperties>({});
  const [glow, setGlow] = useState({ x: 50, y: 50 });

  function onMove(e: React.MouseEvent<HTMLDivElement>) {
    const el = ref.current;
    if (!el) return;
    try {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    } catch { return; }
    const r = el.getBoundingClientRect();
    const px = (e.clientX - r.left) / r.width;
    const py = (e.clientY - r.top) / r.height;
    setStyle({
      transform: `perspective(900px) rotateX(${((0.5 - py) * max).toFixed(2)}deg) rotateY(${((px - 0.5) * max).toFixed(2)}deg) translateY(-2px)`,
    });
    setGlow({ x: px * 100, y: py * 100 });
  }
  function reset() { setStyle({}); }

  return (
    <div ref={ref} onMouseMove={onMove} onMouseLeave={reset}
      className={`tilt transition-transform duration-200 ${className || ""}`} style={style}>
      <div className="tilt-inner relative">
        <div className="pointer-events-none absolute inset-0 rounded-2xl opacity-0 hover:opacity-100 transition-opacity"
          style={{ background: `radial-gradient(320px 200px at ${glow.x}% ${glow.y}%, rgba(236,47,139,0.16), transparent 70%)` }} />
        {children}
      </div>
    </div>
  );
}
