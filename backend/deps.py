"""Shared auth dependencies."""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import get_db
from . import models as M
from .services import decode_token

sec = HTTPBearer(auto_error=False)

def current_user(creds: HTTPAuthorizationCredentials = Depends(sec), db: Session = Depends(get_db)):
    if not creds: raise HTTPException(401, "Not authenticated")
    try: p = decode_token(creds.credentials)
    except Exception: raise HTTPException(401, "Invalid token")
    u = db.query(M.User).filter_by(id=int(p["sub"])).first()
    if not u: raise HTTPException(401, "User not found")
    return u

def tenant_id(u=Depends(current_user)) -> int:
    return u.tenant_id

def require_role(*roles):
    def f(u=Depends(current_user)):
        if u.role not in roles and u.role != "admin":
            raise HTTPException(403, "Forbidden")
        return u
    return f
