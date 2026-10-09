from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models as M, schemas as S
from ..deps import current_user
from ..services import hash_pw, make_token, audit
import secrets

r = APIRouter(prefix="/api/auth", tags=["auth"])

@r.post("/register")
def register(b: S.RegisterIn, db: Session = Depends(get_db)):
    t = db.query(M.Tenant).filter_by(name=b.tenant or "Demo Bank").first()
    if not t:
        t = M.Tenant(name=b.tenant or "Demo Bank"); db.add(t); db.flush()
    if db.query(M.User).filter_by(tenant_id=t.id, email=b.email).first():
        raise HTTPException(400, "Email already registered")
    salt = secrets.token_hex(8)
    u = M.User(tenant_id=t.id, email=b.email, salt=salt, pw_hash=hash_pw(b.password, salt), role=b.role)
    db.add(u); db.commit()
    audit(db, t.id, u.id, "register", b.email); db.commit()
    return {"token": make_token(u.id, t.id, u.role), "tenant": t.name, "tenant_id": t.id, "role": u.role, "email": u.email}

@r.post("/login")
def login(b: S.LoginIn, db: Session = Depends(get_db)):
    u = db.query(M.User).filter_by(email=b.email).first()
    if not u or u.pw_hash != hash_pw(b.password, u.salt):
        raise HTTPException(401, "Invalid credentials")
    t = db.query(M.Tenant).filter_by(id=u.tenant_id).first()
    audit(db, u.tenant_id, u.id, "login", b.email); db.commit()
    return {"token": make_token(u.id, u.tenant_id, u.role), "tenant": t.name if t else "",
            "tenant_id": u.tenant_id, "role": u.role, "email": u.email}

@r.get("/me")
def me(u: M.User = Depends(current_user), db: Session = Depends(get_db)):
    t = db.query(M.Tenant).filter_by(id=u.tenant_id).first()
    tenants = [{"id": x.id, "name": x.name} for x in db.query(M.Tenant).all()] if u.role == "admin" else []
    return {"email": u.email, "role": u.role, "tenant_id": u.tenant_id,
            "tenant": t.name if t else "", "all_tenants": tenants}

@r.post("/switch")
def switch(tenant_id: int, u: M.User = Depends(current_user), db: Session = Depends(get_db)):
    t = db.query(M.Tenant).filter_by(id=tenant_id).first()
    if not t: raise HTTPException(404, "Tenant not found")
    # demo convenience: allow switch (still logged); production would check membership
    u.tenant_id = tenant_id
    db.commit()
    audit(db, tenant_id, u.id, "tenant_switch", t.name); db.commit()
    return {"token": make_token(u.id, tenant_id, u.role), "tenant": t.name, "tenant_id": tenant_id}
