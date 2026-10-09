from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models as M, schemas as S
from ..deps import current_user
from ..services import audience_query, calc_roi, scenarios, audit

r = APIRouter(prefix="/api/roi", tags=["roi"])

@r.post("/simulate")
def simulate(b: S.RoiIn, u: M.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = audience_query(db, u.tenant_id, {"min_proba": b.min_proba, "min_clv": b.min_clv, "segment": b.segment})
    n = len(rows)
    avg_clv = sum(v.clv for _, _, v in rows)/max(1, n)
    base = calc_roi(n, b.success_rate, avg_clv, b.intervention_cost, b.reach)
    audit(db, u.tenant_id, u.id, "simulate",
          f"proba>={b.min_proba} clv>={b.min_clv} cost={b.intervention_cost} succ={b.success_rate} -> ROI {base['roi_pct']}%")
    db.commit()
    return {"audience": n, "avg_clv": round(avg_clv, 2), "estimated": True,
            **base, "scenarios": scenarios(base, b.success_rate)}
