"use client";
import { useEffect, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

const RISKS = ["#34D399", "#34D399", "#FBBF24", "#FBBF24", "#FF4D6D", "#FF4D6D", "#FF4D6D"];

function Rig({ paused }: { paused: boolean }) {
  const group = useRef<THREE.Group>(null);
  const pointer = useRef({ x: 0, y: 0 });
  const reduced = useRef(false);

  useEffect(() => {
    try { reduced.current = window.matchMedia("(prefers-reduced-motion: reduce)").matches; } catch { reduced.current = true; }
    const fn = (e: PointerEvent) => {
      pointer.current = { x: (e.clientX / window.innerWidth - 0.5) * 0.6, y: (e.clientY / window.innerHeight - 0.5) * 0.4 };
    };
    window.addEventListener("pointermove", fn);
    return () => window.removeEventListener("pointermove", fn);
  }, []);

  useFrame((state, delta) => {
    const g = group.current;
    if (!g) return;
    const d = Math.min(delta, 0.05);
    if (!paused && !reduced.current) g.rotation.y += d * 0.28;
    g.rotation.x += ((pointer.current.y * 0.5 - g.rotation.x) * 0.04);
    g.rotation.z += ((pointer.current.x * 0.2 - g.rotation.z) * 0.04);
  });

  return (
    <group ref={group}>
      {/* maroon depth orb behind */}
      <mesh position={[0, 0, -1.6]}>
        <sphereGeometry args={[1.9, 32, 32]} />
        <meshBasicMaterial color="#3b0d24" transparent opacity={0.85} />
      </mesh>
      {/* central glossy pink sphere */}
      <mesh>
        <sphereGeometry args={[0.85, 48, 48]} />
        <meshStandardMaterial color="#EC2F8B" emissive="#C026D3" emissiveIntensity={0.55} roughness={0.25} metalness={0.35} />
      </mesh>
      <pointLight position={[3, 2, 4]} intensity={30} color="#FF4D6D" />
      <pointLight position={[-3, -1, 3]} intensity={18} color="#C026D3" />
      <ambientLight intensity={0.5} />
      {/* orbit rings */}
      {[1.55, 2.15].map((r, i) => (
        <mesh key={r} rotation={[Math.PI / 2.25, 0, i * 0.5]}>
          <torusGeometry args={[r, 0.008, 8, 96]} />
          <meshBasicMaterial color="#EC2F8B" transparent opacity={0.4} />
        </mesh>
      ))}
      {/* orbiting avatar spheres with risk halos */}
      {RISKS.map((c, i) => (
        <OrbitAvatar key={i} index={i} total={RISKS.length} color={c} paused={paused} />
      ))}
    </group>
  );
}

function OrbitAvatar({ index, total, color, paused }: { index: number; total: number; color: string; paused: boolean }) {
  const ref = useRef<THREE.Group>(null);
  const reduced = useRef(false);
  useEffect(() => {
    try { reduced.current = window.matchMedia("(prefers-reduced-motion: reduce)").matches; } catch { reduced.current = true; }
  }, []);
  const radius = index % 2 === 0 ? 1.55 : 2.15;
  const speed = (index % 2 === 0 ? 0.32 : 0.2) * (index % 3 === 0 ? -1 : 1);
  const phase = (index / total) * Math.PI * 2;
  const tilt = 0.5 + (index % 3) * 0.18;

  useFrame((state) => {
    const g = ref.current;
    if (!g) return;
    const t = paused || reduced.current ? phase * 10 : state.clock.elapsedTime * speed + phase * 4;
    g.position.set(Math.cos(t) * radius, Math.sin(t * 0.9) * radius * Math.sin(tilt) * 0.6, Math.sin(t) * radius * 0.55);
    const s = 1 + Math.sin(state.clock.elapsedTime * 1.4 + index) * 0.08;
    g.scale.setScalar(0.075 * s + 0.035);
  });

  return (
    <group ref={ref}>
      <mesh>
        <sphereGeometry args={[1, 20, 20]} />
        <meshStandardMaterial color="#4a4a52" emissive={color} emissiveIntensity={0.35} roughness={0.35} metalness={0.1} />
      </mesh>
      <mesh scale={1.5}>
        <sphereGeometry args={[1, 20, 20]} />
        <meshBasicMaterial color={color} transparent opacity={0.28} side={THREE.BackSide} />
      </mesh>
    </group>
  );
}

export default function OrbitScene() {
  const wrap = useRef<HTMLDivElement>(null);
  const visible = useRef(true);

  useEffect(() => {
    const onVis = () => { visible.current = !document.hidden; };
    document.addEventListener("visibilitychange", onVis);
    return () => document.removeEventListener("visibilitychange", onVis);
  }, []);

  return (
    <div ref={wrap} className="absolute inset-0">
      <Canvas dpr={[1, 2]} camera={{ position: [0, 0, 5.2], fov: 45 }} gl={{ antialias: true, alpha: true }}>
        <Rig paused={false} />
      </Canvas>
    </div>
  );
}
