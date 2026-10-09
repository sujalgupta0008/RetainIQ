# RetainIQ UI Redesign — Progress Tracker (COMPLETE)
Branch: `feat/ui-redesign` | Stack: Next.js 14 App Router + Tailwind 3 + recharts + lucide-react

## Phase 1 — Audit (DONE)
See table below. `docs/screenshots/before/` holds a README (no automated befores — backend auth
was required; the audit table is the source of truth).

| Route | Purpose | APIs | Key UI |
|---|---|---|---|
| `/` | redirect → /dashboard | — | — |
| `/login` | auth + demo login | POST `/api/auth/login` (direct fetch) | centered white card, 2 inputs, demo buttons |
| `/dashboard` | Executive Command Center | 7x GET `/api/dashboard/*` parallel | 8 MetricCards, Pie/Bar/Line, quadrants, campaign table |
| `/customers` | searchable paginated list | GET `/api/customers?...` | filter card, table w/ badges, pagination |
| `/customers/[id]` | 360° detail | GET `/api/customers/:id` | header badges, 4 stats, drivers, trajectory, NBA, profile |
| `/segments` | segment cards | GET `/api/segments/overview` | 2-col cards, RaR bars |
| `/campaigns` | create + list | GET+POST `/api/campaigns` | form (7 interventions), table |
| `/campaigns/[id]` | detail + launch | GET + POST `.../launch` | header + launch btn, control vs treatment |
| `/roi-simulator` | live ROI sim (300ms debounce) | POST `/api/roi/simulate` | 5 sliders, 6 metrics, sensitivity chart, CTA |
| `/analytics` | products/deterioration/alerts | 3x GET `/api/analytics/*` | alerts, product table, deterioration list |
| `/experiments` | A/B list read-only | GET `/api/experiments` | single table |
| `/recommendations` | NBA queue | GET `/api/recommendations?priority` | priority filter + table |
| `/risk` | risk-dist + model eval + retrain | GETs + POST retrain | BarChart, AUC tiles, confusion 2x2, explainer |
| `/ai-analyst` | grounded chat | GET suggested, POST `/api/ai/ask` | suggestion pills, chat newest-first |
| `/data` | CSV ingest + retrain | GET status, POST preview/upload, POST retrain | upload + preview w/ mapping |
| `/settings` | workspace + audit | GET me/audit, POST switch | workspace card, audit log |

Before: light-only slate/indigo, no tokens, no dark mode, no motion/3D/skeletons/toasts.

## Phase 2 — Design system (DONE)
Commit `0747fc0`. Charcoal + Hot-Pink tokens in `tailwind.config.js` + `globals.css` CSS vars
(dark default radial `#3a3a3f→#141416`, light warm `#F7F5F6`), Inter + JetBrains Mono via
next/font, tabular-nums, theme toggle persisted in localStorage (try/catch) + anti-flash
inline script, glass/gradient-ring/grid/canvas utilities, pink focus rings, reduced-motion guard.

## Phase 3 — Shared components (DONE)
Commit `fda07c1`. `components/ui.tsx`: Card, MetricCard (compat), StatCard (count-up+spark+delta),
Button (4 variants + loading), Badge + RiskBadge/PrioBadge (compat), Tabs, Table/THead/TH/TD/TRow,
Pagination, Modal, Drawer, Input/Select/Field + inputCls/btnPrimary/btnGhost (compat, restyled),
ToastProvider/useToast, Skeleton/SkeletonCard/TableSkeleton, EmptyState, Tooltip, Avatar
(gradient ring + risk halo), PageHeader, Loading/Err (compat), ChartTooltip/BrandDefs/ChartGradients.
`components/AppShell.tsx`: collapsible sidebar (persisted), gradient active indicator, topbar with
page search, tenant badge, avatar user menu, theme toggle, mobile drawer.

## Phase 4 — 3D and motion (DONE)
Commit `52f8aa5` (+ gradient-defs fix later). `motion.tsx` (Reveal/Stagger/Tilt with
reduced-motion + mouse-glow), `OrbitScene.tsx` (R3F: glossy pink sphere, maroon depth orb,
2 rings, 7 risk-halo orbiters, pointer parallax, dpr≤2, auto-pause on reduced-motion),
`CustomerOrbit.tsx` (dynamic ssr:false + CSS/SVG fallback), `ChurnOrb.tsx` (CSS-only risk donut).
drei NOT installed (custom geometry only — smaller bundle). No CSP change needed.

## Phase 5 — Pages (DONE)
Commit `191a971` (+ fixups). All 14 routes redesigned with shared components; APIs, state,
validation, and copy semantics preserved. Login is split hero + 3D orbit + glass form.
Dashboard has tilt KPI cards + Churn Risk Orb + gradient charts. Every page: PageHeader,
loading/empty/error states, responsive 390/768/1440, focus-visible rings, AA contrast
(white/zinc text; pink used for accents/glows, never body text on pink).

## Phase 6 — Verify (DONE)
- `npm run build` ✅ (17/17 static), `npx tsc --noEmit` ✅ (no eslint config in repo — no `lint` script).
- Backend tests ✅ `65 passed` (backend untouched by UI commits).
- Prod smoke ✅ all 14 routes 200 (`/` 307→/dashboard by design); Playwright click-load of
  login + dashboard at 1440/768/390 with **zero console/page errors**.
- After screenshots ✅ `docs/screenshots/after/` (11 PNGs, dark+light key pages).
- Lighthouse ✅ login 90/100/93; dashboard 88/100/93 (unauthenticated redirect flow — see report).
- Final report ✅ `docs/UI_REPORT.md`.
- Fix log: stale `.next` 500 (`Cannot find module './682.js'`) → clean rebuild; layout `<head>`
  → script-in-body; recharts dropped `<defs>` inside custom wrapper → document-wide
  `ChartGradients`; R3F avatar orbs oversized/black → small emissive spheres.
