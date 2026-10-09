import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models as M, schemas as S
from ..deps import current_user, require_role, rate_limit
from ..services import hash_pw, make_token, audit

r = APIRouter(prefix="/api/auth", tags=["auth"])

# Non-admin self-registration may only create these roles; 'admin' is never granted
# via open registration (schemas.RegisterIn also clamps, this is defense-in-depth).
SELF_SERVE_ROLES = {"manager", "analyst", "viewer"}


@r.post("/register", dependencies=[Depends(rate_limit(20, 60))])
def register(body: S.RegisterIn, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    tenant_name = (body.tenant or "Demo Bank").strip()[:100] or "Demo Bank"
    # Defense-in-depth: never honor an admin role from open registration.
    role = body.role if body.role in SELF_SERVE_ROLES else "manager"
    tenant = db.query(M.Tenant).filter_by(name=tenant_name).first()
    if not tenant:
        tenant = M.Tenant(name=tenant_name)
        db.add(tenant)
        db.flush()
    if db.query(M.User).filter_by(tenant_id=tenant.id, email=email).first():
        raise HTTPException(400, "Email already registered")
    salt = secrets.token_hex(8)
    user = M.User(tenant_id=tenant.id, email=email, salt=salt, pw_hash=hash_pw(body.password, salt), role=role)
    db.add(user)
    db.commit()
    # Audit stores the email (account lifecycle event); truncated, per-tenant visible.
    audit(db, tenant.id, user.id, "register", email[:120])
    db.commit()
    return {"token": make_token(user.id, tenant.id, user.role), "tenant": tenant.name, "tenant_id": tenant.id, "role": user.role, "email": user.email}


@r.post("/login", dependencies=[Depends(rate_limit(30, 60))])
def login(body: S.LoginIn, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    # NOTE: global email lookup is a demo simplification; production tenants should
    # scope login by tenant/organization identifier to avoid cross-tenant enumeration.
    user = db.query(M.User).filter_by(email=email).first()
    # Constant-shape failure: don't reveal whether the email exists.
    if not user or user.pw_hash != hash_pw(body.password, user.salt):
        raise HTTPException(401, "Invalid credentials")
    tenant = db.query(M.Tenant).filter_by(id=user.tenant_id).first()
    audit(db, user.tenant_id, user.id, "login", email[:120])
    db.commit()
    return {"token": make_token(user.id, user.tenant_id, user.role), "tenant": tenant.name if tenant else "",
            "tenant_id": user.tenant_id, "role": user.role, "email": user.email}


@r.get("/me")
def me(user: M.User = Depends(current_user), db: Session = Depends(get_db)):
    tenant = db.query(M.Tenant).filter_by(id=user.tenant_id).first()
    tenants = [{"id": x.id, "name": x.name} for x in db.query(M.Tenant).all()] if user.role == "admin" else []
    return {"email": user.email, "role": user.role, "tenant_id": user.tenant_id,
            "tenant": tenant.name if tenant else "", "all_tenants": tenants}


@r.post("/switch")
def switch(tenant_id: int, user: M.User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    # FIX (S01): previously ANY authenticated user could jump to ANY tenant id, and the
    # switch permanently rewrote users.tenant_id. Now admin-only; production should use a
    # membership table + session-scoped switch instead of mutating the user row.
    if tenant_id <= 0:
        raise HTTPException(400, "Invalid tenant")
    tenant = db.query(M.Tenant).filter_by(id=tenant_id).first()
    if not tenant:
        raise HTTPException(404, "Tenant not found")
    user.tenant_id = tenant_id
    db.commit()
    audit(db, tenant_id, user.id, "tenant_switch", tenant.name[:120])
    db.commit()
    return {"token": make_token(user.id, tenant_id, user.role), "tenant": tenant.name, "tenant_id": tenant_id}
