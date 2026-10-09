from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models as M
from ..deps import current_user

r = APIRouter(prefix="/api/audit", tags=["audit"])


@r.get("")
def logs(limit: int = Query(default=50, ge=1, le=200), user: M.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(M.AuditLog).filter_by(tenant_id=user.tenant_id).order_by(M.AuditLog.id.desc()).limit(limit).all()
    return [{"action": entry.action, "meta": entry.meta, "ts": str(entry.ts)} for entry in rows]
