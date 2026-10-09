# RetainIQ UI Re-theme — Final Report
Branch: `feat/ui-retheme` (from `feat/ui-redesign`) · Date: 2026-10-08
Reference: light blue/navy SaaS dashboard (style + layout guide; all visuals rebuilt, no copied assets)

## 1. Tokens
- **Light DEFAULT** (`lib/theme.tsx` default + anti-flash script + `<html class=light>`);
  dark = deep navy `#0A142E → #0F2350` on the same persisted toggle.
- Canvas: `#F4F8FF → #FFFFFF` + faint blue radial glow + subtle dot pattern (masked).
- Cards: white, rounded-2xl, 1px `#E6ECF5`, layered blue shadow
  (`0 10px 30px rgba(37,99,235,0.08)` + stacking).
- Sidebar: always navy gradient `#0B1A3A → #0F2350`, white icons, active = blue pill + glow.
- Primary `#2563EB` (hover `#1D4ED8`), gradient `#2563EB → #3B82F6`; teal `#14B8A6` for
  success/retention/growth. Headings navy `#0B1A3A` bold, body `#475569`, muted `#94A3B8`.
- **Risk scale (badges + charts + pills + halos):** Very High `#EF4444` · High `#F97316` ·
  Medium `#F59E0B` · Low `#22C55E`. Backend stores Low/Medium/High only; Very High is
  display-level for proba ≥ 0.8 (priority list).
- Charts: blue `#3B82F6` main, teal secondary, risk colors above, gradient fills → transparent,
  light grid `#EEF2F7`. Inter + JetBrains Mono kept, tabular numbers, WCAG AA
  (navy/slate text; white on `#2563EB` = 8.6:1; pills use dark text on tinted bg).

## 2. Components changed
- `tailwind.config.js` + `globals.css`: full token swap (kept key names so pages auto-adapt).
- `ui.tsx`: Button defaults to **primary** when variant omitted (bug found in verify — login
  CTA rendered white), blue gradients, teal/orange/red badge tones, 4-level `RiskBadge`,
  blue Table hover, blue focus rings/tooltip dot/tilt glow, `ChartGradients` → blue/teal,
  avatar gradients blue/navy + 4 risk halos. Removed dead `BrandDefs` export.
- `AppShell.tsx`: navy sidebar, blue-pill active, light topbar.
- `FloatingDash.tsx` (new): pure CSS-3D tilted dashboard, SVG chart, 3 bobbing glass cards.
- Deleted: `ChurnOrb.tsx` (superseded by KPI mini-donut), `OrbitScene.tsx` + `CustomerOrbit.tsx`
  (R3F removed); uninstalled `three`, `@react-three/fiber`, `@types/three`.
- Dashboard helpers (in-page): `bandOf` (proba → display band), `outreach` mapping
  (rm_call/service_recovery → “Call now”, Monitor → “Monitor”, else “Email offer”),
  `MiniDonut`, `AucGauge`.

## 3. Dashboard recomposition (same endpoints, no API changes)
KPIs (Total + segment count/median CLV · At Risk + % + 3-share mini donut · Retention
Opportunity = expected protected, teal) → Churn Trend (High % area from trajectory≥60%
counts + avg-risk teal line) + Retention Priority top-5 (avatar, proba/RaR, risk pill,
outreach chip, links) → Segments donut (% legend) + Top Drivers blue bars (RaR share) +
AUC gauge (“Trained on N” — no timestamp exists in metrics) → floating glass call
mini-card top-3 (overlaps grid on lg, inline on mobile) → campaign table retained.
- Honest placeholders (no invented numbers): Very High series → caption (band not stored);
  untrained model → fallback note; empty queue/campaigns → EmptyStates.
- Dropped display-only: quadrant tiles, revenue-by-segment bars (same data on Segments page).

## 4. Before / after
After shots (prod build, real demo data, zero console errors on every capture):
`docs/screenshots/after-retheme/` — 14 PNGs:
| Page | 1440 | 768 | 390 |
|---|---|---|---|
| Login light/dark | `login-1440-{light,dark}.png` | `login-768-{light,dark}.png` | `login-390-{light,dark}.png` |
| Dashboard light/dark | `dashboard-1440-{light,dark}.png` | `dashboard-768-{light,dark}.png` | `dashboard-390-{light,dark}.png` |
| Customers light/dark | `customers-1440-{light,dark}.png` | — | — |
“Before” = `docs/screenshots/after/` (charcoal-pink theme, previous phase).

