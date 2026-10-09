# RetainIQ — Full Audit Report (`audit/full-sweep`)

Date: 2026-10-06 · Branch: `audit/full-sweep` (3 commits on top of `main` @ d548531)
Scope: every source file (backend ~2000 LOC, frontend 17 pages + lib), git history, deps, live boot.

## 1. Executive summary

| | Before | After |
|---|---|---|
| Overall risk | **High** — broken tenant isolation (any user could jump tenants), open admin self-registration, unbounded uploads, no input validation, silent 500s | **Low (demo-grade)** — all confirmed issues fixed + verified; residual items need human decisions (see §5) |
| Tests | 20 passed (`test_api.py` ran only as a script, 0 pytest tests) | **66 passed**, total coverage **89%** |
| Bandit | 7 issues (2 Medium pickle, 5 Low) | **0 issues** (remaining uses justified + guarded) |
| Ruff (serious: F821/E9/E722) | 1 bare-except + dead code | **All pass** (156 style-only notes left untouched deliberately) |
| npm audit | 9 vulns (1 critical) on next 14.2.5 | next → **14.2.35** (latest 14.x patch, build passes); residual requires Next 15 (breaking, §5) |
| pip-audit | `-r` mode broken by env (numpy 1.26.4 metadata vs Python 3.13); `--local`: project deps show starlette advisory in installed env (drift, §5) | Same (env-level, needs pin refresh — recommended, not done blindly) |
| Live boot | Assumed working | **Verified**: boot, headers, login→dashboard→simulate→AI, 404/422/403 guards |

No secrets found in repo/history (only the `JWT_SECRET` dev placeholder — ROTATE, §3).
`retainiq.db` (7443 dev-accumulated rows) and all data files were **never modified or deleted**.

## 2. All findings

