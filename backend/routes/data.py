import io
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models as M
from ..deps import current_user, require_role, rate_limit
from ..services import audit
from ..csv_import import normalize_customer_csv

r = APIRouter(prefix="/api/data", tags=["data"])

# Upload guardrails (S04): bound memory/CPU per request. Tune via constants.
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_UPLOAD_ROWS = 20000

SAMPLE = """name,age,income,tenure_months,region,avg_balance,txn_freq,avg_txn
Test User,38,900000,30,Mumbai,120000,10,4500
Sample Saver,45,1500000,60,Pune,300000,14,6000
"""


@r.get("/sample", response_class=PlainTextResponse)
def sample():
    return SAMPLE


@r.get("/status")
def status(u: M.User = Depends(current_user), db: Session = Depends(get_db)):
    return {"customers": db.query(M.Customer).filter_by(tenant_id=u.tenant_id).count(),
            "features": db.query(M.CustomerFeature).filter_by(tenant_id=u.tenant_id).count()}


def _read_csv(f: UploadFile) -> pd.DataFrame:
    # Filename check is advisory (browsers may omit it); content is validated by parsing.
    name = (f.filename or "").lower()
    if name and not name.endswith((".csv", ".txt")):
        raise HTTPException(400, "Only .csv files are accepted")
    raw_bytes = f.file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"File too large (limit {MAX_UPLOAD_BYTES // 1024 // 1024} MB)")
    try:
        raw = raw_bytes.decode("utf-8", errors="ignore")
    except Exception:
        raise HTTPException(400, "Could not decode CSV as text")
    if raw.count("\n") > MAX_UPLOAD_ROWS + 1:
        raise HTTPException(413, f"Too many rows (limit {MAX_UPLOAD_ROWS})")
    try:
        df = pd.read_csv(io.StringIO(raw))
    except Exception as e:
        raise HTTPException(400, f"Could not parse CSV: {e}")
    if len(df) > MAX_UPLOAD_ROWS:
        raise HTTPException(413, f"Too many rows (limit {MAX_UPLOAD_ROWS})")
    if len(df.columns) > 100:
        raise HTTPException(400, "Too many columns (limit 100)")
    return df


@r.post("/preview", dependencies=[Depends(rate_limit(30, 60))])
def preview(f: UploadFile, u: M.User = Depends(current_user)):
    df = _read_csv(f)
    dtype, records, mapping, issues = normalize_customer_csv(df)
    if dtype == "unknown":
        raise HTTPException(400, "Unrecognized CSV. Need a banking sample (name,income,avg_balance,txn_freq) "
                                "or IBM Telco columns (CustomerID, Monthly Charges, Churn Value), "
                                "or at least an id/name column.")
    labels = sum(r["label"] for r in records)
    return {"dataset_type": dtype, "rows_detected": len(df),
            "rows_importable": len(records), "rows_rejected": len(df) - len(records),
            "churn_labels": labels,
            "mapping": [{"from": a, "to": b} for a, b in mapping],
            "sample_names": [r["name"] for r in records[:3]],
            "issues": issues[:10],
            "telco_note": ("Telco dataset detected. Financial fields are domain-adapted proxies "
                           "used to demonstrate RetainIQ's retention workflow.") if dtype == "telco" else None}


