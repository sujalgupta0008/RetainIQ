# RetainIQ — FEATURES.md (Source of Truth)

> This document describes the ACTUAL implementation in this repo. Code follows this doc; where code diverged for simplicity, this doc was updated to match code.

## 1. Product overview
RetainIQ is an AI-powered customer retention & ROI intelligence platform for banks/fintechs. Closed loop: **DETECT → EXPLAIN → PRIORITIZE → DECIDE → SIMULATE → ACT → MEASURE → LEARN**. Hero feature: **Retention ROI Simulator**. Stack: Next.js+TS+Tailwind+Recharts frontend, FastAPI+Pydantic+SQLAlchemy backend, SQLite-by-default (Postgres-compatible via `DATABASE_URL`), Pandas+Scikit-learn+XGBoost(fallback)+SHAP(fallback) ML, provider-abstracted LLM with deterministic fallback.

## 2. Problem statement
Banks lose customers via declining engagement, balance migration, complaints, inactivity. Legacy churn tools only answer "who will churn". Institutions need: who, why, value, revenue at risk, who is worth saving, what action, what spend, expected ROI, did it work, what works best.

## 3. Target users
Banks, fintechs, digital lenders, retention/CRM teams, BI/data teams, relationship managers, executives.

## 4. User personas
- **Retention Manager (Priya):** builds campaigns, simulates ROI, launches A/B tests.
- **Relationship Manager (Arjun):** works Customer 360 queue, calls top-priority accounts.
- **Exec (CRO Meera):** watches Command Center: revenue at risk, expected protected, ROI.
- **Data Analyst (Kabir):** uploads CSV, checks model metrics, segments.

## 5. Product goals
G1 Predict churn with calibrated probability + risk band. G2 Explain every prediction in plain language. G3 Value every customer (CLV) + revenue at risk. G4 Recommend next-best-action with cost/success/ROI. G5 Simulate ROI before spend (hero). G6 Execute campaigns + A/B experiments + measure incremental lift + ROI. G7 Answer NL questions from real data (AI analyst, no hallucination). G8 Multi-tenant demo (Demo Bank, Demo Fintech). G9 Fully demoable locally with seeded data, no keys required.

## 6. Non-goals
No real core-banking integration, no real payment execution, no enterprise IAM/SSO, no streaming/Kafka, no model registry/retraining pipelines, no vector DB/RAG agents, no mobile app.

## 7. Complete feature inventory
P0: auth+RBAC+tenancy, Executive Command Center, Customer 360, churn prediction (XGB+LogReg), SHAP-style explainability, CLV, revenue-at-risk, priority scoring/segments, next-best-action, ROI simulator (+sensitivity), Campaign Studio (simulate→launch→simulated execution), experimentation (control/treatment), campaign results, AI analyst (LLM + deterministic fallback).
P1: risk trajectory (90/60/30/today), deterioration score, segment analytics (value×risk quadrants), product analytics, alerts, audit log, CSV upload + sample download, demo mode with seed data.

## 8. Functional requirements
- FR-AUTH-1: register/login/logout, JWT, roles admin/manager/analyst/viewer, tenant isolation enforced server-side from token (never trust client tenant header alone).
- FR-DASH-1: all 12 hero metrics computed from DB via services (no hardcoding).
- FR-CUST-1: searchable/sortable/filterable customer list (pagination); FR-CUST-2: 360 page with profile, balances, activity, predictions, drivers, NBA, trajectory.
- FR-ML-1: train script produces artifacts + metrics; FR-ML-2: inference endpoint returns proba+band+drivers; FR-ML-3: metrics page shows AUC/precision/recall/F1/confusion matrix.
- FR-XAI-1: per-customer top +/− drivers with human sentence (template from real feature deltas, never invented).
- FR-CLV-1/RAR-1: transparent formulas (see §22–23), labels estimated/predicted/realized.
- FR-PRIO-1: priority score 0–100 + Critical/High/Monitor/Low.
- FR-NBA-1: 8 actions with cost/success/ROI reasoning.
- FR-ROI-1: inputs→outputs per formulas (§25), live charts, 3 scenarios.
- FR-CAMP-1: audience builder (risk/CLV/product/segment filters) → projected ROI → launch (simulated reach/outcome using NBA success rates + noise, seeded).
- FR-EXP-1: control/treatment split at launch (default 20% control), incremental lift + revenue + ROI.
- FR-AI-1: NL Q&A grounded in DB aggregates; fallback answers 6 canonical questions + generic summary.
- FR-DATA-1: CSV upload with validation; sample CSV download.
  `backend/csv_import.py` normalizes banking / IBM-Telco / generic schemas
  (detect → normalize → validate → insert → features → predictions).
  Telco money fields are documented domain-adapted proxies, never real balances;
  Churn Value is preserved as the ML target; retrain learns new labels.
