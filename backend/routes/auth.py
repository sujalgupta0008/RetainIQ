from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models as M, schemas as S
from ..deps import current_user, require_role, rate_limit
from ..services import hash_pw, make_token, audit
import secrets

r = APIRouter(prefix="/api/auth", tags=["auth"])

# Non-admin self-registration may only create these roles; 'admin' is never granted
# via open registration (schemas.RegisterIn also clamps, this is defense-in-depth).
SELF_SERVE_ROLES = {"manager", "analyst", "viewer"}


@r.post("/register", dependencies=[Depends(rate_limit(20, 60))])
def register(b: S.RegisterIn, db: Session = Depends(get_db)):
    email = b.email.strip().lower()
    tenant_name = (b.tenant or "Demo Bank").strip()[:100] or "Demo Bank"
    # Defense-in-depth: never honor an admin role from open registration.
    role = b.role if b.role in SELF_SERVE_ROLES else "manager"
    t = db.query(M.Tenant).filter_by(name=tenant_name).first()
    if not t:
        t = M.Tenant(name=tenant_name)
        db.add(t)
        db.flush()
    if db.query(M.User).filter_by(tenant_id=t.id, email=email).first():
        raise HTTPException(400, "Email already registered")
    salt = secrets.token_hex(8)
    u = M.User(tenant_id=t.id, email=email, salt=salt, pw_hash=hash_pw(b.password, salt), role=role)
    db.add(u)
    db.commit()
    # Audit stores the email (account lifecycle event); truncated, per-tenant visible.
    audit(db, t.id, u.id, "register", email[:120])
    db.commit()
    return {"token": make_token(u.id, t.id, u.role), "tenant": t.name, "tenant_id": t.id, "role": u.role, "email": u.email}


@r.post("/login", dependencies=[Depends(rate_limit(30, 60))])
def login(b: S.LoginIn, db: Session = Depends(get_db)):
    email = b.email.strip().lower()
    # NOTE: global email lookup is a demo simplification; production tenants should
    # scope login by tenant/organization identifier to avoid cross-tenant enumeration.
    u = db.query(M.User).filter_by(email=email).first()
    # Constant-shape failure: don't reveal whether the email exists.
    if not u or u.pw_hash != hash_pw(b.password, u.salt):
        raise HTTPException(401, "Invalid credentials")
    t = db.query(M.Tenant).filter_by(id=u.tenant_id).first()
    audit(db, u.tenant_id, u.id, "login", email[:120])
    db.commit()
    return {"token": make_token(u.id, u.tenant_id, u.role), "tenant": t.name if t else "",
            "tenant_id": u.tenant_id, "role": u.role, "email": u.email}


@r.get("/me")
def me(u: M.User = Depends(current_user), db: Session = Depends(get_db)):
    t = db.query(M.Tenant).filter_by(id=u.tenant_id).first()
    tenants = [{"id": x.id, "name": x.name} for x in db.query(M.Tenant).all()] if u.role == "admin" else []
    return {"email": u.email, "role": u.role, "tenant_id": u.tenant_id,
            "tenant": t.name if t else "", "all_tenants": tenants}


@r.post("/switch")
def switch(tenant_id: int, u: M.User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    # FIX (S01): previously ANY authenticated user could jump to ANY tenant id, and the
    # switch permanently rewrote users.tenant_id. Now admin-only; production should use a
    # membership table + session-scoped switch instead of mutating the user row.
    if tenant_id <= 0:
        raise HTTPException(400, "Invalid tenant")
    t = db.query(M.Tenant).filter_by(id=tenant_id).first()
    if not t:
        raise HTTPException(404, "Tenant not found")
    u.tenant_id = tenant_id
    db.commit()
    audit(db, tenant_id, u.id, "tenant_switch", t.name[:120])
    db.commit()
    return {"token": make_token(u.id, tenant_id, u.role), "tenant": t.name, "tenant_id": tenant_id}
