import json, os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models as M
from ..deps import current_user, require_role

r = APIRouter(prefix="/api/predictions", tags=["predictions"])

@r.get("/metrics")
def metrics(u: M.User = Depends(current_user)):
    p = os.path.join(os.path.dirname(__file__), "..", "ml", "artifacts", "metrics.json")
    p = os.path.abspath(p)
    if os.path.exists(p):
        return {"trained": True, **json.load(open(p))}
    return {"trained": False, "note": "Model not trained yet — rule-based fallback in use. POST /retrain."}

@r.post("/retrain")
def retrain(u: M.User = Depends(require_role("admin", "manager", "analyst")), db: Session = Depends(get_db)):
    from ..ml.train import main as train_main
    from ..ml.infer import predict_proba
    from ..services import band, explain_fallback, calc_clv, calc_rar, pick_action, priority_of, ACTIONS, audit
    from fastapi import HTTPException
    import pandas as pd
    cfs = db.query(M.CustomerFeature).filter_by(tenant_id=u.tenant_id).all()
    # FIX (B02): empty-tenant guard — previously max() of empty sequence raised 500.
    if not cfs:
        raise HTTPException(400, "No customer features for this workspace yet — upload data first")
    train_main()
    df = pd.DataFrame([x.f for x in cfs]); med = {c: float(df[c].median()) for c in df.columns}
    vals = db.query(M.CustomerValue).filter_by(tenant_id=u.tenant_id).all()
    tmp = {}
    for cf in cfs:
        pr = predict_proba(cf.f)
        annual = cf.f["avg_txn"]*cf.f["txn_freq"]*12
        clv, contrib = calc_clv(cf.f["avg_balance"], annual, cf.f["product_count"], cf.f["complaints"], cf.f["tenure_months"])
        tmp[cf.customer_id] = (pr, clv, contrib, calc_rar(pr, clv))
    cmax = max(v[1] for v in tmp.values()); rmax = max(v[3] for v in tmp.values())
    for cf in cfs:
        pr, clv, contrib, rar = tmp[cf.customer_id]
        dr, sent = explain_fallback(cf.f, pr, med)
        p = db.query(M.ChurnPrediction).filter_by(customer_id=cf.customer_id, tenant_id=u.tenant_id).first()
        if not p:
            continue
        p.proba, p.band, p.drivers, p.explanation = round(pr, 4), band(pr), dr, sent
        p.trajectory = {**(p.trajectory or {}), "today": round(pr, 4)}
        vv = db.query(M.CustomerValue).filter_by(customer_id=cf.customer_id, tenant_id=u.tenant_id).first()
        if vv:
            vv.clv, vv.annual_contrib, vv.revenue_at_risk = clv, contrib, rar
        act, succ, reason = pick_action(cf.f, clv)
        sc, pri = priority_of(pr, clv, rar, ACTIONS[act]["cost"], succ, cmax, rmax)
        rc = db.query(M.Recommendation).filter_by(customer_id=cf.customer_id, tenant_id=u.tenant_id).first()
        if not rc:
            continue
        rc.action, rc.cost, rc.success = act, ACTIONS[act]["cost"], succ
        rc.expected_roi = round((succ*clv - ACTIONS[act]["cost"])/max(1, ACTIONS[act]["cost"]), 3)
        rc.reason, rc.priority, rc.priority_score = reason, pri, sc
    audit(db, u.tenant_id, u.id, "retrain", f"{len(cfs)} customers"); db.commit()
    return {"ok": True, "updated": len(cfs)}
