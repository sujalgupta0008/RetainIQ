from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models as M, schemas as S
from ..deps import current_user
from ..services import (analyst_context, analyst_fallback, analyst_llm, audit,
                      find_customer, CANONICAL_QUESTIONS)

r = APIRouter(prefix="/api/ai", tags=["ai"])

@r.get("/suggested")
def suggested():
    return CANONICAL_QUESTIONS

@r.post("/ask")
def ask(b: S.AskIn, u: M.User = Depends(current_user), db: Session = Depends(get_db)):
    ctx = analyst_context(db, u.tenant_id)
    cust = find_customer(db, u.tenant_id, b.question)
    if cust:
        ctx["customer"] = cust
    ans = analyst_llm(b.question, ctx) or analyst_fallback(b.question, ctx)
    audit(db, u.tenant_id, u.id, "ai_ask", b.question[:300]); db.commit()
    return {"answer": ans, "grounded": True, "disclaimer": "Estimates from current model outputs, not guarantees."}