- FR-AUDIT-1: log login/campaign/simulate/launch/AI/upload.

## 9. Non-functional requirements
Page load <3s local, API p95 <500ms (SQLite, <1k customers), deterministic seed (`SEED=42`), reproducible ML (`random_state=42`), TypeScript strict, Pydantic validation, proper HTTP codes, graceful loading/empty/error states, no secrets in git, CORS env-configured.

## 10. Complete application architecture
Monolith: `frontend (Next.js)` → `backend (FastAPI :8000)` → `SQLite file retainiq.db` (or Postgres when `DATABASE_URL` set) + `backend/ml/artifacts/*.pkl`. No microservices/workers/Redis. ML training is an offline script; inference is imported functions (same process).

## 11. Frontend architecture
Next.js 14 App Router, TS strict, Tailwind, Recharts, lucide-react. `lib/api.ts` (fetch wrapper with JWT), `lib/format.ts` (INR formatting), components: MetricCard, RiskBadge, DataTable, ChartCard, FilterBar, Modal. Pages: /login /dashboard /customers /customers/[id] /risk /segments /recommendations /roi-simulator /campaigns /campaigns/[id] /experiments /analytics /ai-analyst /data /settings. Auth guard via localStorage token + middleware-free client redirect.

## 12. Backend architecture
Single FastAPI `main.py`. Layers: `routes/*.py` (thin HTTP) → `services.py` (all domain logic, plain functions) → `models.py` (SQLAlchemy) → `database.py` (engine/session, `get_db`, tenant helper). `schemas.py` Pydantic. `seed.py` synthetic data. `ml/train.py`, `ml/infer.py`, `ml/explain.py`.

## 13. Database architecture
Normalized, FK'd, indexed (tenant_id, customer_id, timestamps, risk, campaign_id). SQLite default for zero-setup demo; Postgres-compatible (no SQLite-only SQL; autoincrement PKs, DateTime, Float). Tables (13, pragmatic subset of spec): tenants, users, customers, accounts, products, customer_products, transactions, interactions(complaints+contacts unified with type field + separate complaints view via type='complaint'), customer_features, churn_predictions, customer_values, retention_recommendations, campaigns, campaign_targets, experiments, experiment_results, audit_logs. (Spec's `complaints`/`customer_interactions` merged into `interactions` with `kind` column to keep code small — documented divergence.)

## 14. ML architecture
`ml/train.py`: ingestion (from DB/seed CSV) → validation → preprocessing (StandardScaler + one-hot for product mix, median impute) → engineered features (16 listed) → stratified train/test split → Baseline LogisticRegression → Primary XGBoost (or HistGradientBoostingClassifier fallback if xgboost missing) → eval → persist `artifacts/{model.pkl, baseline.pkl, scaler.pkl, features.json, metrics.json}`. Leakage prevention: only behavioral windows ≤ prediction date; label = churned within next 90d (synthetic rule + noise); random_state=42 everywhere.

## 15. AI/LLM architecture
`services.ai_analyst(question, tenant_id)`: 1) classify intent (keyword rules), 2) run DB aggregate tools (revenue at risk by segment, top customers, intervention ROI, budget allocation, trend), 3) build structured context JSON, 4) if `GEMINI_API_KEY` or `OPENAI_API_KEY` set → call provider via httpx (Gemini `generateContent` / OpenAI chat completions, 15s timeout) with "answer ONLY from context" system prompt, else deterministic template answer. LLM never sees raw PII beyond aggregated names/IDs needed; never invents numbers (fallback computes exactly; LLM path includes numbers in context and instruction to cite them).

## 16. API architecture
REST `/api/*`, JSON, JWT Bearer. Pagination `?page&page_size`, filtering, sorting. Errors `{detail}` with proper codes. OpenAPI at `/docs`.

## 17. Authentication architecture
Register/login → PBKDF2-HMAC-SHA256 (100k iters, per-user salt) + JWT (PyJWT, HS256, 24h, claims sub/tenant_id/role). `get_current_user` dependency; role guard `require_role([...])`; tenant scoping `tenant_id == token.tenant_id` on every query. Demo accounts seeded.

