from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models as M
from ..deps import current_user

r = APIRouter(prefix="/api/experiments", tags=["experiments"])

@r.get("")
def all_experiments(user: M.User = Depends(current_user), db: Session = Depends(get_db)):
    out = []
    for exp in db.query(M.Experiment).filter_by(tenant_id=user.tenant_id).all():
        res = db.query(M.ExperimentResult).filter_by(experiment_id=exp.id).first()
        camp = db.query(M.Campaign).filter_by(id=exp.campaign_id).first()
        out.append({"id": exp.id, "name": exp.name, "campaign": camp.name if camp else "",
            "results": {"treat_n": res.treat_n, "ctrl_n": res.ctrl_n, "treat_ret": res.treat_ret,
                "ctrl_ret": res.ctrl_ret, "lift": res.lift, "revenue": res.revenue,
                "cost": res.cost, "roi": res.roi} if res else None})
    return out

@r.get("/{eid}")
def one_experiment(eid: int, user: M.User = Depends(current_user), db: Session = Depends(get_db)):
    exp = db.query(M.Experiment).filter_by(id=eid, tenant_id=user.tenant_id).first()
    if not exp: raise HTTPException(404, "Not found")
    res = db.query(M.ExperimentResult).filter_by(experiment_id=eid).first()
    return {"id": exp.id, "name": exp.name, "campaign_id": exp.campaign_id,
            "results": {k: getattr(res, k) for k in
             ["treat_n","ctrl_n","treat_ret","ctrl_ret","lift","revenue","cost","roi"]} if res else None,
            "note": "Simulated outcomes for demo — do not claim causal certainty beyond this design."}
