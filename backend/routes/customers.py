from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models as M
from ..deps import current_user
from ..services import deterioration, escape_like

r = APIRouter(prefix="/api/customers", tags=["customers"])


@r.get("")
def list_customers(search: str = Query(default="", max_length=120),
                   risk: str = Query(default="", max_length=20),
                   segment: str = Query(default="", max_length=60),
                   sort: str = Query(default="rar", max_length=20),
                   page: int = Query(default=1, ge=1, le=10000),
                   page_size: int = Query(default=20, ge=1, le=100),
                   user: M.User = Depends(current_user), db: Session = Depends(get_db)):
    tid = user.tenant_id
    q = db.query(M.Customer, M.ChurnPrediction, M.CustomerValue, M.Recommendation).join(
        M.ChurnPrediction, M.ChurnPrediction.customer_id == M.Customer.id).join(
        M.CustomerValue, M.CustomerValue.customer_id == M.Customer.id).join(
        M.Recommendation, M.Recommendation.customer_id == M.Customer.id).filter(
        M.Customer.tenant_id == tid)
    if search:
        # Escape LIKE wildcards so search text can't broaden matches; backslash escape.
        q = q.filter(M.Customer.name.ilike(f"%{escape_like(search)}%", escape="\\"))
    if risk:
        if risk not in ("High", "Medium", "Low"):
            raise HTTPException(400, "Invalid risk band")
        q = q.filter(M.ChurnPrediction.band == risk)
    if segment:
        q = q.filter(M.Customer.segment == segment[:60])
    rows = q.all()
    key = {"rar": lambda x: -x[2].revenue_at_risk, "proba": lambda x: -x[1].proba,
           "clv": lambda x: -x[2].clv, "name": lambda x: x[0].name}.get(sort, lambda x: -x[2].revenue_at_risk)
    rows.sort(key=key)
    total = len(rows)
    page_rows = rows[(page-1)*page_size: page*page_size]
    return {"total": total, "page": page, "page_size": page_size, "items": [{
        "id": c.id, "name": c.name, "age": c.age, "segment": c.segment, "region": c.region,
        "tenure": c.tenure_months, "proba": p.proba, "band": p.band, "clv": v.clv,
        "rar": v.revenue_at_risk, "action": rec.action, "priority": rec.priority,
        "score": rec.priority_score} for c, p, v, rec in page_rows]}


@r.get("/{cid}")
def detail(cid: int, user: M.User = Depends(current_user), db: Session = Depends(get_db)):
    tid = user.tenant_id
    cust = db.query(M.Customer).filter_by(id=cid, tenant_id=tid).first()
    if not cust:
        raise HTTPException(404, "Customer not found")
    # FIX (S05): related rows are tenant-scoped too (defense-in-depth; customer PKs are
    # globally unique so this was low-risk, but cross-tenant reads must be impossible).
    pred = db.query(M.ChurnPrediction).filter_by(customer_id=cid, tenant_id=tid).first()
    val = db.query(M.CustomerValue).filter_by(customer_id=cid, tenant_id=tid).first()
    reco = db.query(M.Recommendation).filter_by(customer_id=cid, tenant_id=tid).first()
    feats = db.query(M.CustomerFeature).filter_by(customer_id=cid, tenant_id=tid).first()
    accts = db.query(M.Account).filter_by(customer_id=cid, tenant_id=tid).all()
    txns = db.query(M.Transaction).filter_by(customer_id=cid, tenant_id=tid).order_by(M.Transaction.ts.desc()).limit(12).all()
    inter = db.query(M.Interaction).filter_by(customer_id=cid, tenant_id=tid).order_by(M.Interaction.ts.desc()).limit(10).all()
    links = db.query(M.CustomerProduct).filter_by(customer_id=cid, tenant_id=tid).all()
    pnames = []
    for link in links:
        prod = db.query(M.Product).filter_by(id=link.product_id).first()
        if prod:
            pnames.append(prod.name)
    det_score, det_flags = deterioration(feats.f if feats else {})
    return {"id": cust.id, "name": cust.name, "age": cust.age, "income": cust.income, "tenure": cust.tenure_months,
        "region": cust.region, "segment": cust.segment,
        "balances": [{"type": a.type, "balance": a.balance} for a in accts],
        "total_balance": round(sum(a.balance for a in accts), 2),
        "products": pnames, "product_count": len(pnames),
        "transactions": [{"amount": x.amount, "ts": str(x.ts), "type": x.type} for x in txns],
        "txn_freq": feats.f.get("txn_freq") if feats else None,
        "avg_txn": feats.f.get("avg_txn") if feats else None,
        "logins": feats.f.get("logins") if feats else None,
        "complaints": feats.f.get("complaints") if feats else None,
        "interactions": [{"kind": x.kind, "ts": str(x.ts), "note": x.note} for x in inter],
        "proba": pred.proba if pred else None, "band": pred.band if pred else None,
        "trajectory": pred.trajectory if pred else {}, "drivers": pred.drivers if pred else [],
        "explanation": pred.explanation if pred else "",
        "clv": val.clv if val else 0, "annual_contrib": val.annual_contrib if val else 0,
        "rar": val.revenue_at_risk if val else 0,
        "action": {"key": reco.action, "cost": reco.cost, "success": reco.success,
                   "roi": reco.expected_roi, "reason": reco.reason} if reco else None,
        "priority": reco.priority if reco else None, "score": reco.priority_score if reco else None,
        "deterioration": det_score, "det_flags": det_flags, "features": feats.f if feats else {}}
