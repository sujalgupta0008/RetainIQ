"""All domain logic as plain functions. ROI formulas centralized here (tested)."""
import os, hashlib
import jwt

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
SEED = int(os.getenv("SEED", "42"))

ACTIONS = {
 "fee_waiver": {"cost": 500, "success": 0.22, "label": "Fee waiver"},
 "cashback": {"cost": 1200, "success": 0.28, "label": "Cashback offer"},
 "personalized_offer": {"cost": 800, "success": 0.25, "label": "Personalized offer"},
 "loan_offer": {"cost": 2000, "success": 0.20, "label": "Loan/credit offer"},
 "premium_upgrade": {"cost": 1500, "success": 0.18, "label": "Premium upgrade"},
 "rm_call": {"cost": 1000, "success": 0.30, "label": "Relationship manager call"},
 "service_recovery": {"cost": 700, "success": 0.35, "label": "Service recovery"},
 "no_intervention": {"cost": 0, "success": 0.02, "label": "No intervention"},
}

# ---------- auth ----------
def hash_pw(pw: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 100_000).hex()

def make_token(user_id: int, tenant_id: int, role: str) -> str:
    import datetime as dt
    now_utc = dt.datetime.now(dt.timezone.utc)
    payload = {"sub": str(user_id), "tenant_id": tenant_id, "role": role,
               "iat": now_utc, "exp": now_utc + dt.timedelta(hours=24)}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def decode_token(t: str) -> dict:
    return jwt.decode(t, JWT_SECRET, algorithms=["HS256"])

# ---------- audit ----------
def audit(db, tenant_id, user_id, action, meta=""):
    from .models import AuditLog
    db.add(AuditLog(tenant_id=tenant_id, user_id=user_id, action=action, meta=str(meta)[:2000]))

# ---------- finance (TESTED) ----------
def calc_clv(avg_balance, annual_txn_vol, product_count, complaints_1y, tenure_months) -> tuple:
    contrib = avg_balance*0.035 + annual_txn_vol*0.002 + product_count*1200 - complaints_1y*500
    contrib = max(500.0, float(contrib))
    years = min(7.0, 3.0 + tenure_months/24.0)
    return round(contrib*years, 2), round(contrib, 2)

def calc_rar(churn_proba, clv) -> float:
    return round(float(churn_proba)*float(clv), 2)

def calc_roi(targeted: int, success_rate: float, avg_value: float, unit_cost: float, reach: float = 1.0) -> dict:
    """Central ROI engine. All estimates labeled by callers."""
    # Defensive clamping so out-of-range callers (or stale clients) can't produce
    # nonsensical/negative-money outputs; Pydantic schemas enforce the same bounds.
    targeted = max(0, int(targeted or 0))
    success_rate = min(1.0, max(0.0, float(success_rate or 0.0)))
    avg_value = max(0.0, float(avg_value or 0.0))
    unit_cost = max(0.0, float(unit_cost or 0.0))
    reach = min(1.0, max(0.0, float(reach if reach is not None else 1.0)))
    t = int(round(targeted*reach))
    retained = t*success_rate
    cost = t*unit_cost
    revenue = retained*avg_value
    net = revenue - cost
    roi = (net/cost) if cost > 0 else 0.0
    be = (unit_cost/avg_value) if avg_value > 0 else 1.0
    out = {"targeted": t, "retained": round(retained,1), "cost": round(cost,2),
           "revenue": round(revenue,2), "net": round(net,2),
           "roi": round(roi,4), "roi_pct": round(roi*100,1),
           "break_even_rate": round(be,4)}
    return out

def scenarios(base: dict, success_rate: float) -> dict:
    # recompute revenue/net/roi scaled; cost/targeted same
    def sc(mult):
        s = min(0.9, success_rate*mult)
        ret = base["targeted"]*s
        rev = ret*(base["revenue"]/base["retained"] if base["retained"] else 0)
        net = rev - base["cost"]
        roi = net/base["cost"] if base["cost"] else 0
        return {"success": round(s,3), "retained": round(ret,1), "revenue": round(rev,2),
                "net": round(net,2), "roi_pct": round(roi*100,1)}
    return {"conservative": sc(0.6), "expected": sc(1.0), "optimistic": sc(1.4)}