## 18. Multi-tenant architecture
`tenants` table; every business table has `tenant_id` FK + index; all service queries filter by it. Demo: Demo Bank (400 customers), Demo Fintech (200). Login selects tenant implicitly via user; tenant switcher calls `/auth/switch?tenant=` (demo convenience, still server-validated membership).

## 19. Data flow
Seed script → DB → train.py reads customer_features+labels → artifacts → infer.py on new/changed customers → predictions+values+recommendations rows → API services aggregate → frontend charts/tables → user simulates/launches campaign → campaign_targets+experiments rows → simulated outcomes → results + audit.

## 20. Customer lifecycle flow
Active → At-risk (deterioration score>50 or proba 0.4–0.6) → High-risk (proba≥0.6) → Targeted (in campaign) → Reached → Retained/Churned (simulated) → measurement feeds experiment lift.

## 21. Churn prediction flow
Nightly-equivalent (on seed + on upload + manual `/predictions/retrain`): compute features → scaler → XGB predict_proba → band (Low<0.35, Medium 0.35–0.6, High≥0.6) → persist + trajectory snapshot (today; 30/60/90d backfilled synthetically at seed with decay noise).

## 22. Customer value calculation (CLV — transparent)
```
annual_contribution = avg_balance*0.035 + annual_txn_volume*0.002 + product_count*1200 - complaint_count_1y*500   (floor 500)
expected_years = min(7, 3 + tenure_months/24)
CLV = annual_contribution * expected_years
```
avg_balance from accounts; annual_txn_volume = avg_txn_value*txn_freq*12. Margin assumptions documented in UI tooltip ("estimated").

## 23. Revenue-at-risk calculation
```
revenue_at_risk = churn_probability * CLV   (predicted/estimated, NOT realized)
```
Dashboard sums per segment. Labels: estimated (CLV), predicted (risk), realized (campaign-measured retained revenue only).

## 24. Next-best-action logic
Catalog (cost ₹, base success): fee_waiver(500,0.22), cashback(1200,0.28), personalized_offer(800,0.25), loan_offer(2000,0.20), premium_upgrade(1500,0.18), rm_call(1000,0.30), service_recovery(700,0.35 if complaints>0 else 0.10), no_intervention(0,0.02). Rule boosts: complaints→service_recovery; balance_drop→cashback; inactivity→rm_call; low products→personalized_offer; high CLV→rm_call/premium. Score = success_adj*CLV − cost; pick max expected net; store reasoning string + expected ROI = net/cost.

## 25. ROI simulator formulas (centralized in services.py + tested)
```
targeted = count(audience filters)
retained = targeted * success_rate
cost = targeted * intervention_cost
revenue_protected(estimated) = retained * avg_CLV(audience)
net = revenue_protected − cost
roi = net / cost  (guard cost=0)
break_even_rate = cost_per_customer / avg_CLV
scenarios: conservative 0.6×, expected 1.0×, optimistic 1.4× success (clamped ≤0.9)
```

## 26. Campaign architecture
Campaign {audience JSON, intervention, offer_cost, expected_success, duration_days, status draft/launched/completed}. Launch: resolve audience query → split 80/20 treatment/control (seeded RNG) → campaign_targets rows → simulate: treatment retained ~ Bernoulli(expected_success), control ~ Bernoulli(base_rate=avg churn complement ≈0.15) → experiment + experiment_results rows → status completed (simulated execution instant for demo, timestamps recorded).

## 27. Experimentation/A-B testing architecture
One experiment per campaign: groups control/treatment; metrics: churn_rate, retention_rate, incremental_retention = treat_ret − ctrl_ret, est_revenue_impact = incremental*treat_n*avg_CLV, cost, ROI. No causal claims beyond design; UI notes "simulated outcomes for demo".

## 28. Outcome measurement
Realized metrics only from campaign_targets outcomes + control comparison. Predicted vs realized shown side-by-side on campaign detail.

## 29. AI analyst architecture
See §15. Tools (Python functions): revenue_at_risk_by_segment, top_priority_customers(n), intervention_roi_table, budget_allocator(budget), risk_trend, campaign_summary. Intent router + fallback templates.

