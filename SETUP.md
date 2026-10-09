# SETUP.md — run RetainIQ locally

## Prereqs
- Python 3.11+ · Node 18+ · npm
- No database server needed (SQLite file `retainiq.db` is created automatically)

## 1. Backend
```powershell
pip install -r backend/requirements.txt
copy .env.example .env        # optional; defaults work as-is
python -m backend.seed --reset
python -m backend.ml.train
python -m uvicorn backend.main:app --reload --port 8000
```
- API: http://localhost:8000 · OpenAPI docs: http://localhost:8000/docs · health: `/api/health`

## 2. Frontend
```powershell
cd frontend
copy .env.example .env.local  # optional; default API URL is http://localhost:8000
npm install
npm run dev                   # http://localhost:3000  (or `npm run build; npm run start` for prod)
```

## 3. Demo accounts (password `demo123`)
| Email | Tenant | Role |
|---|---|---|
| admin@demobank.in | Demo Bank (400 customers) | admin |
| manager@demobank.in | Demo Bank | manager |
| admin@demofintech.in | Demo Fintech (200 customers) | admin |
| manager@demofintech.in | Demo Fintech | manager |

## 4. Environment variables
| Var | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./retainiq.db` | Set to Postgres URL for Supabase/Neon/Render |
| `JWT_SECRET` | dev-only | Change in production |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated frontend origins |
| `GEMINI_API_KEY` / `OPENAI_API_KEY` | empty | Optional — AI Analyst uses deterministic fallback without them |
| `SEED` | `42` | Deterministic seed data + experiments |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Frontend → backend URL |

## 5. Postgres switch (deploy)
```powershell
$env:DATABASE_URL = "postgresql+psycopg2://user:pass@host:5432/retainiq"
# add psycopg2-binary to requirements, then seed + run as above
```
Tables auto-create on startup (`Base.metadata.create_all`). Frontend deploys to Vercel with
`NEXT_PUBLIC_API_URL` pointing at the backend (Render/Railway).

## 6. Useful commands
```powershell
python -m pytest backend/tests/test_services.py -q   # unit tests
python -m backend.tests.test_api                      # full smoke test
python -m backend.ml.train                            # retrain (also via UI: Data → Retrain)
```
