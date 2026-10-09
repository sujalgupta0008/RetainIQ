# RetainIQ login-fit — Progress Tracker
Branch: `fix/login-fit` (from `feat/ui-retheme`). Goal: 100% zoom looks like 67% zoom; login never scrolls on desktop.

## Phase 1 — Measure (DONE)
Playwright, deviceScaleFactor 1, 100% zoom, light theme, prod build. Shots: `docs/screenshots/before-fit/`.
| Viewport | scrollHeight | innerHeight | Scroll? | Overflow |
|---|---|---|---|---|
| 1920x1080 | 1080 | 1080 | no | 0 |
| 1536x864 | 1068 | 864 | YES | 204px |
| 1440x900 | 1068 | 900 | YES | 168px |
| 1366x768 | 1068 | 768 | YES | 300px |
| 1280x720 | 1068 | 720 | YES | 348px |
| 1024x768 | 1068 | 768 | YES | 300px |
| 768x1024 | 1489 | 1024 | YES | 465px (stacked) |
| 390x844 | 1535 | 844 | YES | 691px (stacked) |
Content is ~1068px tall fixed (grid + hero + card don't shrink). Only 1080p fits.

## Phase 2 — Global scale (DONE)
- `html { font-size: 16px }` below lg (mobile readability unchanged); at ≥1024px
  `clamp(13px, 100vw/105, 14.5px)` → 1440px ≈ 13.7px, 1366px ≈ 13px, 1920px capped 14.5px.
  All rem-based Tailwind spacing/type scales together. No zoom/transform hacks.
- Proportional cuts: `.page-title` 22/26px → 1.15/1.35rem; StatCard 26→22px; dashboard
  KPIs 30→26px; login H1 → fluid `.hero-title` (max 3rem); Card p-5→p-4; tables fixed
  `text-[13px]` (≥12px floor everywhere; buttons/labels keep rem sizes).
- Drive-by: login H1 now uses `var(--text-1)` so dark mode stays readable.
- Build ✅ tsc ✅.

## Phase 3 — Login one-screen (DONE)
- Root: `min-h-[100dvh]`, and on lg+ `h-[100dvh] + overflow-hidden`; two-col grid
  (`1fr 1.05fr`), vertically centered, tighter rhythm (py-4/6, gaps, brand row, card p-4/5).
- Right column (`lg:max-h + overflow-hidden`, flex): hero on top
  (`.login-hero`: `clamp(180px,28vh,320px)`, `overflow:hidden`, bottom fade mask — decorative
  crop, never overlaps the card), compact form below (p-4/5, 2.75rem inputs/buttons ≈40px,
  tighter dividers, demo buttons one row, one-line note).
- Short screens (`max-height:760px`): hero + feature chips hidden via `.hide-short`.
- Mobile (<lg): stacked + scrollable; hero hidden; chips + hero CTA row hidden below md
  (duplicates of form actions) so the form fits one screen.
- Result: 8/8 viewports scrollHeight == innerHeight (incl. 390x844).
- Build ✅ tsc ✅.

## Phase 4 — Verify (DONE)
- Login no-scroll asserted programmatically (scrollHeight <= innerHeight):
  1920x1080: 1080<=1080 · 1536x864: 864<=864 · 1440x900: 900<=900 ·
  1366x768: 768<=768 · 1280x720: 720<=720 — all PASS, submit button in viewport each time.
- Zero console/page errors on all login captures; demo login still lands on dashboard.
- App pages at 1440x900 + 1366x768 (dashboard, customers, roi-simulator, risk, settings):
  all load clean, no error states, layout balanced after scale change (screenshots checked).
- `npm run build` ✅ 17/17 · `tsc --noEmit` ✅ · no eslint config / `lint` script in repo
  (same as baseline) · backend **65 passed** (= baseline).
- Shots: `docs/screenshots/after-fit/` (5 login + 2 dashboard). Report section added.
- Pre-existing quirk (noted, not introduced): `.next` sometimes goes stale (`./682.js`)
  when servers are swapped mid-build — clean rebuild fixes; no code impact.

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

## Phase 3 — 3D/motion light version (DONE)
- Login split: left navy headline + supporting text + trust chips + “Try the live demo”
  (reuses demo-login logic) + focus-form button; right = new `FloatingDash` (pure CSS 3D:
  perspective tilt board, depth shadows, SVG area chart, 3 bobbing glass cards, platform glow)
  with the sign-in card overlapping. Zero WebGL on the light theme.
- Removed R3F: deleted `OrbitScene`/`CustomerOrbit`, uninstalled `three`,
  `@react-three/fiber`, `@types/three` (lockfile updated consistently via npm).
- Motion: existing Reveal/Stagger/Tilt reused (150–400ms); global reduced-motion guard
  freezes the bobbing; tilt is mouse-only.

## Phase 4 — Re-theme remaining pages (DONE)
- `AppShell`: navy gradient sidebar (white icons, blue-pill active + glow, icon-only collapse),
  light topbar, blue tenant badge/focus states; all logic unchanged.
- Page sweep: every hardcoded pink replaced — AI bubbles/links blue, driver dots orange/teal,
  risk bars/legend green/amber/orange, upload/CTA gradients blue, ROI slider blue, treatment
  panel blue, segment bars blue, Open-links navy-blue.
- Remaining `text-semantic-*` / `text-risk-high` usages resolve through new tokens (teal
  growth, orange high-risk) — no edits needed. Tilt glow + Tabs hover + tooltip dot → blue.

## Phase 5 — Verify (DONE)
- `npm run build` ✅ 17/17 · `tsc --noEmit` ✅ · backend **65 passed** (= baseline, untouched).
- `git diff -- frontend/next.config.js` ✅ empty. Prod smoke ✅ 13/13 routes 200.
- Screenshots ✅ `docs/screenshots/after-retheme/` (14 PNGs, light+dark, 1440/768/390) —
  every capture zero console/page errors.
- Lighthouse login 90/100/93 ✅; authed-dashboard LH blocked by context isolation →
  Playwright vitals instead (FCP ~80ms, CLS 0.022, TBT 0). Details in `docs/UI_REPORT.md`.
- Fixes from verify: Button primary default; stale-build 500s; orphaned servers.
- Report ✅ `docs/UI_REPORT.md` rewritten for the re-theme.

## (old phases 1–6 audit table from the charcoal redesign follows)

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
