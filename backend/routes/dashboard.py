import statistics

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models as M
from ..deps import current_user
from ..services import product_risk_rows

r = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@r.get("/summary")
def summary(user: M.User = Depends(current_user), db: Session = Depends(get_db)):
    tid = user.tenant_id
    total = db.query(M.Customer).filter_by(tenant_id=tid).count()
    high = db.query(M.ChurnPrediction).filter_by(tenant_id=tid, band="High").count()
    medium = db.query(M.ChurnPrediction).filter_by(tenant_id=tid, band="Medium").count()
    low = db.query(M.ChurnPrediction).filter_by(tenant_id=tid, band="Low").count()
    rar = db.query(func.sum(M.CustomerValue.revenue_at_risk)).filter_by(tenant_id=tid).scalar() or 0
    clv_risk = rar  # same model, two labels
    camps = db.query(M.Campaign).filter_by(tenant_id=tid).all()
    results = db.query(M.ExperimentResult).filter_by(tenant_id=tid).all()
    cost = sum(x.cost for x in results); revenue = sum(x.revenue for x in results)
    targeted = db.query(M.CampaignTarget).filter_by(tenant_id=tid).count()
    retained = db.query(M.CampaignTarget).filter_by(tenant_id=tid, retained=True).count()
    return {"total": total, "high": high, "medium": medium, "low": low,
        "revenue_at_risk": round(rar, 2), "value_at_risk": round(clv_risk, 2),
        "expected_protected": round(revenue, 2), "campaign_cost": round(cost, 2),
        "expected_roi_pct": round((revenue-cost)/max(1, cost)*100, 1),
        "retention_budget": 1000000, "customers_targeted": targeted,
        "expected_retained": retained, "campaigns": len(camps)}

@r.get("/risk-dist")
def risk_dist(user: M.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(M.ChurnPrediction.band, func.count(M.ChurnPrediction.id)).filter_by(
        tenant_id=user.tenant_id).group_by(M.ChurnPrediction.band).all()
    return [{"band": band, "count": count} for band, count in rows]

@r.get("/revenue-by-segment")
def revenue_by_segment(user: M.User = Depends(current_user), db: Session = Depends(get_db)):
    tid = user.tenant_id
    rows = db.query(M.Customer.segment, func.sum(M.CustomerValue.revenue_at_risk), func.count(M.Customer.id)).join(
        M.CustomerValue, M.CustomerValue.customer_id == M.Customer.id).filter(
        M.Customer.tenant_id == tid).group_by(M.Customer.segment).all()
    return [{"segment": seg, "rar": round(rar or 0, 2), "count": count} for seg, rar, count in rows]

@r.get("/product-risk")
def product_risk(user: M.User = Depends(current_user), db: Session = Depends(get_db)):
    return product_risk_rows(db, user.tenant_id)

@r.get("/risk-trend")
def risk_trend(user: M.User = Depends(current_user), db: Session = Depends(get_db)):
    preds = db.query(M.ChurnPrediction).filter_by(tenant_id=user.tenant_id).all()
    agg = {"d90": [], "d60": [], "d30": [], "today": []}
    for pred in preds:
        traj = pred.trajectory or {}
        for point in agg:
            if point in traj: agg[point].append(traj[point])
    return [{"point": point, "avg_risk": round(statistics.mean(v)*100, 1) if v else 0,
             "high": sum(1 for x in v if x >= 0.6)} for point, v in agg.items()]

@r.get("/quadrant")
def quadrant(user: M.User = Depends(current_user), db: Session = Depends(get_db)):
    tid = user.tenant_id
    clvs = [v.clv for v in db.query(M.CustomerValue).filter_by(tenant_id=tid).all()]
    median = statistics.median(clvs) if clvs else 50000
    rows = db.query(M.Customer, M.ChurnPrediction, M.CustomerValue).join(
        M.ChurnPrediction, M.ChurnPrediction.customer_id == M.Customer.id).join(
        M.CustomerValue, M.CustomerValue.customer_id == M.Customer.id).filter(
        M.Customer.tenant_id == tid).all()
    quads = {"hv_hr": 0, "hv_lr": 0, "lv_hr": 0, "lv_lr": 0}
    for cust, pred, val in rows:
        key = ("hv" if val.clv >= median else "lv") + "_" + ("hr" if pred.proba >= 0.5 else "lr")
        quads[key] += 1
    return {"median_clv": round(median, 2), **quads}

@r.get("/campaign-perf")
def campaign_perf(user: M.User = Depends(current_user), db: Session = Depends(get_db)):
    out = []
    for camp in db.query(M.Campaign).filter_by(tenant_id=user.tenant_id).all():
        exp = db.query(M.Experiment).filter_by(campaign_id=camp.id).first()
        res = db.query(M.ExperimentResult).filter_by(experiment_id=exp.id).first() if exp else None
        out.append({"id": camp.id, "name": camp.name, "status": camp.status,
            "roi_pct": round(res.roi*100, 1) if res else None,
            "revenue": res.revenue if res else 0, "lift": res.lift if res else 0})
    return out