def band(p: float) -> str:
    return "High" if p >= 0.6 else ("Medium" if p >= 0.35 else "Low")

def priority_of(proba, clv, rar, cost, success, clv_max, rar_max) -> tuple:
    score = (0.5*(rar/max(1,rar_max)) + 0.3*proba + 0.2*(clv/max(1,clv_max)))*100
    score = round(max(0, min(100, score)), 1)
    if proba >= 0.6 and score >= 45: seg = "Critical"
    elif proba >= 0.4 and score >= 30: seg = "High Priority"
    elif proba >= 0.35 or score >= 20: seg = "Monitor"
    else: seg = "Low Priority"
    return score, seg

def pick_action(feats: dict, clv: float) -> tuple:
    """Rule-boosted max(expected net). Returns (key, success_adj, reason)."""
    comp = feats.get("complaints", 0); bal_t = feats.get("balance_trend", 0)
    eng = feats.get("engagement_decline", 0); pc = feats.get("product_count", 1)
    best, best_val, best_s, reason = "personalized_offer", -1e18, 0.25, ""
    for k, v in ACTIONS.items():
        s = v["success"]
        r = f"Base success {s:.0%} for {v['label']}."
        if k == "service_recovery" and comp > 0:
            s = min(0.6, s + 0.1*comp); r = f"{comp} complaint(s) — service recovery has highest win-back."
        if k == "cashback" and bal_t < -0.1:
            s += 0.05; r = f"Balance down {bal_t:.0%} — cashback re-activates spend."
        if k == "rm_call" and (eng > 0.25 or clv > 150000):
            s += 0.05; r = "High value or disengaged — human outreach works best."
        if k == "personalized_offer" and pc <= 1:
            s += 0.04; r = "Single-product holder — cross-sell offer deepens relationship."
        if k == "no_intervention" and clv < 20000:
            r = "Low value — cost of action exceeds likely return."
        val = s*clv - v["cost"]
        if val > best_val:
            best, best_val, best_s, reason = k, val, s, r
    return best, round(min(0.9, best_s), 3), reason

# ---------- features from raw rows ----------
def features_from_state(age, income, tenure, avg_bal, bal_trend, txn_freq, avg_txn,
    txn_trend, card_use, n_prod, has_loan, complaints, res_days, logins, eng_dec, inact, fail) -> dict:
    return {"tenure_months": tenure, "age": age, "income": income, "avg_balance": avg_bal,
     "balance_trend": bal_trend, "txn_freq": txn_freq, "avg_txn": avg_txn, "txn_trend": txn_trend,
     "card_usage": card_use, "product_count": n_prod, "has_loan": has_loan, "complaints": complaints,
     "resolution_days": res_days, "logins": logins, "engagement_decline": eng_dec,
     "inactivity_days": inact, "failed_rate": fail}

FEAT_LABELS = {"tenure_months":"tenure","age":"age","income":"income","avg_balance":"average balance",
 "balance_trend":"balance trend","txn_freq":"transaction frequency","avg_txn":"average transaction value",
 "txn_trend":"transaction trend","card_usage":"card usage","product_count":"product holdings",
 "has_loan":"loan usage","complaints":"complaints","resolution_days":"complaint resolution time",
 "logins":"login frequency","engagement_decline":"engagement decline","inactivity_days":"inactivity",
 "failed_rate":"failed transaction rate"}

