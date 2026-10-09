from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from .. import models as M
from ..deps import current_user
from ..services import deterioration

r = APIRouter(prefix="/api/analytics", tags=["analytics"])

@r.get("/products")
def products(u: M.User = Depends(current_user), db: Session = Depends(get_db)):
    from .dashboard import prod_risk
    return prod_risk(u, db)

@r.get("/deterioration")
def det(u: M.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(M.Customer, M.CustomerFeature, M.ChurnPrediction).join(
        M.CustomerFeature, M.CustomerFeature.customer_id == M.Customer.id).join(
        M.ChurnPrediction, M.ChurnPrediction.customer_id == M.Customer.id).filter(
        M.Customer.tenant_id == u.tenant_id).all()
    out = []
    for c, f, p in rows:
        s, flags = deterioration(f.f)
        if s >= 30:
            out.append({"id": c.id, "name": c.name, "score": s, "flags": flags, "proba": p.proba})
    return sorted(out, key=lambda x: -x["score"])[:50]

@r.get("/alerts")
def alerts(u: M.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(M.Customer, M.ChurnPrediction, M.CustomerValue).join(
        M.ChurnPrediction, M.ChurnPrediction.customer_id == M.Customer.id).join(
        M.CustomerValue, M.CustomerValue.customer_id == M.Customer.id).filter(
        M.Customer.tenant_id == u.tenant_id).all()
    a = []
    for c, p, v in rows:
        tr = (p.trajectory or {})
        spike = tr.get("today", 0) - tr.get("d30", 0)
        if spike >= 0.15:
            a.append({"type": "risk_spike", "customer": c.name, "id": c.id,
                      "msg": f"Churn risk spiked {spike:.0%} in 30 days (now {p.proba:.0%})"})
        if p.proba >= 0.6 and v.clv >= 150000:
            a.append({"type": "danger_zone", "customer": c.name, "id": c.id,
                      "msg": f"High-value customer in danger zone — RaR ₹{v.revenue_at_risk:,.0f}"})
    res = db.query(M.ExperimentResult).filter_by(tenant_id=u.tenant_id).all()
    for x in res:
        if x.roi is not None and x.roi < 0.2:
            a.append({"type": "low_roi", "customer": "", "id": None,
                      "msg": f"Experiment {x.experiment_id} ROI below threshold ({x.roi:.0%})"})
    return a[:30]
