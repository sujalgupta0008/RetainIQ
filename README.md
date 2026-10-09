# RetainIQ — AI-Powered Customer Retention & ROI Intelligence Platform

> "Who should we save, what should we do, how much should we spend, and will it be profitable?"

RetainIQ helps banks & fintechs identify high-value customers at risk, understand **why**,
choose the **next best action**, predict **financial impact** with the hero **Retention ROI
Simulator**, and **measure actual ROI** via campaign A/B experiments — closing the loop:
`DETECT → EXPLAIN → PRIORITIZE → DECIDE → SIMULATE → ACT → MEASURE → LEARN`.

- **Frontend:** Next.js 14 + TypeScript + Tailwind + Recharts + lucide-react
- **Backend:** FastAPI + Pydantic + SQLAlchemy (SQLite by default, Postgres via `DATABASE_URL`)
- **ML:** Scikit-learn + XGBoost (auto-fallback to HistGradientBoosting) — AUC **0.91** on seeded data
- **AI:** Provider abstraction (Gemini / OpenAI-compatible) + deterministic analytics fallback (works with no keys)

## Quickstart (2 terminals)

```powershell
# 1) Backend
pip install -r backend/requirements.txt
python -m backend.seed --reset        # realistic synthetic data: Demo Bank (400) + Demo Fintech (200)
python -m backend.ml.train             # train churn model -> backend/ml/artifacts/
python -m uvicorn backend.main:app --reload --port 8000   # API + docs at http://localhost:8000/docs

# 2) Frontend
cd frontend; npm install; npm run dev  # app at http://localhost:3000
```

Demo login: **admin@demobank.in / demo123** (or one-click 🏦 Demo Bank / 💳 Demo Fintech on the login page).

## Features
Executive Command Center (12 live metrics) · Customer 360 + risk trajectory · Churn prediction
(AUC/precision/recall/F1/confusion matrix) · Plain-language explanations from real behavior deltas ·
CLV + revenue-at-risk (`proba × CLV`) · Priority scoring (Critical/High/Monitor/Low) ·
Next-best-action (8 interventions, cost/success/ROI) · **ROI Simulator with sliders + sensitivity
scenarios** · Campaign Studio (projected ROI → launch → 80/20 A/B simulated execution) ·
Experiment lift/revenue/ROI · AI Analyst grounded in real aggregates · CSV upload + sample ·
Audit log · Multi-tenant demo · Alerts · Deterioration score · Product/segment analytics.

All money figures are labeled **estimated / predicted / realized** — predictions are never
presented as financial outcomes.

## Docs
- `FEATURES.md` — source of truth (50 sections incl. formulas, schema, endpoints)
- `SETUP.md` — install, env vars, Postgres switch
- `DEMO.md` — exact 3-minute hackathon script
- `ARCHITECTURE.md` — system design · `API.md` — endpoint reference

## Tests
```powershell
python -m pytest backend/tests/test_services.py -q   # ROI/CLV/NBA/explain unit tests
python -m backend.tests.test_api                      # end-to-end smoke: login→dashboard→customer→simulate→campaign→experiment→AI
```
