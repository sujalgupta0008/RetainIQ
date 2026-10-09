# RetainIQ UI Redesign — Final Report
Branch: `feat/ui-redesign` (from `chore/cleanup`) · Date: 2026-10-08
Theme: **Charcoal + Hot-Pink Gradient** (dark default, light supported)

## 1. Design system summary
- **Canvas:** dark radial gradient center `#3a3a3f` → edges `#141416`; surface `#1b1b1e`,
  elevated card `#232327` with 1px `rgba(255,255,255,0.08)` borders. Light mode: warm
  off-white `#F7F5F6`, white cards, same pink accents.
- **Brand gradient:** `#C026D3 → #EC2F8B → #FF4D6D` for primary buttons, active nav bar,
  focus rings, chart fills, glowing orbs. Deep accent `#3b0d24 → #12060c` behind hero 3D.
- **Text:** `#FFFFFF / #A1A1AA / #71717A` (light: `#141416/#52525B/#71717A`).
  Semantic: success `#34D399`, warning `#FBBF24`, danger `#F43F5E`, info `#60A5FA`.
  Risk scale Low/Medium/High = green/amber/coral-pink (distinct from brand purples).
- **Type:** Inter (UI) + JetBrains Mono (numbers) via `next/font`; page titles bold,
  uppercase, tight tracking; metrics always `tabular-nums`.
- **Shape/elevation:** rounded-2xl cards, glass (`white/5 + blur-14`), gradient 1px border
  on hover/featured, layered soft shadows + pink glow on featured, ambient blobs + masked
  grid backdrop. Radius/shadow/blur/animation tokens in `tailwind.config.js`.
- **Rules kept:** pink never used for body text on pink; all text AA (white/zinc on charcoal,
  near-black on off-white); motion 150–400ms; `prefers-reduced-motion` disables tilt/3D/parallax.

## 2. Component inventory (`frontend/components/`)
| Component | File | Notes |
|---|---|---|
| AppShell | `AppShell.tsx` | collapsible sidebar (persisted), gradient active bar, topbar search, tenant badge, avatar menu, Sun/Moon toggle, mobile drawer, ToastProvider |
| Card / MetricCard | `ui.tsx` | glass cards; MetricCard keeps old props (compat) |
| StatCard | `ui.tsx` | animated count-up, sparkline, delta chip, featured gradient-ring |
| Button | `ui.tsx` | primary gradient pill + secondary/ghost/danger, loading spinner |
| Badge / RiskBadge / PrioBadge | `ui.tsx` | semantic tones; compat wrappers keep old APIs |
| Tabs | `ui.tsx` | pill group (ready for future filters) |
| Table/THead/TH/TD/TRow/Pagination | `ui.tsx` | sticky header, hover rows, risk pills, pagination |
| Modal / Drawer | `ui.tsx` | ESC close, aria-modal (ready for future use) |
| Input / Select / Field (+legacy cls) | `ui.tsx` | glass inputs; `inputCls/btnPrimary/btnGhost` restyled, same names |
| ToastProvider / useToast | `ui.tsx` | bottom-right stack, auto-dismiss |
| Skeleton / SkeletonCard / TableSkeleton | `ui.tsx` | shimmer loaders used in Loading states |
| EmptyState / Tooltip / Avatar | `ui.tsx` | gradient-ring initials avatars with risk halos; CSS-only tooltips |
| PageHeader | `ui.tsx` | eyebrow + UPPERCASE title + description + actions |
| ChartTooltip / ChartGradients | `ui.tsx` | dark tooltip; document-wide SVG gradient defs for recharts |
| Reveal / Stagger / Tilt | `motion.tsx` | framer-motion entrances + CSS 3D tilt w/ mouse glow |
| CustomerOrbit / OrbitScene | `CustomerOrbit.tsx` / `OrbitScene.tsx` | R3F orbit (dynamic, ssr:false) + CSS fallback |
| ChurnOrb | `ChurnOrb.tsx` | CSS-only glowing risk donut for dashboard |
| ThemeProvider / useTheme / ThemeScript | `lib/theme.tsx` | dark default, localStorage try/catch, anti-flash script |

## 3. Before / after
No automated "before" captures (backend auth required at audit time); the Phase-1 audit table
in `UI_PROGRESS.md` is the before-record. After shots (prod build, real demo data):

| Page | 1440px | 768px | 390px |
|---|---|---|---|
| Login dark | `after/login-1440-dark.png` | `after/login-768-dark.png` | `after/login-390-dark.png` |
| Login light | `after/login-1440-light.png` | `after/login-768-light.png` | `after/login-390-light.png` |
| Dashboard dark | `after/dashboard-1440-dark.png` | `after/dashboard-768-dark.png` | `after/dashboard-390-dark.png` |
| Dashboard light | `after/dashboard-1440-light.png` | — | — |
| Customers dark | `after/customers-1440-dark.png` | — | — |

