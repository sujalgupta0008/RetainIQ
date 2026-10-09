from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from .. import models as M
from ..deps import current_user

r = APIRouter(prefix="/api/segments", tags=["segments"])

@r.get("/overview")
def overview(u: M.User = Depends(current_user), db: Session = Depends(get_db)):
    t = u.tenant_id
    import statistics
    clvs = [v.clv for v in db.query(M.CustomerValue).filter_by(tenant_id=t).all()]
    med = statistics.median(clvs) if clvs else 50000
    rows = db.query(M.Customer, M.ChurnPrediction, M.CustomerValue).join(
        M.ChurnPrediction, M.ChurnPrediction.customer_id == M.Customer.id).join(
        M.CustomerValue, M.CustomerValue.customer_id == M.Customer.id).filter(
        M.Customer.tenant_id == t).all()
    segs = {}
    for c, p, v in rows:
        hv = v.clv >= med; hr = p.proba >= 0.5
        key = "High Value / High Risk" if hv and hr else ("High Value / Low Risk" if hv else ("Low Value / High Risk" if hr else "Low Value / Low Risk"))
        s = segs.setdefault(key, {"segment": key, "count": 0, "rar": 0, "avg_proba": []})
        s["count"] += 1; s["rar"] += v.revenue_at_risk; s["avg_proba"].append(p.proba)
    out = []
    for s in segs.values():
        s["rar"] = round(s["rar"], 2)
        s["avg_proba"] = round(sum(s["avg_proba"])/max(1, len(s["avg_proba"])), 3)
        out.append(s)
    return {"median_clv": round(med, 2), "segments": sorted(out, key=lambda x: -x["rar"])}
