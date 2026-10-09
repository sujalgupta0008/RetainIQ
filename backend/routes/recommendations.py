from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models as M
from ..deps import current_user

r = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@r.get("")
def all_recs(priority: str = Query(default="", max_length=30), limit: int = Query(default=100, ge=1, le=500),
             user: M.User = Depends(current_user), db: Session = Depends(get_db)):
    q = db.query(M.Customer, M.ChurnPrediction, M.CustomerValue, M.Recommendation).join(
        M.ChurnPrediction, M.ChurnPrediction.customer_id == M.Customer.id).join(
        M.CustomerValue, M.CustomerValue.customer_id == M.Customer.id).join(
        M.Recommendation, M.Recommendation.customer_id == M.Customer.id).filter(
        M.Customer.tenant_id == user.tenant_id)
    if priority: q = q.filter(M.Recommendation.priority == priority)
    rows = q.all()
    rows.sort(key=lambda x: -x[3].priority_score)
    return [{"customer_id": c.id, "name": c.name, "segment": c.segment, "proba": p.proba,
        "clv": v.clv, "rar": v.revenue_at_risk, "action": rec.action, "cost": rec.cost,
        "success": rec.success, "roi": rec.expected_roi, "reason": rec.reason,
        "priority": rec.priority, "score": rec.priority_score} for c, p, v, rec in rows[:limit]]
