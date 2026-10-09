from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models as M, schemas as S
from ..deps import current_user, rate_limit
from ..services import (analyst_context, analyst_fallback, analyst_llm, audit,
                      find_customer, CANONICAL_QUESTIONS)

r = APIRouter(prefix="/api/ai", tags=["ai"])

@r.get("/suggested")
def suggested():
    return CANONICAL_QUESTIONS

@r.post("/ask", dependencies=[Depends(rate_limit(30, 60))])
def ask(body: S.AskIn, user: M.User = Depends(current_user), db: Session = Depends(get_db)):
    ctx = analyst_context(db, user.tenant_id)
    cust = find_customer(db, user.tenant_id, body.question)
    if cust:
        ctx["customer"] = cust
    ans = analyst_llm(body.question, ctx) or analyst_fallback(body.question, ctx)
    # Audit stores a truncated question; it may contain a customer name the operator typed.
    # Per-tenant visible only; PII-minimizing deployments can disable ai_ask audit here.
    audit(db, user.tenant_id, user.id, "ai_ask", body.question[:300]); db.commit()
    return {"answer": ans, "grounded": True, "disclaimer": "Estimates from current model outputs, not guarantees."}
