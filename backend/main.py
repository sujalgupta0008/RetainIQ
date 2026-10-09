"""RetainIQ backend entrypoint. Run: uvicorn backend.main:app --reload"""
import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from .database import engine, Base
from . import models  # noqa: F401 -- import registers tables on Base.metadata

log = logging.getLogger("retainiq")

Base.metadata.create_all(engine)
app = FastAPI(title="RetainIQ API", version="1.0.0",
              description="Retention & ROI intelligence — predictions are estimates, not financial guarantees.")

# FIX (S03): fail-loud on default JWT secret in production. Tests/dev keep the fallback
# with a warning so the suite runs without env setup.
_JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")  # nosec: B105 - dev-only fallback; prod refuses to start (see below)
if _JWT_SECRET == "dev-secret-change-me":  # nosec: B105 - comparing against dev default to refuse prod start
    if os.getenv("RETAINIQ_ENV", "dev").lower().startswith("prod"):
        raise RuntimeError("REFUSING TO START: set a strong JWT_SECRET in production")
    log.warning("JWT_SECRET is the dev default — set a long random value via env (see .env.example)")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Minimal security headers for API responses (S10)."""
    async def dispatch(self, request, call_next):
        resp = await call_next(request)
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        # API serves JSON only; lock down framing/plugins. No inline scripts served here.
        resp.headers.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
        return resp


app.add_middleware(SecurityHeadersMiddleware)

origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins,
                   allow_credentials=True,
                   # FIX (S10): explicit method/header allow-list instead of ["*"] so a
                   # misconfigured CORS_ORIGINS can't silently open the API surface.
                   allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                   allow_headers=["Authorization", "Content-Type", "Accept"],
                   max_age=600)

from .routes import auth, dashboard, customers, predictions, segments, recommendations, roi, campaigns, experiments, analytics, ai, data, audit
for mod in [auth, dashboard, customers, predictions, segments, recommendations, roi, campaigns, experiments, analytics, ai, data, audit]:
    app.include_router(mod.r)


@app.get("/api/health")
def health():
    return {"ok": True, "service": "retainiq"}


@app.get("/")
def root():
    return {"service": "retainiq", "docs": "/docs"}