def explain_fallback(feats: dict, proba: float, medians: dict) -> tuple:
    """Deterministic driver ranking: (low-is-bad vs high-is-bad) * deviation."""
    low_bad = {"tenure_months","avg_balance","txn_freq","avg_txn","card_usage","product_count","logins"}
    high_bad = {"complaints","resolution_days","engagement_decline","inactivity_days","failed_rate","age"}
    trend_bad_neg = {"balance_trend","txn_trend"}
    scored = []
    for k, v in feats.items():
        m = medians.get(k, v) or 1
        if k in low_bad:
            dev = (m - v)/abs(m) if m else 0
        elif k in high_bad:
            dev = (v - m)/abs(m) if m else 0
        elif k in trend_bad_neg:
            # Negative balance/txn trend is bad; scale by magnitude, capped at [-1, 1].
            # (Small positive trends count as mildly protective.)
            dev = max(-1.0, min(1.0, -v * 3)) if v < 0 else -0.05
        else:
            dev = 0
        scored.append((k, dev))
    scored.sort(key=lambda x: -x[1])
    pos = [(k, d) for k, d in scored if d > 0.02][:3]
    neg = [(k, d) for k, d in scored if d <= 0.02][:2]
    def phrase(k, d):
        f = feats[k]; m = medians.get(k, f)
        pct = 0
        try: pct = (f-m)/abs(m)*100 if m else 0
        except Exception: pct = 0
        lbl = FEAT_LABELS.get(k, k)
        if k in ("balance_trend","txn_trend"):
            return f"{lbl} {'fell' if f<0 else 'weakened'} ({f:.0%})"
        if pct < 0: return f"{lbl} {pct:.0f}% below typical"
        if pct > 0: return f"{lbl} up {pct:.0f}% vs typical"
        return f"{lbl} at {f}"
    if pos:
        sent = ("Churn risk " + ("is high " if proba >= 0.6 else "increased ") + "primarily because " +
                ", ".join(phrase(k, d) for k, d in pos) + ".")
    else:
        sent = "Churn risk is driven by a mix of stable factors; no single sharp deterioration."
    drivers = [{"feature": k, "label": FEAT_LABELS.get(k, k), "impact": round(float(d), 3),
                "value": feats[k], "typical": medians.get(k)} for k, d in (pos + neg)]
    return drivers, sent

def deterioration(feats: dict) -> tuple:
    parts = []
    if feats.get("txn_trend", 0) < -0.15: parts.append(("declining transactions", 25))
    if feats.get("balance_trend", 0) < -0.1: parts.append(("declining balance", 20))
    if feats.get("card_usage", 1) < 0.3: parts.append(("low card usage", 15))
    if feats.get("engagement_decline", 0) > 0.25: parts.append(("engagement drop", 20))
    if feats.get("complaints", 0) > 0: parts.append(("complaints", 10*min(2, feats["complaints"])))
    if feats.get("failed_rate", 0) > 0.05: parts.append(("failed transactions", 10))
    score = round(min(100, sum(s for _, s in parts)), 1)
    return score, [p[0] for p in parts]

# ---------- audience ----------
def audience_query(db, tenant_id, f: dict):
    from .models import Customer, ChurnPrediction, CustomerValue
    q = db.query(Customer, ChurnPrediction, CustomerValue).join(
        ChurnPrediction, ChurnPrediction.customer_id == Customer.id).join(
        CustomerValue, CustomerValue.customer_id == Customer.id).filter(
        Customer.tenant_id == tenant_id)
    if f.get("min_proba") is not None:
        q = q.filter(ChurnPrediction.proba >= f["min_proba"])
    if f.get("min_clv"):
        q = q.filter(CustomerValue.clv >= f["min_clv"])
    if f.get("segment"):
        q = q.filter(Customer.segment == f["segment"])
    return q.all()

# ---------- product risk (shared by dashboard + analyst; batched: 3 queries total) ----------
def product_risk_rows(db, tenant_id):
    """Per-product risk aggregation, sorted by revenue at risk desc.

    Same numbers as the old per-product N+1 loops, but the mappings, values and bands
    are each fetched once and aggregated in Python.
    """
    from .models import CustomerProduct, CustomerValue, ChurnPrediction, Product
    cps = db.query(CustomerProduct).filter_by(tenant_id=tenant_id).all()
    if not cps:
        return []
    by_prod: dict[int, list[int]] = {}
    for cp in cps:
        by_prod.setdefault(cp.product_id, []).append(cp.customer_id)
    cids = [cp.customer_id for cp in cps]
    rar_by_cust = {v.customer_id: v.revenue_at_risk for v in db.query(CustomerValue).filter(
        CustomerValue.customer_id.in_(cids)).all()}
    band_by_cust = {p.customer_id: p.band for p in db.query(ChurnPrediction).filter(
        ChurnPrediction.customer_id.in_(cids)).all()}
    names = {p.id: p.name for p in db.query(Product).all()}
    out = [{"product": names.get(pid, "?"), "customers": len(ids),
            "high_risk": sum(1 for c in ids if band_by_cust.get(c) == "High"),
            "rar": round(sum(rar_by_cust.get(c, 0) for c in ids), 2)}
           for pid, ids in by_prod.items()]
    return sorted(out, key=lambda x: -x["rar"])

