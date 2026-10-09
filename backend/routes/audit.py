from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models as M
from ..deps import current_user

r = APIRouter(prefix="/api/audit", tags=["audit"])

@r.get("")
def logs(limit: int = 50, u: M.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(M.AuditLog).filter_by(tenant_id=u.tenant_id).order_by(M.AuditLog.id.desc()).limit(limit).all()
    return [{"action": x.action, "meta": x.meta, "ts": str(x.ts)} for x in rows]
