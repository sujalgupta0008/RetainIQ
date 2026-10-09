"""Shared auth dependencies."""
import time
from collections import defaultdict
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import get_db
from . import models as M
from .services import decode_token

sec = HTTPBearer(auto_error=False)

# Simple in-process rate limiter (per client IP + endpoint). Not distributed-safe,
# but prevents trivial brute-force/abuse on a single instance without extra deps.
# Production with multiple workers should use Redis-backed limiting.
_hits: dict[str, list[float]] = defaultdict(list)


def rate_limit(max_calls: int, window_s: int = 60):
    def _check(request: Request):
        key = f"{request.client.host if request.client else 'unknown'}:{request.url.path}:{max_calls}"
        now = time.monotonic()
        calls = [t for t in _hits[key] if now - t < window_s]
        if len(calls) >= max_calls:
            raise HTTPException(429, "Too many requests, please slow down")
        calls.append(now)
        _hits[key] = calls
        # Opportunistic cleanup to bound memory.
        if len(_hits) > 10000:
            _hits.clear()
    return _check


def current_user(creds: HTTPAuthorizationCredentials = Depends(sec), db: Session = Depends(get_db)):
    if not creds:
        raise HTTPException(401, "Not authenticated")
    try:
        payload = decode_token(creds.credentials)
    except Exception:
        raise HTTPException(401, "Invalid token")
    try:
        uid = int(payload.get("sub", ""))
    except (TypeError, ValueError):
        raise HTTPException(401, "Invalid token")
    user = db.query(M.User).filter_by(id=uid).first()
    if not user:
        raise HTTPException(401, "User not found")
    return user


def require_role(*roles):
    def check(user=Depends(current_user)):
        if user.role not in roles and user.role != "admin":
            raise HTTPException(403, "Forbidden")
        return user
    return check
