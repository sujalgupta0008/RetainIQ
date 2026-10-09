# RetainIQ Audit — Progress Log

Branch: `audit/full-sweep` (created from `main` @ d548531).
Safety: working tree was clean; `retainiq.db` / `.env` untouched; no secrets printed/committed.

## Phase 1 — Recon (findings)

### Repo map
- `backend/` (FastAPI, ~2138 LOC py excl. pycache): `main.py`, `database.py` (SQLite default,
  Postgres via `DATABASE_URL`), `models.py` (16 tables, all tenant-owned tables have `tenant_id`
  + index), `schemas.py` (weak validation — see findings), `services.py` (auth/JWT, CLV/RaR/ROI,
  priority, NBA, explain, AI analyst fallback + LLM provider calls), `deps.py` (Bearer auth),
  `seed.py` (deterministic synthetic data: Demo Bank 400 + Demo Fintech 200, SEED=42),
  `csv_import.py` (banking/telco/generic adapter, deterministic proxies), `ml/train.py`
  (XGBoost→HGB fallback + logistic baseline, stratified 80/20, artifacts to `ml/artifacts/`),
  `ml/infer.py` (artifact load or rule fallback), `ml/explain.py` (stub), `routes/` (13 routers:
  auth, dashboard, customers, predictions, segments, recommendations, roi, campaigns,
  experiments, analytics, ai, data, audit), `tests/` (test_services, test_analyst, test_csv_import,
  test_api smoke-as-script).
- `frontend/` (Next.js 14 + TS + Tailwind + Recharts): 12 pages (dashboard, customers, customers/[id],
  risk, segments, recommendations, roi-simulator, campaigns, campaigns/[id], experiments,
  analytics, ai-analyst, data, login, settings), `lib/api.ts` (fetch wrapper, token in
  localStorage, 401→login redirect), `lib/format.ts`, `components/ui.tsx`. Deps pinned exact in
  `package.json` (next 14.2.5, react 18.3.1, recharts 2.12.7). `next.config.js` empty (no security
  headers). `.env.example` has only `NEXT_PUBLIC_API_URL`.
- `data/sample_customers.csv` (3-row banking sample). `retainiq.db` (local sqlite, gitignored, kept).
- Docs: README/ARCHITECTURE/API/SETUP/DEMO/FEATURES/SIMULATOR.md + 2 Hinglish PDFs (committed).
- No Dockerfile, no CI workflow, no SECURITY.md. `.gitignore` already covers `*.db`, `.env`,
  `node_modules/`, `.next/`. `backend/ml/artifacts/*.pkl` ARE git-tracked (demo convenience).
- Auth flow: register/login → JWT (HS256, 24h, `JWT_SECRET` env or `dev-secret-change-me`) →
  Bearer in localStorage → `current_user` → `tenant_id` scoping. Roles: admin|manager|analyst|viewer.

### How to run / build / test
- Backend: `pip install -r backend/requirements.txt` → `python -m backend.seed --reset` →
  `python -m backend.ml.train` → `python -m uvicorn backend.main:app --reload --port 8000`.
- Frontend: `cd frontend; npm install; npm run dev` (port 3000). Login `admin@demobank.in/demo123`.
- Tests: `python -m pytest backend/tests/ -q` (baseline: **20 passed**; test_api.py runs only as
  script `python -m backend.tests.test_api`, contributes 0 pytest tests — to fix).
- Baseline warnings: `datetime.utcnow()` deprecation (models/seed/services), sklearn
  "valid feature names" UserWarning, PyJWT `InsecureKeyLengthWarning` (20-byte default secret).

### Files read
All backend `.py` (excl. pycache), all frontend `app/**/page.tsx` + `lib/*` + `components/ui.tsx`,
`package.json`, `next.config.js`, `.env.example`, `.gitignore`, `README.md`, sample CSV.
Remaining docs (ARCH/API/SETUP/DEMO/FEATURES/SIMULATOR) skimmed for run instructions only.

## Phase 2 — Security findings (to fix)
- S01 Critical: `POST /api/auth/switch` — any authenticated user can jump to ANY tenant and it
  permanently rewrites `users.tenant_id`. Broken access control / tenant isolation bypass.
- S02 Critical: `POST /api/auth/register` accepts arbitrary `role` (incl. `admin`) + no password
  policy + no email validation → privilege escalation + weak credentials.