# ---------- AI analyst ----------
CANONICAL_QUESTIONS = [
 "Why did churn risk increase this month?",
 "Which customer segment has the highest revenue at risk?",
 "Which intervention has the best ROI?",
 "How should we spend a ₹10 lakh retention budget?",
 "Show me the top 20 customers to prioritize.",
]

def analyst_context(db, tenant_id):
    from .models import (Customer, ChurnPrediction, CustomerValue, Recommendation,
                         Campaign, Experiment, ExperimentResult)
    from sqlalchemy import func
    total = db.query(Customer).filter_by(tenant_id=tenant_id).count()
    hi = db.query(ChurnPrediction).filter_by(tenant_id=tenant_id, band="High").count()
    med = db.query(ChurnPrediction).filter_by(tenant_id=tenant_id, band="Medium").count()
    lo = db.query(ChurnPrediction).filter_by(tenant_id=tenant_id, band="Low").count()
    rar = db.query(func.sum(CustomerValue.revenue_at_risk)).filter_by(tenant_id=tenant_id).scalar() or 0
    tclv = db.query(func.sum(CustomerValue.clv)).filter_by(tenant_id=tenant_id).scalar() or 0
    avgp = db.query(func.avg(ChurnPrediction.proba)).filter_by(tenant_id=tenant_id).scalar() or 0
    by_seg = db.query(Customer.segment, func.sum(CustomerValue.revenue_at_risk), func.count(Customer.id)).join(
        CustomerValue, CustomerValue.customer_id == Customer.id).filter(
        Customer.tenant_id == tenant_id).group_by(Customer.segment).all()
    top = db.query(Customer.name, ChurnPrediction.proba, CustomerValue.clv, CustomerValue.revenue_at_risk,
        Recommendation.action, Recommendation.priority).join(ChurnPrediction, ChurnPrediction.customer_id == Customer.id).join(
        CustomerValue, CustomerValue.customer_id == Customer.id).join(
        Recommendation, Recommendation.customer_id == Customer.id).filter(
        Customer.tenant_id == tenant_id).order_by(CustomerValue.revenue_at_risk.desc()).limit(20).all()
    acts = db.query(Recommendation.action, func.count(Recommendation.id),
                     func.avg(Recommendation.success)).filter_by(tenant_id=tenant_id).group_by(
                     Recommendation.action).all()
    camps = []
    for c in db.query(Campaign).filter_by(tenant_id=tenant_id).all():
        exp = db.query(Experiment).filter_by(campaign_id=c.id).first()
        res = db.query(ExperimentResult).filter_by(experiment_id=exp.id).first() if exp else None
        camps.append({"name": c.name, "status": c.status, "intervention": c.intervention,
            "roi_pct": round(res.roi * 100, 1) if res else None,
            "revenue": res.revenue if res else 0, "lift": res.lift if res else 0,
            "cost": res.cost if res else 0})
    prods = product_risk_rows(db, tenant_id)
    model = None
    try:
        import json as _j, os as _o
        mp = _o.path.join(_o.path.dirname(__file__), "ml", "artifacts", "metrics.json")
        if _o.path.exists(mp):
            m = _j.load(open(mp))
            model = {"auc": round(m.get("auc", 0), 3), "precision": round(m.get("precision", 0), 3),
                     "recall": round(m.get("recall", 0), 3), "f1": round(m.get("f1", 0), 3), "n": m.get("n", 0)}
    except Exception:
        model = None
    return {"total": total, "high": hi, "medium": med, "low": lo,
        "rar": round(rar, 2), "total_clv": round(tclv, 2), "avg_proba": round(float(avgp), 3),
        "by_segment": [{"segment": s, "rar": round(r or 0, 2), "n": n} for s, r, n in by_seg],
        "top": [{"name": n, "proba": round(p, 3), "clv": round(c, 2), "rar": round(r, 2),
                 "action": a, "priority": pr} for n, p, c, r, a, pr in top],
        "interventions": [{"action": a, "count": c, "avg_success": round(float(s or 0), 3),
                           "cost": ACTIONS.get(a, {}).get("cost", 0)} for a, c, s in acts],
        "campaigns": camps, "products": prods[:5], "model": model}

