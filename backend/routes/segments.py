import statistics

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models as M
from ..deps import current_user

r = APIRouter(prefix="/api/segments", tags=["segments"])

@r.get("/overview")
def overview(user: M.User = Depends(current_user), db: Session = Depends(get_db)):
    tid = user.tenant_id
    clvs = [v.clv for v in db.query(M.CustomerValue).filter_by(tenant_id=tid).all()]
    median = statistics.median(clvs) if clvs else 50000
    rows = db.query(M.Customer, M.ChurnPrediction, M.CustomerValue).join(
        M.ChurnPrediction, M.ChurnPrediction.customer_id == M.Customer.id).join(
        M.CustomerValue, M.CustomerValue.customer_id == M.Customer.id).filter(
        M.Customer.tenant_id == tid).all()
    segs = {}
    for cust, pred, val in rows:
        high_value = val.clv >= median; high_risk = pred.proba >= 0.5
        key = "High Value / High Risk" if high_value and high_risk else ("High Value / Low Risk" if high_value else ("Low Value / High Risk" if high_risk else "Low Value / Low Risk"))
        seg = segs.setdefault(key, {"segment": key, "count": 0, "rar": 0, "avg_proba": []})
        seg["count"] += 1; seg["rar"] += val.revenue_at_risk; seg["avg_proba"].append(pred.proba)
    out = []
    for seg in segs.values():
        seg["rar"] = round(seg["rar"], 2)
        seg["avg_proba"] = round(sum(seg["avg_proba"])/max(1, len(seg["avg_proba"])), 3)
        out.append(seg)
    return {"median_clv": round(median, 2), "segments": sorted(out, key=lambda x: -x["rar"])}