## 5. Bundle size (First Load JS)
| Route | Redesign | Re-theme | Δ |
|---|---|---|---|
| shared | 87.6 kB | 87.5 kB | −0.1 |
| /login | 97.6 kB | 134 kB | +36 (framer-motion now in login chunk; three/fiber gone) |
| /dashboard | 254 kB | 254 kB | 0 (13.7 kB page) |
| others | 131–236 kB | 131–236 kB | ±1 |
R3F/three chunks eliminated (were dynamic-only on login). No perf collapse (below).

## 6. Scores
- Lighthouse **/login**: Performance **90** · A11y **100** · Best practices **93**
  (FCP 1.2s / LCP 3.6s / TBT 20ms / CLS 0 — same shell as before, CSS hero is cheap).
- Lighthouse on the **logged-in dashboard was technically blocked**: LH opens an isolated
  browser context, and app auth is localStorage-bound (unchanged by design), so the run
  always hit the login redirect (verified: finalUrl …/login, scores 0). Tried context-seeded
  storage + `--disable-storage-reset` — LH still isolates.
- Instead, real authed-dashboard vitals via Playwright PerformanceObserver (3 runs, 1440px):
  **FCP ~80ms · CLS 0.022 · longtask-blocking 0ms** · no console/page errors · stayed on
  `/dashboard` with data rendered. (LCP entry absent — text/chart paint; FCP/CLS/TBT all green.)

## 7. Verification (all ran)
- `npm run build` ✅ 17/17 · `tsc --noEmit` ✅ · backend **65 passed** (= baseline; backend untouched).
- `git diff -- frontend/next.config.js` ✅ empty (headers/CSP not weakened).
- Prod smoke ✅ 13/13 routes 200 (`/` redirects by design); Playwright authed loads ✅ 14/14 clean.
- Bugs found by verifying: primary Button rendered white when `variant` omitted (fixed default);
  stale `.next` 500s (clean rebuild); EADDRINUSE from orphaned servers (killed).

## 8. Known gaps
1. No LH Lab score for the authed dashboard (isolation, above) — field-style vitals substituted.
2. Very High trend series has no data source (documented caption, not invented).
3. “Last updated” for the model doesn’t exist in metrics — shows “Trained on N”.
4. Screenshots cover login/dashboard/customers; other routes share shell/components, all 200 + clean.
5. Segments donut labels come from backend segment names (currently quadrant-style names) — real data, shown as-is.
6. **Login follow-up (2026-10-08):** right-column overlap fixed (visual gets `pb-10` breathing
   room, floating chips constrained inside the board, form no longer pulled up over the visual).
   Added “Continue with Google” (inline G logo, no external assets): attempts real GIS +
   `POST /api/auth/google` only when `NEXT_PUBLIC_GOOGLE_CLIENT_ID` is set; otherwise shows an
   honest “not connected” message. Real Google login needs backend OAuth + client ID (out of
   UI scope) — verified: message shows, email/demo flows unchanged and land on dashboard.

## 9. Login-fit pass (fix/login-fit, 2026-10-08)
Goal: 100% zoom looks like the old 67% zoom; login never scrolls on desktop.
- **Measure:** only 1920x1080 fit before (content fixed ~1068px; 1366x768 overflowed 300px).
- **Global scale:** `html font-size 16px` below lg; at ≥1024px
  `clamp(13px, 100vw/105, 14.5px)` — rem-based Tailwind scales together, no zoom/transform.
  Plus proportional cuts (page titles, StatCard/KPI sizes, fluid hero title, Card padding,
  tables fixed 13px so body text stays ≥12px).
- **Login one-screen:** `100dvh` + `overflow:hidden` on lg, 2-col grid; hero capped
  `clamp(180px,28vh,320px)` with fade (never overlaps card); compact card (≈40px inputs);
  hero+chips hidden under 760px height; hero hidden and chips/CTA row hidden below md on
  mobile so the form fits one screen.
- **Verify:** scrollHeight<=innerHeight asserted on 1920/1536/1440/1366/1280 (all exact-fit,
  submit in viewport, zero console errors); dashboard/customers/simulator/risk/settings clean
  at 1440x900 + 1366x768; build 17/17, tsc clean, backend 65 passed; shots in
  `docs/screenshots/after-fit/` (before: `before-fit/`).