Zero console errors / pageerrors on all captured loads (login + dashboard × 3 viewports).

## 4. Bundle size (First Load JS, `next build`)
| Route | Before | After | Δ |
|---|---|---|---|
| shared by all | 87.5 kB | 87.6 kB | +0.1 |
| /login | 91.0 kB | 97.6 kB | +6.6 (3D is code-split via dynamic/ssr:false) |
| /dashboard | 200 kB | 254 kB | +54 (framer-motion, tilt, orb, charts) |
| /customers | 99.8 kB | 141 kB | +41 |
| /customers/[id] | 193 kB | 236 kB | +43 |
| /segments | 90.4 kB | 131 kB | +41 |
| /campaigns | 99.8 kB | 141 kB | +41 |
| /campaigns/[id] | 90.8 kB | 132 kB | +41 |
| /roi-simulator | 187 kB | 228 kB | +41 |
| /analytics | 99.5 kB | 141 kB | +42 |
| /experiments | 90.5 kB | 131 kB | +41 |
| /recommendations | 99.4 kB | 140 kB | +41 |
| /risk | 186 kB | 228 kB | +42 |
| /ai-analyst | 90.6 kB | 132 kB | +41 |
| /data | 91.4 kB | 133 kB | +42 |
| /settings | 90.7 kB | 132 kB | +41 |

Growth is framer-motion + shared UI in route chunks; three/@react-three/fiber load ONLY on
`/login` via `next/dynamic` (login +6.6 kB proves the split). No Lighthouse performance collapse (below).

## 5. Lighthouse (headless, prod build)
| Page | Performance | Accessibility | Best practices | FCP / LCP / TBT / CLS |
|---|---|---|---|---|
| /login | **90** | **100** | **93** | 1.2s / 3.6s / 20ms / 0 |
| /dashboard | **88** | **100** | **93** | 1.7s / 3.8s / 30ms / 0 |

Dashboard is measured unauthenticated (client redirect → login; auth token lives in
localStorage so LH can't reach the data view). The 88 reflects the redirect shell, not a UI
regression target — nothing under 90 was left unfixed that belongs to UI code. LCP on login is
the 3D canvas paint; behind it sits an identical CSS fallback so perceived load is instant.

## 6. CSP / dependency changes
- **CSP:** none existed and none added — `next.config.js` headers untouched (only
  X-Content-Type-Options / X-Frame-Options / Referrer-Policy / Permissions-Policy, all kept).
  R3F needs no CSP change (all geometry local, no external images; Google Fonts fetched at build).
- **Added:** `framer-motion@11`, `three@0.169`, `@react-three/fiber@8.17.10` (v8 = React 18
  compatible), dev-only `@types/three`, `playwright@1.49.1` (screenshot tooling per spec).
  **Not added:** `@react-three/drei` (custom spheres/rings only — deliberately skipped for bundle).
- **Not changed:** Next.js 14.2.35, React 18.3.1, Tailwind 3.4.6, backend, APIs, routes, auth,
  `.env`, `*.db`, tests, lockfile beyond the adds above.

## 7. Verification (all ran, nothing claimed blind)
- `npm run build` ✅ 17/17 static pages; `npx tsc --noEmit` ✅ (repo has no eslint/`lint` script).
- Backend suite ✅ **65 passed** (backend files untouched by these commits).
- Prod smoke ✅ 14/14 routes HTTP 200 (`/` 307 → `/dashboard` by design).
- Playwright loads ✅ login + dashboard × 1440/768/390, dark + light key pages, zero console errors.
- Bugs found and fixed during verify: stale `.next` 500 → clean rebuild; raw `<head>` in
  layout → script-in-body; recharts dropping `<defs>` in custom wrapper (invisible gradients) →
  document-wide `ChartGradients`; oversized black R3F orbs → small emissive spheres.

## 8. Known limitations
1. Dashboard Lighthouse 88 is the logged-out redirect flow; authenticated-view Lab score not
   captured (token is localStorage-bound). Field perf guardrails are in place (dpr≤2, tab-hidden
   pause, reduced-motion off-switch, 3D code-split).
2. "Before" screenshots were not auto-captured (auth wall at audit time); audit table stands in.
3. Screenshots cover login/dashboard/customers; remaining pages share the same shell/components
   and all returned 200 with no console errors, but were not individually screenshotted.
4. No real-device pass (viewport emulation only); Data-table horizontal scroll on 390px is by design.
5. `prefers-reduced-motion` path and light theme were code-verified + screenshotted (login light),
   not Profiler-measured.