## 30. Explainability architecture
SHAP if installed (TreeExplainer on XGB, top-5 abs values) else fallback: standardized-feature-delta × model coefficient/importance → top +/− drivers mapped to human labels + template sentence: "Churn risk {increased|is high} primarily because {driver phrases with % deltas}." Deltas computed vs tenant median (real numbers).

## 31. Dashboard/page structure
/login, /dashboard (12 metrics + 6 charts), /customers (table), /customers/[id] (360), /risk (distribution+trend+model metrics), /segments (quadrants), /recommendations (NBA queue), /roi-simulator (hero), /campaigns + /campaigns/[id], /experiments, /analytics (product/segment/deterioration), /ai-analyst (chat), /data (upload/sample/retrain), /settings (tenant, keys status, user).

## 32. Component structure
MetricCard, RiskBadge, DataTable (pagination/sort), ChartCard, FilterBar, Modal/Drawer, CustomerCard, TrajectoryChart, SimulatorControls, CampaignWizard, ExperimentTable, ChatBox, UploadBox, EmptyState/LoadingSpinner.

## 33. Database schema
See §13; full DDL in `backend/models.py`. Key: customers(id, tenant_id, name, age, income, tenure_months, region, segment, created_at), accounts(id,customer_id,balance,type), products(id,name,category), customer_products, transactions(id,customer_id,amount,ts,type), interactions(id,customer_id,kind[complaint|call|login_fail|visit], severity, resolved, ts), customer_features(customer_id, 16 feats, label), churn_predictions(customer_id, proba, band, trajectory JSON, ts), customer_values(customer_id, clv, annual_contrib), retention_recommendations(customer_id, action, cost, success, roi, reason), campaigns(...), campaign_targets(campaign_id, customer_id, group, reached, retained), experiments(...), experiment_results(...), audit_logs(tenant_id,user_id,action,meta,ts), users(id,tenant_id,email,hash,salt,role), tenants(id,name).

## 34. API endpoint specification
- POST /api/auth/register|/login|/logout|/me|/switch
- GET /api/dashboard/summary|/risk-dist|/revenue-by-segment|/product-risk|/risk-trend|/quadrant|/campaign-perf
- GET /api/customers + ?search&risk&segment&sort&page | GET /api/customers/{id} (360 aggregate)
- GET /api/predictions/metrics | POST /api/predictions/retrain | POST /api/predictions/predict/{id}
- GET /api/segments/overview | GET /api/segments/list?segment=
- GET /api/recommendations?priority= | GET /api/recommendations/{customer_id}
- POST /api/roi/simulate {filters,cost,success,reach} → outputs+scenarios
- CRUD /api/campaigns + POST /{id}/launch + GET /{id}/results
- GET /api/experiments + /{id}
- GET /api/analytics/products|/deterioration|/alerts
- POST /api/ai/ask {question}
- POST /api/data/upload (CSV) | GET /api/data/sample | GET /api/data/status
- GET /api/audit?limit=
Full request/response schemas in `backend/schemas.py` + live OpenAPI `/docs`.

## 35. Seed/demo data strategy
`backend/seed.py` (SEED=42, Faker-free stdlib+random): 2 tenants, users (admin/manager per tenant, password `demo123`), 600 customers with correlated archetypes (loyal 45% low risk, declining 25% high risk, volatile 15%, new 15%), accounts (1–3), 12mo transactions with trends, interactions/complaints correlated to risk, products (savings/current/cards/loan/insurance/investment), backfilled trajectory (90/60/30d), labels churned ~ proba>0.6 + noise. Campaign history (3 completed w/ results) + 1 draft. Deterministic re-runnable (`--reset`).

## 36. ML feature engineering strategy
16 features: tenure_months, age, income, avg_balance, balance_trend_pct, txn_freq_mo, avg_txn_value, txn_trend_pct, card_usage_ratio, product_count, has_loan, complaints_1y, avg_resolution_days, logins_mo, engagement_decline_pct, inactivity_days, failed_txn_rate. Trends = (last3m − prev3m)/prev3m. Engagement decline from logins+binary activity. All computed in `seed.py`+`services.compute_features()` identically (single function reused).

## 37. Model training/inference strategy
`python -m backend.ml.train` (or POST /predictions/retrain): stratified 80/20, scale numerics, LogReg baseline + XGB/HGB primary, pick primary by AUC, save artifacts. Inference `ml/infer.py:predict_proba(features)` loads artifacts or deterministic rule fallback (weighted sigmoid) if missing — app always runnable.

