# RetainIQ UI Redesign — Progress Tracker
Branch: `feat/ui-redesign` | Stack: Next.js 14 App Router + Tailwind 3 + recharts + lucide-react

## Phase 1 — Audit (DONE)
Date: 2026-10-08

### Pages (14 routes + root redirect)
| Route | Purpose | APIs | Key UI |
|---|---|---|---|
| `/` | redirect → /dashboard | — | — |
| `/login` | auth + demo login | POST `/api/auth/login` (direct fetch) | centered white card, 2 inputs, demo buttons |
| `/dashboard` | Executive Command Center | 7x GET `/api/dashboard/*` parallel | 8 MetricCards, Pie/Bar/Line charts, quadrant tiles, campaign table |
| `/customers` | searchable paginated list | GET `/api/customers?...` | filter card, table w/ RiskBadge+PrioBadge, pagination |
| `/customers/[id]` | 360° detail | GET `/api/customers/:id` | header badges, 4 stats, driver list, trajectory LineChart, NBA card, profile+txns |
| `/segments` | segment cards | GET `/api/segments/overview` | 2-col cards, RaR bars |
| `/campaigns` | create + list | GET+POST `/api/campaigns` | form card (7 interventions), table |
| `/campaigns/[id]` | detail + launch | GET + POST `/api/campaigns/:id[/launch]` | header + launch btn, control vs treatment |
| `/roi-simulator` | HERO live ROI sim | POST `/api/roi/simulate` (300ms debounce) | 5 sliders, 6 MetricCards, sensitivity BarChart, CTA |
| `/analytics` | products/deterioration/alerts | 3x GET `/api/analytics/*` | alerts card, product table, deterioration list |
| `/experiments` | A/B list read-only | GET `/api/experiments` | single table |
| `/recommendations` | NBA queue | GET `/api/recommendations?priority` | priority filter + table |
| `/risk` | risk-dist + model eval + retrain | GET risk-dist, metrics, POST retrain | BarChart, AUC/Prec/Rec/F1 tiles, confusion 2x2, explainer |
| `/ai-analyst` | grounded chat | GET suggested, POST `/api/ai/ask` | suggestion pills, chat bubbles newest-first |
| `/data` | CSV ingest + retrain | GET status, POST preview/upload (multipart), POST retrain | upload card, preview card w/ mapping table |
| `/settings` | workspace + audit | GET me, audit, POST switch | workspace card, audit log |

### Shared components (before)
- `components/ui.tsx`: Card, MetricCard, RiskBadge, PrioBadge, Loading, Err, Field, inputCls, btnPrimary, btnGhost — all light-mode slate/indigo, no dark mode, no animations.
- `app/layout.tsx`: static slate-900 sidebar (w-60, indigo active), top no search, tenant badge+email footer, no collapse, no dark toggle.
- `lib/api.ts`, `lib/format.ts`: unchanged (logic preserved).

### Visual findings (before)
- Light-only `bg-slate-100`, white cards, indigo-600 primary. No design tokens, no dark mode, no glass, no motion, no 3D, no skeletons/empty states/toasts/tooltips.
- Charts: default recharts colors (#ef4444 etc), no gradient fills, no custom tooltip, white grid.
- Typography: system default, no tabular-nums, no uppercase hero style.
- Accessibility: low contrast risks in badges, no focus rings, no keyboard nav states, no reduced-motion.
- Screenshots: `docs/screenshots/before/` — automated Playwright capture deferred (backend auth needed); manual audit above is source of truth. Placeholder README in folder.

### Redesign plan
- **Tokens (Phase 2):** Charcoal + Hot-Pink Gradient theme as specified. CSS vars + tailwind tokens, Inter via next/font, tabular-nums, dark default + light warm off-white, persisted toggle, no flash (inline script).
- **Components (Phase 3):** AppShell (collapsible sidebar, search, tenant badge, user menu, theme toggle), Card, StatCard (count-up+sparkline+delta), Button, Badge, Tabs, Table, Modal/Drawer, Input/Select, Toast, Skeleton, EmptyState, Tooltip, Chart wrapper.
- **3D/Motion (Phase 4):** R3F CustomerOrbit on login (dynamic ssr:false + CSS fallback), CSS tilt+glow KPI, Churn Risk Orb, framer-motion 150-400ms, reduced-motion + hidden-tab pause + pixelRatio≤2.
- **Pages (Phase 5):** Restyle all pages with shared components, same APIs/state/logic, responsive 390/768/1440, WCAG AA, loading/empty/error states.
- **Verify (Phase 6):** build+lint+backend tests, click-through, after screenshots, Lighthouse, UI_REPORT.md, bundle before/after.

## Phase 2 — Design system (TODO)
## Phase 3 — Shared components (TODO)
## Phase 4 — 3D and motion (TODO)
## Phase 5 — Pages (TODO)
## Phase 6 — Verify (TODO)