ID | Severity | Category | File:Line | Description | Status | Fix summary
---|---|---|---|---|---|---
S01 | Critical | Broken access control | `backend/routes/auth.py:57` | Any authenticated user (even viewer) could `POST /api/auth/switch?tenant_id=<any>` and it permanently rewrote `users.tenant_id` — full cross-tenant read/write | **Fixed** | Admin-only (`require_role("admin")`), tenant-exists + positive-int checks; documented that prod needs membership table + session-scoped switch |
S02 | Critical | Privilege escalation | `backend/routes/auth.py:19`, `backend/schemas.py:8` | Open registration accepted arbitrary `role` incl. `admin`; no password policy; no email validation | **Fixed** | Schema: email format check + pw 8–128 + role allow-list (`manager/analyst/viewer`, unknown→`manager`); route double-enforces `SELF_SERVE_ROLES` |
S03 | High | Secrets mgmt | `backend/main.py:18`, `backend/services.py:28` | `JWT_SECRET` silently defaulted to `dev-secret-change-me` (20B → PyJWT warning); 24h tokens, no `iat` | **Fixed** | Startup refuses `prod` on default + dev warning; tokens now carry `iat`; `.env.example` documents generation (≥32B) |
S04 | High | DoS / validation | `backend/routes/data.py:33` | `f.file.read()` unbounded, no filename/row/column limits → OOM/CPU on hostile CSV | **Fixed** | 5MB / 20k-row / 100-col caps (413/400), `.csv` gate, rate-limited (preview 30/min, upload 10/min) |
S05 | Medium | IDOR (defense-in-depth) | `backend/routes/customers.py:44`, `predictions.py:43` | Related lookups used `filter_by(customer_id=)` without tenant (PKs are globally unique so exploitation unlikely) | **Fixed** | All related queries now also filter `tenant_id` |
S06 | Medium | LIKE-wildcard injection | `backend/routes/customers.py:29`, `services.py:291` | `%`/`_` in `search` and AI customer-name regex could broaden matches | **Fixed** | New `escape_like()` + `escape="\\"` on both paths |
S07 | Medium | Missing rate limiting | `backend/deps.py:19`, `auth.py`, `ai.py`, `data.py` | login/register/ai-ask/upload unlimited → brute-force/abuse | **Fixed** | In-process per-IP+endpoint limiter (login 30/min, register 20/min, ask/preview 30/min, upload 10/min); documented non-distributed |
S08 | Medium | PII exposure | `backend/routes/ai.py:22`, `services.py:498` | Audit stores emails/raw questions; `analyst_llm` ships customer names + CLV aggregates to Gemini/OpenAI when keys set | **Fixed (documented)** | Truncation kept, privacy docstring + SECURITY.md warning; unset keys = fully local fallback |
S09 | Medium | Insecure deserialization | `backend/ml/infer.py:62` | `pickle.load` of committed `model/scaler.pkl` = RCE if artifacts tampered | **Fixed** | Fixed-dir paths + 100MB cap + `.sha256` sidecars (written by `train.py`) + rule-model fallback; `nosec` justified |
S10 | Low | CORS/headers | `backend/main.py:25`, `frontend/next.config.js` | `allow_methods/headers=["*"]` + credentials; zero security headers anywhere | **Fixed** | Explicit method/header allow-list; `SecurityHeadersMiddleware` + Next `headers()` (nosniff/DENY/referrer/CSP/permissions) |
S11 | Low→Func | Wrong behavior | `frontend/app/login/page.tsx:25` | Form **ignored the typed password**, always sent `demo123` | **Fixed** | Sends typed password; hardcoded demo pw only for one-click demo buttons |
B01 | Medium | Deprecated API | `models.py:9`, `seed.py:3/47/132`, `services.py:32` | `datetime.utcnow()` deprecated (3.12+, warns on 3.13) | **Fixed** | `datetime.now(timezone.utc)` (+naive for DB compat); PyJWT warning gone via longer-secret guidance |
B02 | High | 500 on empty tenant | `backend/routes/predictions.py:24` | `retrain` with 0 features: `max()` of empty + median of empty frame → 500 | **Fixed** | Early 400 with actionable message; test covers |
B03 | Medium | Missing bounds | `schemas.py`, `customers.py:17`, `audit.py:12`, `recommendations.py:13` | Negative costs, `success_rate>1`, unbounded `page_size`/`limit` | **Fixed** | Pydantic `ge/le` everywhere; `page_size≤100`, `audit≤200`, `recs≤500`; `risk` band allow-list |
B04 | Medium | Test anti-pattern | `backend/tests/test_api.py` (old) | Import-time seed + asserts, 0 pytest tests, own-DB side effects on collection | **Fixed** | Real test functions + shared `conftest.py` (isolated `test_audit.db`); `__main__` smoke kept for README |
B05 | Medium | Inconsistent priority | `backend/routes/data.py:118` (old) | Upload hardcoded `priority="Monitor"`, `score=p*50` vs `priority_of()` in seed/retrain | **Fixed** | Upload now batch-normalizes with `priority_of()` (tenant maxima); regression test asserts equality |
B06 | Low | Dead code | `backend/services.py:148` (old) | `dev = (m-v); dev = ...` (first assignment dead) | **Fixed** | Clean trend-deviation expression |
B07 | Info | Tenant enumeration | `backend/routes/auth.py:70` | Any admin lists all tenants via `/me` | **Accepted** | Admin-only already; switch fix removes abuse path; documented |
B08 | Info | N+1 queries | `dashboard.py:51`, `services.py:228` | Per-product/per-campaign loops | **Accepted** | 6 products/600 rows — negligible; dead `vals` query in retrain removed; noted for scale-out |
B09 | Medium | Hygiene | repo root | No CI, no SECURITY.md, no dev-requirements, weak `.env.example` | **Fixed** | Added `.github/workflows/ci.yml`, `SECURITY.md`, `requirements-dev.txt`, hardened `.env.example`/`.gitignore` |
B10 | — | (merged into B03) | — | Unbounded limits | **Fixed** | See B03 |
B11 | Info | Redundant frame build | `data.py` medians | Built twice (already fixed pre-audit to once) | **Verified** | Single build kept |
B12 | Info | Deterministic sims | `seed.py`, `campaigns.py:54` | `Random(SEED)` / `Random(42+cid)` | **Accepted** | Correct for demo reproducibility; labeled `"simulated": True`; `nosec` justified |
D01 | High | Frontend vulns | `frontend/package.json` | next 14.2.5: cache-poisoning/DoS batch; residual critical RCEs cover all 14.x | **Partial** | `next` → **14.2.35** (latest 14.x, `npm run build` passes). Remaining (incl. Windows/AVIF RCE) needs Next 15 (breaking). Mitigations: no `next/image`, no middleware, no remotePatterns, no custom server |
D02 | Medium | Backend pin drift | `backend/requirements.txt` | Pins (numpy 1.26.4, sklearn 1.5.2, pandas 2.2.3) predate Python 3.13; env already drifted newer; `pip-audit -r` can't resolve | **Needs manual action** | Deliberately NOT re-pinned blindly (retest matrix needed); `--local` shows no advisories on project pins except transitive starlette in installed env |
D03 | Low | Dev-chain advisories | frontend transitive | braces/postcss via tailwind 3.4.6 (build-time only); fix = tailwind v4 breaking | **Accepted** | Build-time only, no user CSS ingested; revisit with Next 15 + tailwind 4 upgrade |

