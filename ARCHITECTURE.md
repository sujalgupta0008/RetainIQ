# ARCHITECTURE.md

```
Browser (Next.js 14, App Router, client components, Recharts)
   │  REST JSON + JWT Bearer   (NEXT_PUBLIC_API_URL)
   ▼
FastAPI (backend/main.py) — thin routes/* → services.py (domain fns) → SQLAlchemy models
   │                                   ├── ml/infer.py (artifacts or rule fallback)
   │                                   └── analyst (LLM provider or deterministic)
   ▼
SQLite file retainiq.db  ──or──  Postgres via DATABASE_URL (same SQLAlchemy code)
Artifacts: backend/ml/artifacts/{model,baseline,scaler,features,metrics}.pkl/json
```

- **No** microservices/workers/Redis/Kafka/GraphQL/vector DB. One backend process serves API + inference.
- **Tenancy:** `tenant_id` on every business table; extracted from JWT server-side; all queries filtered.
- **Auth:** PBKDF2-HMAC-SHA256 + per-user salt; JWT HS256 24h (`sub` = string user id); roles admin/manager/analyst/viewer.
- **Money math** centralized in `services.calc_roi / calc_clv / calc_rar` (unit-tested).
- **Experiments:** per-campaign 80/20 split (seeded RNG), Bernoulli outcomes from expected vs 15% base success.
- **AI:** intent router → DB aggregate tools → context JSON → Gemini/OpenAI if keys set, else templates.
- **Frontend:** `lib/api.ts` fetch wrapper (auto logout on 401), `components/ui.tsx` kit, 15 routes.
