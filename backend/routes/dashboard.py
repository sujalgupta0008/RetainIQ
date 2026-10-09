from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from .. import models as M
from ..deps import current_user

r = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

def _t(u: M.User): return u.tenant_id

@r.get("/summary")
def summary(u: M.User = Depends(current_user), db: Session = Depends(get_db)):
    t = _t(u)
    total = db.query(M.Customer).filter_by(tenant_id=t).count()
    hi = db.query(M.ChurnPrediction).filter_by(tenant_id=t, band="High").count()
    med = db.query(M.ChurnPrediction).filter_by(tenant_id=t, band="Medium").count()
    lo = db.query(M.ChurnPrediction).filter_by(tenant_id=t, band="Low").count()
    rar = db.query(func.sum(M.CustomerValue.revenue_at_risk)).filter_by(tenant_id=t).scalar() or 0
    clv_risk = rar  # customer value at risk == revenue at risk in this model
    camps = db.query(M.Campaign).filter_by(tenant_id=t).all()
    res = db.query(M.ExperimentResult).filter_by(tenant_id=t).all()
    cost = sum(x.cost for x in res); rev = sum(x.revenue for x in res)
    targeted = db.query(M.CampaignTarget).filter_by(tenant_id=t).count()
    retained = db.query(M.CampaignTarget).filter_by(tenant_id=t, retained=True).count()
    return {"total": total, "high": hi, "medium": med, "low": lo,
        "revenue_at_risk": round(rar, 2), "value_at_risk": round(clv_risk, 2),
        "expected_protected": round(rev, 2), "campaign_cost": round(cost, 2),
        "expected_roi_pct": round((rev-cost)/max(1, cost)*100, 1),
        "retention_budget": 1000000, "customers_targeted": targeted,
        "expected_retained": retained, "campaigns": len(camps)}

@r.get("/risk-dist")
def risk_dist(u: M.User = Depends(current_user), db: Session = Depends(get_db)):
    t = _t(u)
    rows = db.query(M.ChurnPrediction.band, func.count(M.ChurnPrediction.id)).filter_by(tenant_id=t).group_by(M.ChurnPrediction.band).all()
    return [{"band": b, "count": c} for b, c in rows]

@r.get("/revenue-by-segment")
def rev_seg(u: M.User = Depends(current_user), db: Session = Depends(get_db)):
    t = _t(u)
    rows = db.query(M.Customer.segment, func.sum(M.CustomerValue.revenue_at_risk), func.count(M.Customer.id)).join(
        M.CustomerValue, M.CustomerValue.customer_id == M.Customer.id).filter(
        M.Customer.tenant_id == t).group_by(M.Customer.segment).all()
    return [{"segment": s, "rar": round(r or 0, 2), "count": c} for s, r, c in rows]

@r.get("/product-risk")
def prod_risk(u: M.User = Depends(current_user), db: Session = Depends(get_db)):
    t = _t(u)
    out = []
    for p in db.query(M.Product).all():
        cids = [x.customer_id for x in db.query(M.CustomerProduct).filter_by(tenant_id=t, product_id=p.id).all()]
        if not cids: continue
        vals = db.query(M.CustomerValue).filter(M.CustomerValue.customer_id.in_(cids)).all()
        preds = {x.customer_id: x for x in db.query(M.ChurnPrediction).filter(M.ChurnPrediction.customer_id.in_(cids)).all()}
        hi = sum(1 for c in cids if preds.get(c) and preds[c].band == "High")
        out.append({"product": p.name, "customers": len(cids), "high_risk": hi,
                    "rar": round(sum(v.revenue_at_risk for v in vals), 2)})
    return sorted(out, key=lambda x: -x["rar"])

@r.get("/risk-trend")
def trend(u: M.User = Depends(current_user), db: Session = Depends(get_db)):
    t = _t(u)
    preds = db.query(M.ChurnPrediction).filter_by(tenant_id=t).all()
    agg = {"d90": [], "d60": [], "d30": [], "today": []}
    for p in preds:
        tr = p.trajectory or {}
        for k in agg:
            if k in tr: agg[k].append(tr[k])
    import statistics
    return [{"point": k, "avg_risk": round(statistics.mean(v)*100, 1) if v else 0,
             "high": sum(1 for x in v if x >= 0.6)} for k, v in agg.items()]

@r.get("/quadrant")
def quadrant(u: M.User = Depends(current_user), db: Session = Depends(get_db)):
    t = _t(u)
    clvs = [v.clv for v in db.query(M.CustomerValue).filter_by(tenant_id=t).all()]
    import statistics
    med = statistics.median(clvs) if clvs else 50000
    rows = db.query(M.Customer, M.ChurnPrediction, M.CustomerValue).join(
        M.ChurnPrediction, M.ChurnPrediction.customer_id == M.Customer.id).join(
        M.CustomerValue, M.CustomerValue.customer_id == M.Customer.id).filter(
        M.Customer.tenant_id == t).all()
    quads = {"hv_hr": 0, "hv_lr": 0, "lv_hr": 0, "lv_lr": 0}
    for c, p, v in rows:
        key = ("hv" if v.clv >= med else "lv") + "_" + ("hr" if p.proba >= 0.5 else "lr")
        quads[key] += 1
    return {"median_clv": round(med, 2), **quads}

@r.get("/campaign-perf")
def perf(u: M.User = Depends(current_user), db: Session = Depends(get_db)):
    t = _t(u)
    out = []
    for c in db.query(M.Campaign).filter_by(tenant_id=t).all():
        exp = db.query(M.Experiment).filter_by(campaign_id=c.id).first()
        res = db.query(M.ExperimentResult).filter_by(experiment_id=exp.id).first() if exp else None
        out.append({"id": c.id, "name": c.name, "status": c.status,
            "roi_pct": round(res.roi*100, 1) if res else None,
            "revenue": res.revenue if res else 0, "lift": res.lift if res else 0})
    return out