## 3. Secrets to rotate (names only, never values)
- `JWT_SECRET` — **ROTATE/SET**: if the dev default was ever used outside localhost, set a fresh ≥32-byte value; all previously issued tokens invalidate on change. Generation command is in `.env.example`.
- `GEMINI_API_KEY`, `OPENAI_API_KEY` — optional; no values were present in repo/history/env. If ever set in shared shells, rotate at providers.
- `DATABASE_URL` — no password in repo (SQLite default). Use a strong Postgres password in prod.
- Demo credentials (`admin@demobank.in / demo123`, seeded) — demo-only; never reuse in any real deployment.

## 4. Tests & scans
- Baseline (before): `20 passed` (`test_services` 6 + `test_analyst` 8 + `test_csv_import` 6; `test_api` contributed 0 — import-time script). Coverage not measured.
- After: **66 passed** (`-q`, ~8–11s), **total coverage 89%** (`--cov=backend`). New: `conftest.py` (isolated seeded DB), `test_security.py` (17: RBAC, isolation, validation, upload guards, rate-limiter unit, LIKE escaping), `test_regression.py` (12: empty-retrain 400, priority consistency, ROI clamping, JWT claims, CSV edges), `test_endpoints.py` (9: all dashboard/segments/analytics/experiments/campaign/audit/headers), `test_api.py` rewritten (5 real tests + `__main__` smoke).
- Uncovered (deliberate): `ml/train.py` retrain-success path (would overwrite shipped artifacts + slow), some `infer.py` fallback branches, `explain.py` stub (17%).
- Ruff: serious subset (F821/F822/F823/E9/E722) **passes**; fixed bare-except, try-pass→logged, dead `vals` query, bad `noqa`. 156 style notes (import order, `BLE001`, `B008`) left as-is — cosmetic, not worth churn.
- Bandit: **before 7 (2M+5L) → after 0** (remaining uses `nosec`-justified + guarded).
- Live verification (uvicorn, real `retainiq.db` untouched): health OK, security headers present, login→dashboard (7443 pre-existing dev rows) OK, simulate OK, AI OK, 404/422/403 guards behave.
- Frontend: `npm run build` **passes** on next 14.2.35.

## 5. Remaining risks / not fixed (and why)
1. **Next.js 15 upgrade (D01)** — residual criticals (Windows-host RCE, AVIF RCE, SSRF set) affect all 14.x; fix = Next 15 major (App Router breaking changes, React 19, tailwind 4 chain). Not attempted in an audit run without a visual-regression harness. Mitigations verified in §2/D01.
2. **Backend pin refresh (D02)** — needs a clean Python-version matrix reinstall + full retrain + test; blind bumps risk breaking the pinned ML stack.
3. **JWT in localStorage + no CSRF/refresh/revocation** — SPA-standard but XSS-stealable; prod needs httpOnly cookies + refresh rotation + logout blocklist.
4. **Tenant switch mutates `users.tenant_id`** — now admin-only, but prod needs a membership table + session-scoped switch.
5. **In-memory rate limiting** — single-process only; multi-worker/prod needs Redis/gateway limits.
6. **Audit-log PII + LLM exfiltration (S08)** — minimized + documented; strict-PII deployments should disable `ai_ask` audit and keep provider keys unset.
7. **Committed `*.pkl` artifacts** — convenient for demo, but binary blobs in git; consider Git-LFS or train-in-CI.
8. **`retainiq.db` (7443 rows)** — pre-existing dev accumulation, left untouched; recommend `seed --reset` for clean demos (back up first).

## 6. Recommendations (next steps)
1. Schedule Next 15 + React 19 + tailwind 4 upgrade with visual tests; re-run `npm audit` to zero.
2. Refresh backend pins against Python 3.12/3.13 in a matrix CI job; un-break `pip-audit -r`.
3. Move auth to httpOnly cookies + refresh rotation; add login CAPTCHA/alerting; Redis rate limits.
4. Replace permanent tenant-switch with membership table + session scope; add per-tenant API keys for service use.
5. Add Postgres-backed staging CI (current CI uses SQLite) + retrain-path test with artifact sandboxing.
6. Push coverage of `train.py`/fallback branches; add frontend (jest/playwright) smoke for login→dashboard→simulator.
7. Rotate any exposed dev `JWT_SECRET`; set `RETAINIQ_ENV=prod` in staging to enforce the guard.
