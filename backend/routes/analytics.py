from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models as M
from ..deps import current_user
from ..services import deterioration, product_risk_rows

r = APIRouter(prefix="/api/analytics", tags=["analytics"])

@r.get("/products")
def products(user: M.User = Depends(current_user), db: Session = Depends(get_db)):
    return product_risk_rows(db, user.tenant_id)

@r.get("/deterioration")
def deterioration_list(user: M.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(M.Customer, M.CustomerFeature, M.ChurnPrediction).join(
        M.CustomerFeature, M.CustomerFeature.customer_id == M.Customer.id).join(
        M.ChurnPrediction, M.ChurnPrediction.customer_id == M.Customer.id).filter(
        M.Customer.tenant_id == user.tenant_id).all()
    out = []
    for cust, feats, pred in rows:
        score, flags = deterioration(feats.f)
        if score >= 30:
            out.append({"id": cust.id, "name": cust.name, "score": score, "flags": flags, "proba": pred.proba})
    return sorted(out, key=lambda x: -x["score"])[:50]

@r.get("/alerts")
def alerts(user: M.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(M.Customer, M.ChurnPrediction, M.CustomerValue).join(
        M.ChurnPrediction, M.ChurnPrediction.customer_id == M.Customer.id).join(
        M.CustomerValue, M.CustomerValue.customer_id == M.Customer.id).filter(
        M.Customer.tenant_id == user.tenant_id).all()
    found = []
    for cust, pred, val in rows:
        traj = (pred.trajectory or {})
        spike = traj.get("today", 0) - traj.get("d30", 0)
        if spike >= 0.15:
            found.append({"type": "risk_spike", "customer": cust.name, "id": cust.id,
                      "msg": f"Churn risk spiked {spike:.0%} in 30 days (now {pred.proba:.0%})"})
        if pred.proba >= 0.6 and val.clv >= 150000:
            found.append({"type": "danger_zone", "customer": cust.name, "id": cust.id,
                      "msg": f"High-value customer in danger zone — RaR ₹{val.revenue_at_risk:,.0f}"})
    results = db.query(M.ExperimentResult).filter_by(tenant_id=user.tenant_id).all()
    for res in results:
        if res.roi is not None and res.roi < 0.2:
            found.append({"type": "low_roi", "customer": "", "id": None,
                      "msg": f"Experiment {res.experiment_id} ROI below threshold ({res.roi:.0%})"})
    return found[:30]
