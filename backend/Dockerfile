FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend ./backend
COPY .env.example ./.env.example

# SQLite default lives at /app/retainiq.db; mount a volume to persist it.
# For Postgres, set DATABASE_URL=postgresql+psycopg2://... at runtime.
ENV DATABASE_URL=sqlite:///./retainiq.db \
    RETAINIQ_ENV=prod \
    PORT=8000

EXPOSE 8000

# Idempotent seed (skips when tenants exist) then serve. Train artifacts are
# optional: the app falls back to the rule model when metrics.json is absent.
CMD sh -c "python -m backend.seed; python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"
