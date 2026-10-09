import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models as M, schemas as S
from ..deps import current_user, require_role
from ..services import audience_query, audit, ACTIONS

r = APIRouter(prefix="/api/campaigns", tags=["campaigns"])

@r.get("")
def list_c(u: M.User = Depends(current_user), db: Session = Depends(get_db)):
    out = []
    for c in db.query(M.Campaign).filter_by(tenant_id=u.tenant_id).order_by(M.Campaign.id.desc()).all():
        n = db.query(M.CampaignTarget).filter_by(campaign_id=c.id).count()
        out.append({"id": c.id, "name": c.name, "intervention": c.intervention,
            "audience": c.audience, "offer_cost": c.offer_cost, "expected_success": c.expected_success,
            "status": c.status, "targets": n})
    return out

@r.post("")
def create(b: S.CampaignIn, u: M.User = Depends(require_role("admin", "manager")), db: Session = Depends(get_db)):
    rows = audience_query(db, u.tenant_id, {"min_proba": b.min_proba, "min_clv": b.min_clv, "segment": b.segment})
    avg_clv = sum(v.clv for _, _, v in rows)/max(1, len(rows))
    c = M.Campaign(tenant_id=u.tenant_id, name=b.name, intervention=b.intervention,
        audience={"min_proba": b.min_proba, "min_clv": b.min_clv, "segment": b.segment, "product": b.product},
        offer_cost=b.offer_cost, expected_success=b.expected_success,
        duration_days=b.duration_days, status="draft")
    db.add(c); db.flush()
    n = len(rows); retained = n*b.expected_success; rev = retained*avg_clv
    proj = {"targeted": n, "revenue": round(rev, 2),
            "cost": round(n*b.offer_cost, 2),
            "roi_pct": round((rev - n*b.offer_cost)/max(1, n*b.offer_cost)*100, 1)}
    audit(db, u.tenant_id, u.id, "campaign_create", f"{b.name} audience={n}"); db.commit()
    return {"id": c.id, "projected": proj, "audience": n}

@r.get("/{cid}")
def one(cid: int, u: M.User = Depends(current_user), db: Session = Depends(get_db)):
    c = db.query(M.Campaign).filter_by(id=cid, tenant_id=u.tenant_id).first()
    if not c: raise HTTPException(404, "Not found")
    exp = db.query(M.Experiment).filter_by(campaign_id=cid).first()
    res = db.query(M.ExperimentResult).filter_by(experiment_id=exp.id).first() if exp else None
    return {"id": c.id, "name": c.name, "intervention": c.intervention, "audience": c.audience,
        "offer_cost": c.offer_cost, "expected_success": c.expected_success, "status": c.status,
        "results": {"treat_n": res.treat_n, "ctrl_n": res.ctrl_n, "treat_ret": res.treat_ret,
            "ctrl_ret": res.ctrl_ret, "lift": res.lift, "revenue": res.revenue,
            "cost": res.cost, "roi": res.roi} if res else None}

@r.post("/{cid}/launch")
def launch(cid: int, u: M.User = Depends(require_role("admin", "manager")), db: Session = Depends(get_db)):
    c = db.query(M.Campaign).filter_by(id=cid, tenant_id=u.tenant_id).first()
    if not c: raise HTTPException(404, "Not found")
    if c.status == "completed": raise HTTPException(400, "Already launched")
    rnd = random.Random(42 + cid)  # nosec B311 -- simulated A/B outcomes for demo, not security use
    rows = audience_query(db, u.tenant_id, {"min_proba": c.audience.get("min_proba", 0.4),
        "min_clv": c.audience.get("min_clv", 0), "segment": c.audience.get("segment")})
    if not rows: raise HTTPException(400, "Audience is empty — loosen filters")
    exp = db.query(M.Experiment).filter_by(campaign_id=cid).first()
    if not exp:
        exp = M.Experiment(tenant_id=u.tenant_id, campaign_id=cid, name=f"{c.name} A/B"); db.add(exp); db.flush()
    ids = [cu.id for cu, _, _ in rows]
    rnd.shuffle(ids)
    n_ctrl = max(5, int(len(ids)*0.2))
    ctrl = set(ids[:n_ctrl])
    vals = {v.customer_id: v.clv for _, _, v in rows}
    tn = cn = tr = cr = 0
    for cid_ in ids:
        is_ctrl = cid_ in ctrl
        p_ret = 0.15 if is_ctrl else c.expected_success
        retained = rnd.random() < p_ret
        db.add(M.CampaignTarget(tenant_id=u.tenant_id, campaign_id=c.id, customer_id=cid_,
               group="control" if is_ctrl else "treatment", reached=True, retained=retained))
        if is_ctrl: cn += 1; cr += retained
        else: tn += 1; tr += retained
    tr_r = tr/max(1, tn); cr_r = cr/max(1, cn); lift = tr_r - cr_r
    avgv = sum(vals.values())/max(1, len(vals))
    rev = max(0, lift)*tn*avgv; cost = tn*c.offer_cost
    er = M.ExperimentResult(tenant_id=u.tenant_id, experiment_id=exp.id, treat_n=tn, ctrl_n=cn,
        treat_ret=round(tr_r, 3), ctrl_ret=round(cr_r, 3), lift=round(lift, 3),
        revenue=round(rev, 2), cost=round(cost, 2), roi=round((rev-cost)/max(1, cost), 3))
    db.add(er)
    c.status = "completed"
    audit(db, u.tenant_id, u.id, "campaign_launch", f"{c.name} n={len(ids)} lift={lift:.2%}"); db.commit()
    return {"ok": True, "treat_n": tn, "ctrl_n": cn, "treat_ret": round(tr_r, 3),
            "ctrl_ret": round(cr_r, 3), "lift": round(lift, 3), "revenue": round(rev, 2),
            "cost": round(cost, 2), "simulated": True}
