# RetainIQ UI Re-theme — Progress Tracker
Branch: `feat/ui-retheme` (from `feat/ui-redesign`) · Reference: light blue/navy SaaS dashboard
Prior redesign report: `docs/UI_REPORT.md` (will be rewritten in Phase 5).

## Phase 1 — Tokens (DONE)
Light is DEFAULT (`lib/theme.tsx` default + anti-flash script + `<html class=light>`); dark =
deep navy `#0A142E→#0F2350` via same persisted toggle.
- Canvas light: `#F4F8FF→#FFFFFF` + blue radial glow + subtle dot pattern (`canvas-grid` is now
  dots, masked). Dark keeps dot pattern in slate.
- Cards: white `#surface`, 1px `#E6ECF5`, layered blue-tinted shadow; dark = navy glass.
- Primary `#2563EB` (hover `#1D4ED8`), gradient `#2563EB→#3B82F6`; teal `#14B8A6` success/retention.
  Headings navy `#0B1A3A`, body `#475569`, muted `#94A3B8`.
- Risk scale 4-level everywhere: Very High `#EF4444` · High `#F97316` · Medium `#F59E0B` ·
  Low `#22C55E` (`RiskBadge` + `chartColors.risk` + avatar halos). Backend bands stay
  Low/Medium/High; Very High is display-only for proba ≥ 0.8 (dashboard priority list).
- Charts: blue `#3B82F6` main, teal secondary, light grid `#EEF2F7`, gradient fills → transparent.
- Kept token names (`brand`, `risk`, `semantic`, shadows) so shared components auto-adapt;
  `gradient-text` is now blue→teal, `glass` is white/blue-shadow in light.
- Build ✅ tsc ✅ (no visual page changes yet — old pink gradients in pages die in Phase 2–4).

## Phase 2 — Dashboard recomposition (DONE)
New `app/dashboard/page.tsx`: 3 KPI cards (Total w/ segment count+median CLV; At Risk w/ %
+ 3-share mini donut; Retention Opportunity = expected protected, teal) → trend + priority
(2fr) beside segments/drivers/AUC (1fr) → floating glass call-prioritization card (top-3,
overlaps grid edge on lg, inline on mobile) → campaign table retained.
- Trend = High % area (real: trajectory≥60% counts/total) + avg-risk teal line; Very High has
  no data source → honest caption instead of invented series (spec-allowed placeholder).
- Priority/action mapping (documented): rm_call|service_recovery → “Call now” 📞,
  Monitor priority → “Monitor” 👁, else → “Email offer” ✉; risk pill from proba
  (≥.8 Very High / ≥.6 High / ≥.35 Medium / else Low). Top-5 by priority rank.
- Segments donut = customer-count share w/ % legend (real); drivers = RaR-share blue bars;
  AUC radial gauge + “Trained on N” caption (no timestamp exists in metrics — used real field).
- Dropped: old quadrant tiles + revenue-by-segment bars (same data lives on Segments page).
- Deleted `ChurnOrb.tsx` (superseded by KPI mini-donut) and dead `BrandDefs` export.

## Phase 3 — 3D/motion light version (TODO)
## Phase 3 — 3D/motion light version (TODO)
## Phase 4 — Re-theme remaining pages (TODO)
## Phase 5 — Verify (TODO)

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