def find_customer(db, tenant_id, question: str):
    """Find a specific customer mentioned in the question (quoted or 'customer X')."""
    from .models import Customer, ChurnPrediction, CustomerValue, Recommendation, Account, CustomerProduct
    import re as _re
    cands = _re.findall(r'"([^"]+)"', question)
    cands += _re.findall(r"(?:customer|about|for|of|named|called)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)",
                         question, flags=_re.IGNORECASE)
    for cand in cands:
        cand = cand.strip()
        if len(cand) < 3 or cand.lower() in ("the", "top", "best", "high", "risk", "churn"):
            continue
        # Escape LIKE wildcards so names containing % or _ can't broaden the match.
        c = db.query(Customer).filter(Customer.tenant_id == tenant_id,
                                      Customer.name.ilike(f"%{escape_like(cand)}%", escape="\\")).first()
        if c:
            p = db.query(ChurnPrediction).filter_by(customer_id=c.id).first()
            v = db.query(CustomerValue).filter_by(customer_id=c.id).first()
            rec = db.query(Recommendation).filter_by(customer_id=c.id).first()
            bal = sum(a.balance for a in db.query(Account).filter_by(customer_id=c.id).all())
            nprod = db.query(CustomerProduct).filter_by(customer_id=c.id).count()
            return {"name": c.name, "segment": c.segment, "region": c.region,
                "tenure": c.tenure_months, "proba": p.proba if p else 0,
                "band": p.band if p else "?", "trajectory": p.trajectory if p else {},
                "drivers": (p.drivers or [])[:3] if p else [],
                "explanation": p.explanation if p else "",
                "clv": v.clv if v else 0, "rar": v.revenue_at_risk if v else 0,
                "balance": round(bal, 2), "products": nprod,
                "action": rec.action if rec else "?", "cost": rec.cost if rec else 0,
                "success": rec.success if rec else 0, "priority": rec.priority if rec else "?"}
    return None

def _parse_money(question: str):
    """Parse ₹ amounts ('10 lakh', '₹5,00,000', '2 crore'). None without a money cue."""
    import re as _re
    q = question.lower().replace(",", "")
    if not _re.search(r"₹|\brs\.?\b|rupee|\blakh\b|\blac\b|\bcrore\b|\bcr\b|thousand|budget|spend|allocate|invest", q):
        return None
    m = _re.search(r"₹?\s*(\d+(?:\.\d+)?)\s*(lakh|lac|l\b|crore|cr\b|million|thousand|k\b)?", q)
    if not m:
        return None
    val, unit = float(m.group(1)), (m.group(2) or "").strip()
    mult = {"lakh": 1e5, "lac": 1e5, "l": 1e5, "crore": 1e7, "cr": 1e7,
            "million": 1e6, "thousand": 1e3, "k": 1e3}.get(unit, 1)
    return val * mult

def _parse_topn(question: str, default=10, cap=20):
    import re as _re
    m = _re.search(r"top\s*(\d+)", question.lower())
    return max(1, min(cap, int(m.group(1)))) if m else default

