"""RetainIQ backend entrypoint. Run: uvicorn backend.main:app --reload"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from . import models  # noqa: register tables

Base.metadata.create_all(engine)
app = FastAPI(title="RetainIQ API", version="1.0.0",
              description="Retention & ROI intelligence — predictions are estimates, not financial guarantees.")

origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in origins],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

from .routes import auth, dashboard, customers, predictions, segments, recommendations, roi, campaigns, experiments, analytics, ai, data, audit
for mod in [auth, dashboard, customers, predictions, segments, recommendations, roi, campaigns, experiments, analytics, ai, data, audit]:
    app.include_router(mod.r)

@app.get("/api/health")
def health():
    return {"ok": True, "service": "retainiq"}

@app.get("/")
def root():
    return {"service": "retainiq", "docs": "/docs"}
