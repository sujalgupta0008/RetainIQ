from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models as M, schemas as S
from ..deps import current_user
from ..services import audience_query, calc_roi, scenarios, audit

r = APIRouter(prefix="/api/roi", tags=["roi"])

@r.post("/simulate")
def simulate(body: S.RoiIn, user: M.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = audience_query(db, user.tenant_id, {"min_proba": body.min_proba, "min_clv": body.min_clv, "segment": body.segment})
    n = len(rows)
    avg_clv = sum(v.clv for _, _, v in rows)/max(1, n)
    base = calc_roi(n, body.success_rate, avg_clv, body.intervention_cost, body.reach)
    audit(db, user.tenant_id, user.id, "simulate",
          f"proba>={body.min_proba} clv>={body.min_clv} cost={body.intervention_cost} succ={body.success_rate} -> ROI {base['roi_pct']}%")
    db.commit()
    return {"audience": n, "avg_clv": round(avg_clv, 2), "estimated": True,
            **base, "scenarios": scenarios(base, body.success_rate)}