def analyst_fallback(question: str, ctx: dict) -> str:
    """Deterministic analyst: routes ANY question to real aggregates. Never invents numbers."""
    import re as _re
    q = question.lower().strip()
    inr = lambda x: f"₹{x:,.0f}"
    top = ctx.get("top", [])

    # 1. greeting / help
    if _re.match(r"^(hi+|hello|hey|namaste|good\s+(morning|afternoon|evening))\b", q) or \
       ("what can you" in q) or q in ("help", "help?"):
        return ("Namaste! I can answer from live portfolio data — try: which segment has the highest "
                "revenue at risk · show top 10 customers · how should we spend ₹5 lakh · how did our "
                "campaigns perform · why is customer \"<name>\" at risk · which product is riskiest · "
                "how accurate is the model?")

    # 2. specific customer (route pre-attaches ctx['customer'])
    cust = ctx.get("customer")
    if cust and ("customer" in q or cust["name"].lower() in q or
                 any(w in q for w in ("who is", "about", "tell me", "why", "detail", "should we"))):
        tr = cust.get("trajectory", {})
        delta = tr.get("today", 0) - tr.get("d30", tr.get("today", 0))
        drv = ", ".join(d.get("label", "") for d in cust.get("drivers", [])) or "mixed factors"
        return (f"{cust['name']} ({cust['segment']}, {cust['region']}, tenure {cust['tenure']} mo): "
                f"churn risk {cust['proba']:.0%} ({cust['band']}), CLV {inr(cust['clv'])}, "
                f"revenue at risk {inr(cust['rar'])}. {cust['explanation']} "
                f"Key drivers: {drv}. 30-day change {delta:+.0%}. Recommended: "
                f"{cust['action'].replace('_', ' ')} (cost {inr(cust['cost'])}, success "
                f"{cust['success']:.0%}) — priority {cust['priority']}. Open Customer 360 for the full view.")

    # 3. budget / spend / allocate (any amount)
    if any(w in q for w in ("budget", "spend", "allocate", "invest", "lakh", "crore")):
        amt = _parse_money(question) or 1_000_000
        unit, succ = 1000, 0.28
        for it in ctx.get("interventions", []):
            if it["action"] == "rm_call":
                unit, succ = it["cost"] or 1000, it["avg_success"] or 0.28
        pool = [t for t in top if t["proba"] >= 0.4] or top
        n = int(amt / max(1, unit))
        targets = pool[:max(1, n)]
        avg = sum(t["clv"] for t in targets) / max(1, len(targets))
        prot = len(targets) * succ * avg
        names = ", ".join(t["name"] for t in targets[:5])
        return (f"With {inr(amt)} at ~{inr(unit)} per outreach you can target ~{num_fmt(len(targets))} "
                f"at-risk customers (avg CLV {inr(avg)}). At {succ:.0%} expected success, estimated "
                f"revenue protected is {inr(prot)}, net value {inr(prot - amt)}. Start with {names} — "
                f"highest revenue at risk, via RM-call/service-recovery. Estimates, not guarantees; "
                f"tune exact numbers in the ROI Simulator.")

    # 4. top / list / prioritize customers
    if any(w in q for w in ("top", "priorit", "list", "show me", "which customers", "whom", "who should")):
        n = _parse_topn(question)
        lines = "; ".join(
            f"{i+1}. {t['name']} (risk {t['proba']:.0%}, RaR {inr(t['rar'])}, {t['action'].replace('_', ' ')})"
            for i, t in enumerate(top[:n]))
        return (f"Top {min(n, len(top))} by revenue at risk: {lines}." if lines
                else "No customers found.")

    # 5. segments
    if "segment" in q:
        b = sorted(ctx.get("by_segment", []), key=lambda x: -x["rar"])
        if not b:
            return "No segment data yet."
        return (f"{b[0]['segment']} carries the highest estimated revenue at risk at {inr(b[0]['rar'])} "
                f"across {b[0]['n']} customers. " +
                " ".join(f"{x['segment']}: {inr(x['rar'])} ({x['n']} cust)." for x in b))

    # 6. interventions / actions / ROI compare
    short_hit = bool(_re.search(r"\b(interventions?|actions?|offers?|cashback|fee|call|recovery|upgrade|loans?|roi)\b", q))
    if short_hit or \
       any(w in q for w in ("best roi", "best action", "best offer", "best intervention",
                            "works best for", "which action", "which offer")):
        rows = sorted(ctx.get("interventions", []), key=lambda x: -x["avg_success"])
        if rows:
            cmp = "; ".join(f"{r['action'].replace('_', ' ')}: {r['count']} customers, "
                            f"{r['avg_success']:.0%} success, {inr(r['cost'])}/each" for r in rows)
            return (f"Modeled intervention performance on your book: {cmp}. Highest success wins per "
                    f"customer via expected net = success × CLV − cost — see Next Best Actions.")
        return ("Service recovery (~35%, ₹700) for complaint churn; RM calls (~30%, ₹1,000) for "
                "high-value disengaged; cashback (~28%, ₹1,200) for spend decline. Expected net = "
                "success × CLV − cost.")

    # 7. campaigns / experiments
    if any(w in q for w in ("campaign", "experiment", "launch", "treatment", "control", "lift", "a/b")):
        camps = ctx.get("campaigns", [])
        if not camps:
            return "No campaigns yet — create one in Campaign Studio, then launch to run the A/B test."
        done = [c for c in camps if c["status"] == "completed"]
        if not done:
            return f"{len(camps)} campaign(s) drafted, none launched yet. Launch one to measure lift vs control."
        best = max(done, key=lambda c: c["roi_pct"] or -1e9)
        lines = "; ".join(f"{c['name']}: lift {c['lift']:.1%}, revenue {inr(c['revenue'])}, "
                          f"ROI {c['roi_pct']}%" for c in done)
        return (f"Completed experiments: {lines}. Best ROI so far: {best['name']} "
                f"({best['roi_pct']}% ROI, {best['lift']:.1%} lift). Outcomes are measured vs control, "
                f"not predicted.")

    # 8. products
    if "product" in q:
        prods = ctx.get("products", [])
        if not prods:
            return "No product data yet."
        lines = "; ".join(f"{p['product']}: {inr(p['rar'])} at risk, {p['high_risk']} high-risk "
                          f"of {p['customers']}" for p in prods)
        return f"Riskiest products by revenue at risk: {lines}."

    # 9. trend / why risk changed
    if any(w in q for w in ("trend", "increas", "decreas", "chang", "why", "spike", "deteriorat",
                            "month", "engagement", "complaint")):
        return (f"{ctx['high']} of {ctx['total']} customers are high risk (≥60%), {ctx['medium']} "
                f"medium, {ctx.get('low', 0)} low; average predicted risk {ctx.get('avg_proba', 0):.1%}. "
                f"Across the book the sharpest deterioration signals are falling transaction frequency, "
                f"balance decline, engagement drops and rising complaints — see Analytics → Deterioration. "
                f"Estimated revenue at risk is {inr(ctx['rar'])}.")

    # 10. value / CLV / worth
    if any(w in q for w in ("clv", "lifetime", "value", "worth", "valuable", "hni")):
        return (f"Total estimated customer value is {inr(ctx.get('total_clv', 0))} across "
                f"{ctx['total']} customers; {inr(ctx['rar'])} of it is at risk "
                f"(churn probability × CLV). Highest-value at-risk accounts sit in "
                f"{(sorted(ctx.get('by_segment', []), key=lambda x: -x['rar']) or [{}])[0].get('segment', '?')} — "
                f"open Segments to prioritize.")

    # 11. model accuracy / performance
    if any(w in q for w in ("model", "accura", "auc", "precision", "recall", "perform", "predict")):
        m = ctx.get("model")
        if m:
            return (f"Churn model (XGBoost primary, logistic baseline, trained on {m['n']} customers): "
                    f"AUC {m['auc']}, precision {m['precision']}, recall {m['recall']}, F1 {m['f1']}. "
                    f"Full confusion matrix on the Risk page.")
        return ("Model metrics appear on the Risk page after training (Data → Retrain).")

    # 12. counts
    if any(w in q for w in ("how many", "count", "number of")):
        if "campaign" in q:
            return f"{len(ctx.get('campaigns', []))} campaigns exist."
        if "high" in q:
            return f"{ctx['high']} high-risk customers (≥60% churn probability)."
        if "medium" in q:
            return f"{ctx['medium']} medium-risk customers."
        if "low" in q:
            return f"{ctx.get('low', 0)} low-risk customers."
        return f"{ctx['total']} customers in this workspace ({ctx['high']} high risk)."

    # 13. definitions (only for known terms — other "what..." falls to smart default)
    if _re.match(r"^(what\s+(is|are)|define|meaning\s+of|explain\s+(what|the\s+term))", q) or \
       ("what" in q.split()[:2] and any(t in q for t in
        ("revenue at risk", "rar", "clv", "lifetime value", "roi", "churn", "priority", "retainiq"))):
        if "revenue at risk" in q or q.strip() == "what is rar":
            return ("Revenue at Risk = churn probability × CLV, summed per customer. It is a predicted "
                    f"estimate ({inr(ctx['rar'])} here), not money already lost.")
        if "clv" in q or "lifetime" in q:
            return ("CLV = (balance margin + transaction margin + product income − complaint cost) × "
                    "expected years. A transparent estimate used to rank who is worth saving.")
        if "roi" in q:
            return ("ROI = (revenue protected − campaign cost) / campaign cost. Revenue protected = "
                    "retained customers × avg CLV. Simulate it live in the ROI Simulator.")
        if "churn" in q:
            return (f"Churn probability is the model's 90-day leave-risk per customer; bands are Low <35%, "
                    f"Medium 35–60%, High ≥60%. Right now {ctx['high']} customers are High.")
        return ("RetainIQ = detect who is at risk → explain why → value them → recommend the action → "
                "simulate ROI → run A/B campaigns → measure. Ask me about segments, budgets, customers, "
                "campaigns, products or the model.")

    # 14. smart default: still answers with the most useful numbers, not a dead end
    names = "; ".join(f"{t['name']} ({t['proba']:.0%}, {inr(t['rar'])})" for t in top[:5])
    n_camp = len(ctx.get("campaigns", []))
    return (f"Portfolio: {ctx['total']} customers — {ctx['high']} high risk, {ctx['medium']} medium; "
            f"estimated revenue at risk {inr(ctx['rar'])}; {n_camp} campaign(s) run. "
            f"Highest-risk value: {names}. "
            f"I can go deeper — ask e.g. 'why is customer \"<name>\" at risk?', 'compare interventions', "
            f"'how did campaigns perform?', 'which product is riskiest?', or 'how should we spend ₹5 lakh?'")

