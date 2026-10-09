"use client";
import "./globals.css";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, logout } from "@/lib/api";
import {
  LayoutDashboard, Users, ShieldAlert, PieChart as PieIcon, Star, Calculator,
  Megaphone, FlaskConical, BarChart3, Bot, Database, Settings, LogOut, Landmark,
} from "lucide-react";

const NAV = [
  { href: "/dashboard", label: "Command Center", icon: LayoutDashboard },
  { href: "/customers", label: "Customers", icon: Users },
  { href: "/risk", label: "Risk & Model", icon: ShieldAlert },
  { href: "/segments", label: "Segments", icon: PieIcon },
  { href: "/recommendations", label: "Next Best Actions", icon: Star },
  { href: "/roi-simulator", label: "ROI Simulator", icon: Calculator },
  { href: "/campaigns", label: "Campaigns", icon: Megaphone },
  { href: "/experiments", label: "Experiments", icon: FlaskConical },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/ai-analyst", label: "AI Analyst", icon: Bot },
  { href: "/data", label: "Data", icon: Database },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  const [tenant, setTenant] = useState("");
  const [email, setEmail] = useState("");
  const isLogin = path === "/login";

  useEffect(() => {
    if (isLogin) return;
    if (!localStorage.getItem("retainiq_token")) { router.replace("/login"); return; }
    api("/api/auth/me").then((m) => { setTenant(m.tenant); setEmail(m.email); }).catch(() => {});
  }, [isLogin, path]);

  if (isLogin) {
    return (<html lang="en"><body className="bg-slate-100">{children}</body></html>);
  }
  return (
    <html lang="en">
      <body>
        <div className="flex min-h-screen">
          <aside className="w-60 shrink-0 bg-slate-900 text-slate-200 flex flex-col">
            <div className="px-5 py-5 flex items-center gap-2 border-b border-slate-800">
              <Landmark size={22} className="text-indigo-400" />
              <div>
                <div className="font-bold text-white leading-none">RetainIQ</div>
                <div className="text-[11px] text-slate-400 mt-1">Retention ROI Intelligence</div>
              </div>
            </div>
            <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
              {NAV.map((n) => {
                const active = path === n.href || (n.href !== "/dashboard" && path.startsWith(n.href));
                const Icon = n.icon;
                return (
                  <Link key={n.href} href={n.href}
                    className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm ${active ? "bg-indigo-600 text-white font-medium" : "hover:bg-slate-800 text-slate-300"}`}>
                    <Icon size={16} /> {n.label}
                  </Link>
                );
              })}
            </nav>
            <div className="px-4 py-3 border-t border-slate-800 text-xs">
              <div className="font-medium text-white truncate">{tenant || "…"}</div>
              <div className="text-slate-400 truncate">{email}</div>
              <button onClick={logout} className="mt-2 flex items-center gap-1.5 text-slate-300 hover:text-white">
                <LogOut size={14} /> Sign out
              </button>
            </div>
          </aside>
          <main className="flex-1 min-w-0 p-6 max-w-[1400px] mx-auto w-full">{children}</main>
        </div>
      </body>
    </html>
  );
}