- S03 High: `JWT_SECRET` defaults to `dev-secret-change-me` (20 bytes → PyJWT warning); no startup
  check; 24h tokens, no iss/iat.
- S04 High: CSV upload/preview — no size/row/filename limits (`f.file.read()` unbounded) → DoS/OOM.
- S05 Medium: tenant filter missing on some related lookups (`customers/{cid}` detail uses
  `filter_by(customer_id=)` without tenant for predictions/values/recs/features).
- S06 Medium: LIKE wildcard injection (`%`/`_` unescaped in `search` + `find_customer`).
- S07 Medium: no rate limiting on login/register/ai-ask/upload → brute-force/abuse.
- S08 Medium: PII in audit logs (email, raw question) + PII sent to external LLM in `analyst_llm`.
- S09 Medium: `pickle.load` of committed model artifacts (insecure deserialization if tampered).
- S10 Low: CORS `allow_methods/headers=["*"]` + `allow_credentials=True`; no security headers
  (backend or Next); JWT in localStorage (XSS-stealable, SPA-accepted, document).
- S11 Low: frontend `login/page.tsx` ignores typed password (always sends `demo123`).
- Deps: `pip-audit`/`npm audit`/`bandit` pending (Phase 2 verification).

## Phase 3 — Bug/quality findings (to fix)
- B01: `datetime.utcnow()` deprecated (models.now, seed, services.make_token) → timezone-aware.
- B02: `retrain` crashes on empty tenant (`max()` of empty, median of empty frame).
- B03: schemas lack numeric bounds (RoiIn/CampaignIn negative/oversize; page/page_size/limit unbounded).
- B04: `test_api.py` side effects on import, 0 pytest tests → convert to real test functions.
- B05: `upload` sets `priority="Monitor"` + `score=p*50` instead of `priority_of(...)` (inconsistent w/ seed/retrain).
- B06: `explain_fallback` dead assignment (`dev = (m-v); dev = ...`).
- B07: `auth/me` tenant enumeration (any admin sees all tenants) — keep but document; switch fix covers abuse.
- B08: N+1 query patterns (`dashboard.prod_risk`, `analyst_context`) — acceptable at 600 rows; add comment + minor batching where cheap.
- B09: `requirements.txt` unpinned transitive deps; missing CI/lint config.
- B10: `audit(limit)` / `recommendations(limit)` / `customers(page_size)` unbounded → cap.
- B11: `data.upload` median DataFrame built twice → build once (already once; keep).
- B12: seed trajectory uses `rnd` (seeded) — deterministic, fine; launch simulation `Random(42+cid)` — fine for demo, label kept (`"simulated": True`).

## Phase 4 — Testing
- Baseline: 20 passed (services 6, analyst 8, csv 6). Coverage: to measure (pytest-cov).
- To add: `test_security.py` (RBAC, tenant isolation, validation, upload limits, auth edge),
  `test_regression.py` (retrain-empty, pagination caps, priority consistency, utc fix),
  convert `test_api.py` to functions, edge cases (empty/null/huge/malformed).

## Phase 5 — Planned fixes (order: Critical → Low)
1. schemas validation; 2. auth register/switch/login hardening; 3. JWT startup check + headers
   middleware + CORS tighten; 4. upload limits; 5. tenant filters; 6. LIKE escaping; 7. rate limit;
   8. audit redaction + LLM privacy note; 9. pickle guard (hash file + warn); 10. utcnow fixes;
   11. retrain-empty guard; 12. pagination caps; 13. test_api conversion; 14. login-page password bug;
   15. next.config headers; 16. hygiene (.env.example, SECURITY.md, CI, requirements pins).

## Phase 6 — Verification (DONE 2026-10-06)
- `pytest backend/tests/`: **66 passed**, coverage **89%** total.
- Ruff serious subset (F821/E9/E722): pass. Bandit: **0 issues**. pip-audit: `-r` env-broken (numpy
  metadata/py3.13) — `--local` triaged (§D02). npm audit: next 14.2.5→14.2.35, build passes; residual
  needs Next 15 (breaking).
- Live uvicorn boot verified: health, security headers, login→dashboard→simulate→AI,
  404/422/403 guards. `retainiq.db` untouched (7443 pre-existing dev rows).
- Frontend `npm run build` passes. Final: AUDIT_REPORT.md written; branch ready for review.

---
Log: Phases run in order; commits after each phase. Secrets: none found in repo besides default
dev JWT placeholder (ROTATE/SET in prod — listed in final report, value never printed).
