# RetainIQ

I built RetainIQ to answer four plain questions about customer churn: who might leave,
why, what to do about it, and whether the fix is worth the money. It runs on demo
data (a fake bank with 400 customers and a fake fintech with 200), so you can try
everything without keys or a database server.

What it does:
- Dashboard with live counts, revenue at risk, and campaign results.
- Customer list ranked by revenue at risk, plus a 360 view per customer (risk,
  plain-English drivers, trajectory, recommended action with cost/success).
- ROI simulator: pick an audience and success assumptions, see projected return
  and conservative/expected/optimistic scenarios.
- Campaigns: define an audience, see projected ROI, launch an 80/20
  treatment/control test with simulated outcomes, then compare experiments.
- AI analyst that answers questions from live database aggregates (works with
  no API key; uses Gemini/OpenAI only if you set a key).
- CSV upload (banking sample or IBM Telco format) + retrain from the Data page.

All money figures are labeled estimated, predicted, or realized. Model outputs
are estimates; only experiment outcomes are called realized.

## How to run it

You need Python 3.11+ and Node 18+. Two terminals:

```powershell
# 1) Backend
pip install -r backend/requirements.txt
python -m backend.seed --reset
python -m backend.ml.train
python -m uvicorn backend.main:app --reload --port 8000
# API + interactive docs: http://localhost:8000/docs

# 2) Frontend
cd frontend; npm install; npm run dev
# App: http://localhost:3000
```

Log in with `admin@demobank.in / demo123` (or the one-click demo buttons on
the login page). The `.env.example` file lists the optional settings
(`DATABASE_URL` for Postgres, `JWT_SECRET`, `GEMINI_API_KEY`/`OPENAI_API_KEY`).

## Folder layout

- `backend/` — FastAPI app: `routes/` (thin HTTP), `services.py` (domain logic),
  `models.py`/`schemas.py`/`database.py`, `seed.py` (demo data),
  `ml/` (train/infer + rule fallback), `csv_import.py`, `tests/`.
- `frontend/` — Next.js 14 app: `app/` (one folder per page),
  `lib/api.ts` (fetch wrapper), `lib/format.ts` (INR formatting),
  `components/ui.tsx` (shared cards/badges/buttons).
- `.env.example` — every setting with its default (`DATABASE_URL`,
  `JWT_SECRET`, `GEMINI_API_KEY`/`OPENAI_API_KEY`, ...). Live endpoint
  reference: http://localhost:8000/docs.

## Results

Honest version: everything runs on synthetic data, so treat the numbers as a
working demo, not a benchmark. After `python -m backend.ml.train`, the Risk
page shows the real AUC/precision/recall/F1 and confusion matrix for whatever
data is in the database. The ROI simulator and analyst always label their
numbers as estimates.

## Tests

```powershell
python -m pytest backend/tests/ -q
python -m backend.tests.test_api   # end-to-end smoke through the main flow
```
