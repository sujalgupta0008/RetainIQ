import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models as M, schemas as S
from ..deps import current_user, require_role
from ..services import audience_query, audit

r = APIRouter(prefix="/api/campaigns", tags=["campaigns"])

@r.get("")
def list_campaigns(user: M.User = Depends(current_user), db: Session = Depends(get_db)):
    out = []
    for camp in db.query(M.Campaign).filter_by(tenant_id=user.tenant_id).order_by(M.Campaign.id.desc()).all():
        n = db.query(M.CampaignTarget).filter_by(campaign_id=camp.id).count()
        out.append({"id": camp.id, "name": camp.name, "intervention": camp.intervention,
            "audience": camp.audience, "offer_cost": camp.offer_cost, "expected_success": camp.expected_success,
            "status": camp.status, "targets": n})
    return out

@r.post("")
def create(body: S.CampaignIn, user: M.User = Depends(require_role("admin", "manager")), db: Session = Depends(get_db)):
    rows = audience_query(db, user.tenant_id, {"min_proba": body.min_proba, "min_clv": body.min_clv, "segment": body.segment})
    avg_clv = sum(v.clv for _, _, v in rows)/max(1, len(rows))
    camp = M.Campaign(tenant_id=user.tenant_id, name=body.name, intervention=body.intervention,
        audience={"min_proba": body.min_proba, "min_clv": body.min_clv, "segment": body.segment, "product": body.product},
        offer_cost=body.offer_cost, expected_success=body.expected_success,
        duration_days=body.duration_days, status="draft")
    db.add(camp); db.flush()
    n = len(rows); retained = n*body.expected_success; revenue = retained*avg_clv
    proj = {"targeted": n, "revenue": round(revenue, 2),
            "cost": round(n*body.offer_cost, 2),
            "roi_pct": round((revenue - n*body.offer_cost)/max(1, n*body.offer_cost)*100, 1)}
    audit(db, user.tenant_id, user.id, "campaign_create", f"{body.name} audience={n}"); db.commit()
    return {"id": camp.id, "projected": proj, "audience": n}

@r.get("/{cid}")
def one_campaign(cid: int, user: M.User = Depends(current_user), db: Session = Depends(get_db)):
    camp = db.query(M.Campaign).filter_by(id=cid, tenant_id=user.tenant_id).first()
    if not camp: raise HTTPException(404, "Not found")
    exp = db.query(M.Experiment).filter_by(campaign_id=cid).first()
    res = db.query(M.ExperimentResult).filter_by(experiment_id=exp.id).first() if exp else None
    return {"id": camp.id, "name": camp.name, "intervention": camp.intervention, "audience": camp.audience,
        "offer_cost": camp.offer_cost, "expected_success": camp.expected_success, "status": camp.status,
        "results": {"treat_n": res.treat_n, "ctrl_n": res.ctrl_n, "treat_ret": res.treat_ret,
            "ctrl_ret": res.ctrl_ret, "lift": res.lift, "revenue": res.revenue,
            "cost": res.cost, "roi": res.roi} if res else None}

@r.post("/{cid}/launch")
def launch(cid: int, user: M.User = Depends(require_role("admin", "manager")), db: Session = Depends(get_db)):
    camp = db.query(M.Campaign).filter_by(id=cid, tenant_id=user.tenant_id).first()
    if not camp: raise HTTPException(404, "Not found")
    if camp.status == "completed": raise HTTPException(400, "Already launched")
    rnd = random.Random(42 + cid)  # nosec B311 -- simulated A/B outcomes for demo, not security use
    rows = audience_query(db, user.tenant_id, {"min_proba": camp.audience.get("min_proba", 0.4),
        "min_clv": camp.audience.get("min_clv", 0), "segment": camp.audience.get("segment")})
    if not rows: raise HTTPException(400, "Audience is empty — loosen filters")
    exp = db.query(M.Experiment).filter_by(campaign_id=cid).first()
    if not exp:
        exp = M.Experiment(tenant_id=user.tenant_id, campaign_id=cid, name=f"{camp.name} A/B"); db.add(exp); db.flush()
    ids = [cust.id for cust, _, _ in rows]
    rnd.shuffle(ids)
    n_ctrl = max(5, int(len(ids)*0.2))
    ctrl = set(ids[:n_ctrl])
    clv_by_id = {v.customer_id: v.clv for _, _, v in rows}
    treat_n = ctrl_n = treat_kept = ctrl_kept = 0
    for cust_id in ids:
        is_ctrl = cust_id in ctrl
        keep_rate = 0.15 if is_ctrl else camp.expected_success
        kept = rnd.random() < keep_rate
        db.add(M.CampaignTarget(tenant_id=user.tenant_id, campaign_id=camp.id, customer_id=cust_id,
               group="control" if is_ctrl else "treatment", reached=True, retained=kept))
        if is_ctrl: ctrl_n += 1; ctrl_kept += kept
        else: treat_n += 1; treat_kept += kept
    treat_rate = treat_kept/max(1, treat_n); ctrl_rate = ctrl_kept/max(1, ctrl_n); lift = treat_rate - ctrl_rate
    avg_clv = sum(clv_by_id.values())/max(1, len(clv_by_id))
    revenue = max(0, lift)*treat_n*avg_clv; cost = treat_n*camp.offer_cost
    result = M.ExperimentResult(tenant_id=user.tenant_id, experiment_id=exp.id, treat_n=treat_n, ctrl_n=ctrl_n,
        treat_ret=round(treat_rate, 3), ctrl_ret=round(ctrl_rate, 3), lift=round(lift, 3),
        revenue=round(revenue, 2), cost=round(cost, 2), roi=round((revenue-cost)/max(1, cost), 3))
    db.add(result)
    camp.status = "completed"
    audit(db, user.tenant_id, user.id, "campaign_launch", f"{camp.name} n={len(ids)} lift={lift:.2%}"); db.commit()
    return {"ok": True, "treat_n": treat_n, "ctrl_n": ctrl_n, "treat_ret": round(treat_rate, 3),
            "ctrl_ret": round(ctrl_rate, 3), "lift": round(lift, 3), "revenue": round(revenue, 2),
            "cost": round(cost, 2), "simulated": True}