## 38. Model evaluation metrics
ROC-AUC (primary), precision, recall, F1 (threshold 0.5), confusion matrix, band distribution. Displayed on /risk. Target AUC ≥0.75 on synthetic data (typically ~0.85+ due to designed signal).

## 39. Security considerations
PBKDF2 hashing, JWT expiry, role+tenant checks, Pydantic validation, parameterized ORM (no raw SQL), CORS from env, no secrets in repo, error messages generic (no stack/PII leak), audit log for sensitive actions.

## 40. Privacy considerations
Synthetic data only; minimal PII (name/email-like strings clearly fake); AI context aggregates first; no real customer data; CSV upload stays in local DB; note in Settings that demo data is fictional.

## 41. Audit logging
`audit_logs` on login, register, simulate, campaign create/launch, upload, retrain, AI ask (question only). Viewable /settings + GET /api/audit.

## 42. Error handling
FastAPI handlers: 400 validation, 401 unauth, 403 forbidden/tenant, 404 not found, 500 generic. Frontend: loading skeletons, empty states ("no customers match filters"), error banners with retry. CSV errors list row+reason.

## 43. Observability
Stdout structured logs (uvicorn), `/api/health`, train metrics.json, audit table as event trail. No APM (out of scope).

## 44. Testing strategy
Backend pytest: ROI formulas (incl. edge cost=0), CLV/RaR math, priority/NBA rules, auth+tenant isolation, campaign simulation invariants (retained≤targeted, ROI math), API smoke (login→dashboard→customer→simulate→campaign→experiment). ML: feature fn determinism, predict range [0,1], metrics keys. Frontend: build (tsc) must pass. Run: `pytest backend/tests -q`.

## 45. Deployment architecture
Frontend Vercel (`frontend/`, `NEXT_PUBLIC_API_URL`), backend Render/Railway (`uvicorn backend.main:app`, `DATABASE_URL` Postgres), DB Supabase/Neon. Local: SQLite, `run.bat`/commands in SETUP.md. Docker: single `Dockerfile.backend` optional (kept minimal).

## 46. Environment variables
Backend: DATABASE_URL (default sqlite:///./retainiq.db), JWT_SECRET (default dev-only), CORS_ORIGINS, GEMINI_API_KEY / OPENAI_API_KEY (optional), SEED. Frontend: NEXT_PUBLIC_API_URL (default http://localhost:8000). See `.env.example`.

## 47. Folder structure
```
RetainIQ/
 FEATURES.md README.md ARCHITECTURE.md API.md SETUP.md DEMO.md .env.example
 backend/{main.py,database.py,models.py,schemas.py,services.py,seed.py,routes/*.py,ml/{train.py,infer.py,explain.py},tests/*.py} requirements.txt
 frontend/{app/**,components/**,lib/**,package.json}
 data/sample_customers.csv
```
Divergence from brief's sketch (§MINIMAL FILE STRUCTURE) is minor: routes split by domain + tests + artifacts — still small and explainable.

## 48. Hackathon demo flow (3 min, exact script in DEMO.md)
Login Demo Bank → Command Center ₹ revenue at risk → high-value/high-risk customer → why at risk → NBA → ROI simulator ₹10L budget + slider → campaign create+launch → control vs treatment lift+ROI → AI "How should we spend ₹10 lakh…?" → closing line.

## 49. Future enterprise features
Real core-banking connectors, real offer fulfillment, scheduler/retraining, Postgres RLS, SSO/SCIM, feature store, champion/challenger models, uplift modeling, multi-currency, PII vault.

## 50. Acceptance criteria (per major feature)
- Start/seed/login/dashboard/360/predict/explain/CLV/RaR/NBA/simulator/campaign/experiment/AI/tenancy/docs/tests all work; no placeholder buttons/TODOs; metrics from DB; ROI centralized+tested; predictions labeled; `/docs` live; `.env.example` present; runnable from documented commands.

## HACKATHON PRIORITY
- P0 (required — all built): auth, command center, customer 360, churn ML + metrics, SHAP-style explain, CLV, RaR, prioritization, NBA, ROI simulator + sensitivity, campaigns + simulated execution, experiments + lift, AI analyst (+fallback).
- P1 (important — all built, simplified): trajectory, deterioration score, segment quadrants, product analytics, alerts, audit log, CSV upload + sample, demo seed + 2 tenants.
- P2 (optional — deferred, listed as future): SSO, schedulers, RLS, model registry, vector RAG, mobile, multi-currency.