def num_fmt(n):
    try:
        return f"{int(n):,}"
    except Exception:
        return str(n)


def escape_like(s: str) -> str:
    """Escape SQL LIKE wildcards so user search text can't alter match semantics."""
    return str(s or "").replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

def analyst_llm(question: str, ctx: dict) -> str | None:
    """Call Gemini or OpenAI if keys exist. Returns None on any failure → fallback.

    PRIVACY NOTE: ctx contains customer names + aggregate financial estimates. It is sent
    to the external provider only when an operator-configured API key exists, truncated to
    6k chars, and never logged. Self-hosted deployments that must not exfiltrate PII should
    unset both keys (the deterministic fallback answers everything locally).
    """
    import json, httpx
    gem = os.getenv("GEMINI_API_KEY"); oai = os.getenv("OPENAI_API_KEY")
    ctx_s = json.dumps(ctx)[:6000]
    sys = ("You are RetainIQ analyst. Answer ONLY from the JSON context. "
           "All money is INR estimates/predictions, never realized. Be concise.")
    try:
        if gem:
            r = httpx.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gem}",
                json={"system_instruction": {"parts": [{"text": sys}]},
                      "contents": [{"parts": [{"text": f"Context: {ctx_s}\nQuestion: {question}"}]}]},
                timeout=15)
            if r.status_code == 200:
                return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        elif oai:
            r = httpx.post("https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {oai}"},
                json={"model": "gpt-4o-mini", "messages": [
                    {"role": "system", "content": sys},
                    {"role": "user", "content": f"Context: {ctx_s}\nQuestion: {question}"}]},
                timeout=15)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
    except Exception:
        return None
    return None
