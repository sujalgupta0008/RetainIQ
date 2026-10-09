# API.md — endpoint reference (live interactive docs at `/docs`)

Auth: `Authorization: Bearer <JWT>` on all non-auth routes. Pagination: `?page&page_size`. Errors: `{detail}`.

| Method | Path | Description |
|---|---|---|
| POST | /api/auth/register | Register (email, password, tenant?, role) → JWT |
| POST | /api/auth/login | Login → JWT + tenant |
| GET | /api/auth/me | Current user + tenant |
| POST | /api/auth/switch?tenant_id= | Demo tenant switch → new JWT |
| GET | /api/health | Health check |
| GET | /api/dashboard/summary | 12 command-center metrics |
| GET | /api/dashboard/risk-dist | Risk band counts |
| GET | /api/dashboard/revenue-by-segment | RaR per segment |
| GET | /api/dashboard/product-risk | Customers/high-risk/RaR per product |
| GET | /api/dashboard/risk-trend | Avg risk d90/d60/d30/today |
| GET | /api/dashboard/quadrant | Value×risk counts + median CLV |
| GET | /api/dashboard/campaign-perf | Campaign revenue/lift/ROI |
| GET | /api/customers?search&risk&segment&sort&page | Ranked customer list |
| GET | /api/customers/{id} | Full 360 (profile, trajectory, drivers, NBA, deterioration) |
| GET | /api/predictions/metrics | AUC/precision/recall/F1/confusion |
| POST | /api/predictions/retrain | Retrain + refresh predictions (manager+) |
| GET | /api/segments/overview | 4 value×risk quadrants |
| GET | /api/recommendations?priority&limit | NBA queue by priority score |
| POST | /api/roi/simulate | {min_proba,min_clv,segment,cost,success,reach} → outputs + 3 scenarios |
| GET/POST | /api/campaigns | List / create (returns projected ROI) |
| GET | /api/campaigns/{id} | Detail + experiment results |
| POST | /api/campaigns/{id}/launch | 80/20 split + simulated outcomes |
| GET | /api/experiments, /api/experiments/{id} | Lift/revenue/cost/ROI |
| GET | /api/analytics/products, /deterioration, /alerts | Product risk, top deteriorating, alerts |
| GET | /api/ai/suggested | 5 canonical questions |
| POST | /api/ai/ask | {question} → grounded answer |
| POST | /api/data/upload | CSV upload (validated) |
| GET | /api/data/sample | Sample CSV |
| GET | /api/data/status | Counts |
| GET | /api/audit?limit | Audit trail |
