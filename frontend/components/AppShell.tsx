"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { api, logout } from "@/lib/api";
import { useTheme } from "@/lib/theme";
import { Avatar, ToastProvider, Tooltip } from "@/components/ui";
import {
  LayoutDashboard, Users, ShieldAlert, PieChart as PieIcon, Star, Calculator,
  Megaphone, FlaskConical, BarChart3, Bot, Database, Settings, LogOut,
  ChevronsLeft, ChevronsRight, Search, Sun, Moon, Menu, X, Zap,
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

function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  const { theme, toggle } = useTheme();
  const [tenant, setTenant] = useState("");
  const [email, setEmail] = useState("");
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const isLogin = path === "/login";

  useEffect(() => {
    try {
      setCollapsed(localStorage.getItem("retainiq_nav") === "1");
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    if (isLogin) return;
    if (!localStorage.getItem("retainiq_token")) { router.replace("/login"); return; }
    api("/api/auth/me").then((m) => { setTenant(m.tenant); setEmail(m.email); }).catch(() => {});
  }, [isLogin, path, router]);

  useEffect(() => { setMobileOpen(false); }, [path]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return NAV;
    return NAV.filter((n) => n.label.toLowerCase().includes(q));
  }, [query]);

  if (isLogin) return <>{children}</>;

  const toggleCollapse = () => {
    setCollapsed((c) => {
      try { localStorage.setItem("retainiq_nav", c ? "0" : "1"); } catch { /* ignore */ }
      return !c;
    });
  };

  const side = (mobile: boolean) => (
    <div className="flex flex-col h-full">
      <Link href="/dashboard" className="flex items-center gap-2.5 px-4 py-5">
        <span className="w-9 h-9 rounded-xl flex items-center justify-center text-white shrink-0 shadow-glow-sm"
          style={{ backgroundImage: "linear-gradient(135deg,#C026D3,#EC2F8B 50%,#FF4D6D)" }}>
          <Zap size={18} strokeWidth={2.5} />
        </span>
        {(!collapsed || mobile) && (
          <span className="min-w-0">
            <span className="block font-extrabold tracking-tight leading-none" style={{ color: "var(--text-1)" }}>RetainIQ</span>
            <span className="block text-[10px] font-medium uppercase tracking-[0.12em] mt-1" style={{ color: "var(--text-3)" }}>Retention ROI</span>
          </span>
        )}
      </Link>
      <nav className="flex-1 overflow-y-auto px-2.5 pb-3 space-y-0.5" aria-label="Primary">
        {filtered.map((n) => {
          const active = path === n.href || (n.href !== "/dashboard" && path.startsWith(n.href));
          const Icon = n.icon;
          const link = (
            <Link key={n.href} href={n.href} aria-current={active ? "page" : undefined}
              className="relative flex items-center gap-2.5 px-3 py-2 rounded-xl text-[13px] font-medium transition-all duration-200 group">
              {active && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 rounded-full"
                  style={{ backgroundImage: "linear-gradient(180deg,#C026D3,#FF4D6D)", boxShadow: "0 0 12px rgba(236,47,139,0.7)" }} />
              )}
              <span className="absolute inset-0 rounded-xl transition-opacity"
                style={{
                  opacity: active ? 1 : 0,
                  background: "linear-gradient(135deg, rgba(192,38,211,0.22), rgba(236,47,139,0.14))",
                  border: active ? "1px solid rgba(236,47,139,0.3)" : "1px solid transparent",
                }} />
              <Icon size={17} className="relative shrink-0" style={{ color: active ? "#fff" : "var(--text-3)" }} />
              {(!collapsed || mobile) && (
                <span className="relative truncate" style={{ color: active ? "#fff" : "var(--text-2)" }}>{n.label}</span>
              )}
            </Link>
          );
          return collapsed && !mobile ? <Tooltip key={n.href} label={n.label}>{link}</Tooltip> : link;
        })}
        {filtered.length === 0 && (
          <p className="text-xs px-3 py-4" style={{ color: "var(--text-3)" }}>No matches for “{query}”.</p>
        )}
      </nav>
      <div className="p-3 mt-auto">
        <div className="glass rounded-2xl p-3">
          <div className="flex items-center gap-2.5 min-w-0">
            <Avatar name={tenant || email || "R"} size={30} />
            {(!collapsed || mobile) && (
              <div className="min-w-0 flex-1">
                <div className="text-xs font-bold truncate" style={{ color: "var(--text-1)" }}>{tenant || "…"}</div>
                <div className="text-[11px] truncate" style={{ color: "var(--text-3)" }}>{email}</div>
              </div>
            )}
          </div>
          {(!collapsed || mobile) && (
            <button onClick={logout} className="mt-2.5 w-full flex items-center justify-center gap-1.5 text-xs font-semibold rounded-full py-1.5 transition-colors hover:bg-white/5"
              style={{ color: "var(--text-2)" }}>
              <LogOut size={13} /> Sign out
            </button>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex min-h-screen">
      {/* desktop sidebar */}
      <aside className={`hidden lg:flex shrink-0 flex-col glass border-r transition-all duration-300 ${collapsed ? "w-[76px]" : "w-60"}`}
        style={{ borderColor: "var(--border)" }}>
        {side(false)}
        <button onClick={toggleCollapse} aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="mx-auto mb-3 w-8 h-8 rounded-full glass flex items-center justify-center hover:border-[rgba(236,47,139,0.4)] transition-colors"
          style={{ color: "var(--text-2)" }}>
          {collapsed ? <ChevronsRight size={15} /> : <ChevronsLeft size={15} />}
        </button>
      </aside>

      {/* mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
          <aside className="absolute left-0 top-0 h-full w-[280px] glass border-r" style={{ borderColor: "var(--border)" }}>
            <button onClick={() => setMobileOpen(false)} aria-label="Close menu" className="absolute top-4 right-3 p-1.5 rounded-lg hover:bg-white/5" style={{ color: "var(--text-2)" }}>
              <X size={17} />
            </button>
            {side(true)}
          </aside>
        </div>
      )}

      <div className="flex-1 min-w-0 flex flex-col">
        {/* top bar */}
        <header className="sticky top-0 z-30 glass border-b" style={{ borderColor: "var(--border)" }}>
          <div className="flex items-center gap-2.5 px-4 md:px-6 py-3 max-w-[1400px] mx-auto w-full">
            <button className="lg:hidden p-2 -ml-2 rounded-lg hover:bg-white/5" onClick={() => setMobileOpen(true)} aria-label="Open menu" style={{ color: "var(--text-2)" }}>
              <Menu size={18} />
            </button>
            <div className="relative flex-1 max-w-md">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: "var(--text-3)" }} />
              <input
                value={query} onChange={(e) => setQuery(e.target.value)}
                placeholder="Search pages…  ( try “risk” )"
                aria-label="Search pages"
                className="w-full glass rounded-full pl-9 pr-4 py-2 text-[13px] placeholder:text-zinc-500 focus:border-[rgba(236,47,139,0.5)] focus:outline-none"
                style={{ color: "var(--text-1)" }}
              />
            </div>
            <div className="ml-auto flex items-center gap-2">
              <span className="hidden sm:inline-flex items-center gap-1.5 text-[11px] font-bold px-2.5 py-1 rounded-full text-white"
                style={{ backgroundImage: "linear-gradient(135deg,#C026D3,#EC2F8B,#FF4D6D)" }}>
                {tenant || "Workspace"}
              </span>
              <button onClick={toggle} aria-label="Toggle theme" className="w-9 h-9 rounded-full glass flex items-center justify-center hover:border-[rgba(236,47,139,0.4)] transition-colors" style={{ color: "var(--text-2)" }}>
                {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
              </button>
              <div className="relative">
                <button onClick={() => setMenuOpen((o) => !o)} aria-haspopup="menu" aria-expanded={menuOpen} aria-label="User menu">
                  <Avatar name={tenant || email || "R"} size={32} />
                </button>
                {menuOpen && (
                  <>
                    <div className="fixed inset-0 z-40" onClick={() => setMenuOpen(false)} />
                    <div className="absolute right-0 mt-2 w-56 glass rounded-2xl p-2 z-50 shadow-card" role="menu">
                      <div className="px-3 py-2 border-b mb-1" style={{ borderColor: "var(--border)" }}>
                        <div className="text-xs font-bold truncate" style={{ color: "var(--text-1)" }}>{tenant}</div>
                        <div className="text-[11px] truncate" style={{ color: "var(--text-3)" }}>{email}</div>
                      </div>
                      <Link href="/settings" onClick={() => setMenuOpen(false)} className="flex items-center gap-2 px-3 py-2 rounded-xl text-[13px] hover:bg-white/5" style={{ color: "var(--text-2)" }}>
                        <Settings size={14} /> Workspace settings
                      </Link>
                      <button onClick={logout} className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-[13px] hover:bg-white/5" style={{ color: "var(--text-2)" }}>
                        <LogOut size={14} /> Sign out
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </header>
        <main className="flex-1 min-w-0 px-4 md:px-6 py-6 max-w-[1400px] mx-auto w-full">{children}</main>
      </div>
    </div>
  );
}

export default function AppShell({ children }: { children: React.ReactNode }) {
  return <ToastProvider><Shell>{children}</Shell></ToastProvider>;
}
