import json
import os

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models as M
from ..deps import current_user, require_role
from ..ml.infer import predict_proba
from ..ml.train import main as train_main
from ..services import band, explain_fallback, calc_clv, calc_rar, pick_action, priority_of, ACTIONS, audit

r = APIRouter(prefix="/api/predictions", tags=["predictions"])

@r.get("/metrics")
def metrics(user: M.User = Depends(current_user)):
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ml", "artifacts", "metrics.json"))
    if os.path.exists(path):
        with open(path) as f:
            return {"trained": True, **json.load(f)}
    return {"trained": False, "note": "Model not trained yet — rule-based fallback in use. POST /retrain."}

@r.post("/retrain")
def retrain(user: M.User = Depends(require_role("admin", "manager", "analyst")), db: Session = Depends(get_db)):
    rows = db.query(M.CustomerFeature).filter_by(tenant_id=user.tenant_id).all()
    # FIX (B02): empty-tenant guard — previously max() of empty sequence raised 500.
    if not rows:
        raise HTTPException(400, "No customer features for this workspace yet — upload data first")
    train_main()
    df = pd.DataFrame([x.f for x in rows]); medians = {c: float(df[c].median()) for c in df.columns}
    scored = {}
    for row in rows:
        proba = predict_proba(row.f)
        annual = row.f["avg_txn"]*row.f["txn_freq"]*12
        clv, contrib = calc_clv(row.f["avg_balance"], annual, row.f["product_count"], row.f["complaints"], row.f["tenure_months"])
        scored[row.customer_id] = (proba, clv, contrib, calc_rar(proba, clv))
    clv_max = max(v[1] for v in scored.values()); rar_max = max(v[3] for v in scored.values())
    for row in rows:
        proba, clv, contrib, rar = scored[row.customer_id]
        drivers, explanation = explain_fallback(row.f, proba, medians)
        pred = db.query(M.ChurnPrediction).filter_by(customer_id=row.customer_id, tenant_id=user.tenant_id).first()
        if not pred:
            continue
        pred.proba, pred.band, pred.drivers, pred.explanation = round(proba, 4), band(proba), drivers, explanation
        pred.trajectory = {**(pred.trajectory or {}), "today": round(proba, 4)}
        val = db.query(M.CustomerValue).filter_by(customer_id=row.customer_id, tenant_id=user.tenant_id).first()
        if val:
            val.clv, val.annual_contrib, val.revenue_at_risk = clv, contrib, rar
        action, success, reason = pick_action(row.f, clv)
        score, priority = priority_of(proba, clv, rar, ACTIONS[action]["cost"], success, clv_max, rar_max)
        reco = db.query(M.Recommendation).filter_by(customer_id=row.customer_id, tenant_id=user.tenant_id).first()
        if not reco:
            continue
        reco.action, reco.cost, reco.success = action, ACTIONS[action]["cost"], success
        reco.expected_roi = round((success*clv - ACTIONS[action]["cost"])/max(1, ACTIONS[action]["cost"]), 3)
        reco.reason, reco.priority, reco.priority_score = reason, priority, score
    audit(db, user.tenant_id, user.id, "retrain", f"{len(rows)} customers"); db.commit()
    return {"ok": True, "updated": len(rows)}