@r.post("/upload", dependencies=[Depends(rate_limit(10, 60))])
def upload(f: UploadFile, u: M.User = Depends(require_role("admin", "manager", "analyst")), db: Session = Depends(get_db)):
    from ..services import (features_from_state, calc_clv, calc_rar, band, pick_action, priority_of,
                            explain_fallback, ACTIONS)
    from ..ml.infer import predict_proba
    df = _read_csv(f)
    dtype, records, _, issues = normalize_customer_csv(df)
    if dtype == "unknown":
        raise HTTPException(400, "Unrecognized CSV schema — see /preview for details.")
    existing = {c.name for c in db.query(M.Customer.name).filter_by(tenant_id=u.tenant_id).all()}
    # pass 1: insert customers + features + accounts
    new, errors = [], list(issues)
    for rec in records:
        if rec["name"] in existing:
            errors.append(f"duplicate '{rec['name']}' already in workspace, skipped")
            continue
        existing.add(rec["name"])
        c = M.Customer(tenant_id=u.tenant_id, name=rec["name"][:120], age=rec["age"],
            income=rec["income"], tenure_months=rec["tenure_months"],
            region=rec["region"][:60], segment=rec["segment"])
        db.add(c)
        db.flush()
        t = rec.get("_telco", {})
        feats = features_from_state(
            rec["age"], rec["income"], rec["tenure_months"], rec["avg_balance"],
            t.get("bal_trend", 0.0), rec["txn_freq"], rec["avg_txn"],
            t.get("txn_trend", 0.0), t.get("card", 0.4), rec["n_products"],
            rec["has_loan"], rec["complaints"], 7.0 if rec["complaints"] else 1.0,
            t.get("logins", 8.0), t.get("eng", 0.0),
            t.get("inactivity", 5), t.get("failed", 0.01))
        db.add(M.CustomerFeature(tenant_id=u.tenant_id, customer_id=c.id, f=feats, label=rec["label"]))
        db.add(M.Account(tenant_id=u.tenant_id, customer_id=c.id, type="savings",
                         balance=rec["avg_balance"]))
        new.append((c.id, feats, rec))
    # medians computed ONCE over the tenant (was per-row before)
    cfs = db.query(M.CustomerFeature).filter_by(tenant_id=u.tenant_id).all()
    med: dict = {}
    if cfs:
        _df = pd.DataFrame([x.f for x in cfs])
        med = {cc: float(_df[cc].median()) for cc in _df.columns}
    # pass 2: predictions + values + recommendations (FIX B05: use priority_of like seed/retrain)
    if new:
        _all_vals = db.query(M.CustomerValue).filter_by(tenant_id=u.tenant_id).all()
        _cmax = max(([v.clv for v in _all_vals] or [0]) + [0])
        _rmax_hint = max(([v.revenue_at_risk for v in _all_vals] or [0]) + [0])
        staged: list[tuple] = []
        for cid, feats, rec in new:
            p = predict_proba(feats)
            clv, contrib = calc_clv(feats["avg_balance"], feats["avg_txn"] * feats["txn_freq"] * 12,
                                    feats["product_count"], feats["complaints"], rec["tenure_months"])
            staged.append((cid, feats, rec, p, clv, contrib, calc_rar(p, clv)))
        cmax = max([s[4] for s in staged] + [_cmax, 1])
        rmax = max([s[6] for s in staged] + [_rmax_hint, 1])
        for cid, feats, rec, p, clv, contrib, rar in staged:
            dr, sent = explain_fallback(feats, p, med)
            db.add(M.ChurnPrediction(tenant_id=u.tenant_id, customer_id=cid, proba=p, band=band(p),
                   trajectory={"today": p}, drivers=dr, explanation=sent))
            db.add(M.CustomerValue(tenant_id=u.tenant_id, customer_id=cid, clv=clv,
                   annual_contrib=contrib, revenue_at_risk=rar))
            act, succ, reason = pick_action(feats, clv)
            sc, pri = priority_of(p, clv, rar, ACTIONS[act]["cost"], succ, cmax, rmax)
            db.add(M.Recommendation(tenant_id=u.tenant_id, customer_id=cid, action=act,
                   cost=ACTIONS[act]["cost"], success=succ,
                   expected_roi=round((succ * clv - ACTIONS[act]["cost"]) / max(1, ACTIONS[act]["cost"]), 3),
                   reason=reason, priority=pri, priority_score=sc))
    audit(db, u.tenant_id, u.id, "upload",
          f"type={dtype} added={len(new)} rejected={len(df) - len(new)}")
    db.commit()
    return {"dataset_type": dtype, "added": len(new),
            "rejected": len(df) - len(new), "errors": errors[:20],
            "next": "Review preview counts, then press Retrain so the model learns the new churn labels."}
