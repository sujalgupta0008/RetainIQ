"""All domain logic as plain functions. ROI formulas centralized here (tested)."""
import datetime as dt
import hashlib
import json
import os
import re

import jwt
from sqlalchemy import func

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


def hash_pw(pw: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 100_000).hex()

def make_token(user_id: int, tenant_id: int, role: str) -> str:
    now_utc = dt.datetime.now(dt.timezone.utc)
    payload = {"sub": str(user_id), "tenant_id": tenant_id, "role": role,
               "iat": now_utc, "exp": now_utc + dt.timedelta(hours=24)}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])


def audit(db, tenant_id, user_id, action, meta=""):
    from .models import AuditLog
    db.add(AuditLog(tenant_id=tenant_id, user_id=user_id, action=action, meta=str(meta)[:2000]))


def calc_clv(avg_balance, annual_txn_vol, product_count, complaints_1y, tenure_months) -> tuple:
    contrib = avg_balance*0.035 + annual_txn_vol*0.002 + product_count*1200 - complaints_1y*500
    contrib = max(500.0, float(contrib))
    years = min(7.0, 3.0 + tenure_months/24.0)
    return round(contrib*years, 2), round(contrib, 2)

def calc_rar(churn_proba, clv) -> float:
    return round(float(churn_proba)*float(clv), 2)

def expected_roi_value(success: float, clv: float, cost: float) -> float:
    """Expected ROI for a single recommendation. Zero-cost actions have no
    incremental spend, so ROI is defined as 0.0 instead of success*CLV/1."""
    success = max(0.0, float(success or 0.0))
    clv = max(0.0, float(clv or 0.0))
    cost = max(0.0, float(cost or 0.0))
    if cost <= 0:
        return 0.0
    return round((success * clv - cost) / cost, 3)


def calc_roi(targeted: int, success_rate: float, avg_value: float, unit_cost: float, reach: float = 1.0) -> dict:
    """Central ROI engine. All estimates labeled by callers."""
    # Clamp stale-client values so outputs stay sane; schemas enforce the same bounds.
    targeted = max(0, int(targeted or 0))
    success_rate = min(1.0, max(0.0, float(success_rate or 0.0)))
    avg_value = max(0.0, float(avg_value or 0.0))
    unit_cost = max(0.0, float(unit_cost or 0.0))
    reach = min(1.0, max(0.0, float(reach if reach is not None else 1.0)))
    reached = int(round(targeted*reach))
    retained = reached*success_rate
    cost = reached*unit_cost
    revenue = retained*avg_value
    net = revenue - cost
    roi = (net/cost) if cost > 0 else 0.0
    break_even = (unit_cost/avg_value) if avg_value > 0 else 1.0
    return {"targeted": targeted, "reached": reached, "retained": round(retained,1), "cost": round(cost,2),
           "revenue": round(revenue,2), "net": round(net,2),
           "roi": round(roi,4), "roi_pct": round(roi*100,1),
           "break_even_rate": round(break_even,4)}

def scenarios(base: dict, success_rate: float) -> dict:
    # Base audience is the actually-reached cohort (back-compat: older payloads
    # only carried "targeted" as reached).
    audience = base.get("reached", base.get("targeted", 0))
    def row(mult):
        rate = min(0.9, success_rate*mult)
        retained = audience*rate
        revenue = retained*(base["revenue"]/base["retained"] if base["retained"] else 0)
        net = revenue - base["cost"]
        roi = net/base["cost"] if base["cost"] else 0
        return {"success": round(rate,3), "retained": round(retained,1), "revenue": round(revenue,2),
                "net": round(net,2), "roi_pct": round(roi*100,1)}
    return {"conservative": row(0.6), "expected": row(1.0), "optimistic": row(1.4)}

def band(proba: float) -> str:
    return "High" if proba >= 0.6 else ("Medium" if proba >= 0.35 else "Low")

def priority_of(proba, clv, rar, cost, success, clv_max, rar_max) -> tuple:
    score = (0.5*(rar/max(1,rar_max)) + 0.3*proba + 0.2*(clv/max(1,clv_max)))*100
    score = round(max(0, min(100, score)), 1)
    if proba >= 0.6 and score >= 45:
        return score, "Critical"
    if proba >= 0.4 and score >= 30:
        return score, "High Priority"
    if proba >= 0.35 or score >= 20:
        return score, "Monitor"
    return score, "Low Priority"

def pick_action(feats: dict, clv: float) -> tuple:
    """Rule-boosted max(expected net). Returns (key, success_adj, reason)."""
    complaints = feats.get("complaints", 0)
    bal_trend = feats.get("balance_trend", 0)
    eng_drop = feats.get("engagement_decline", 0)
    n_products = feats.get("product_count", 1)
    best_key, best_value, best_rate, reason = "personalized_offer", -1e18, 0.25, ""
    for key, cfg in ACTIONS.items():
        rate = cfg["success"]
        why = f"Base success {rate:.0%} for {cfg['label']}."
        if key == "service_recovery" and complaints > 0:
            rate = min(0.6, rate + 0.1*complaints); why = f"{complaints} complaint(s) — service recovery has highest win-back."
        if key == "cashback" and bal_trend < -0.1:
            rate += 0.05; why = f"Balance down {bal_trend:.0%} — cashback re-activates spend."
        if key == "rm_call" and (eng_drop > 0.25 or clv > 150000):
            rate += 0.05; why = "High value or disengaged — human outreach works best."
        if key == "personalized_offer" and n_products <= 1:
            rate += 0.04; why = "Single-product holder — cross-sell offer deepens relationship."
        if key == "no_intervention" and clv < 20000:
            why = "Low value — cost of action exceeds likely return."
        value = rate*clv - cfg["cost"]
        if value > best_value:
            best_key, best_value, best_rate, reason = key, value, rate, why
    return best_key, round(min(0.9, best_rate), 3), reason


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
    for name, value in feats.items():
        typical = medians.get(name, value) or 1
        if name in low_bad:
            dev = (typical - value)/abs(typical) if typical else 0
        elif name in high_bad:
            dev = (value - typical)/abs(typical) if typical else 0
        elif name in trend_bad_neg:
            # Negative trend is bad; small positive trends count as mildly protective.
            dev = max(-1.0, min(1.0, -value * 3)) if value < 0 else -0.05
        else:
            dev = 0
        scored.append((name, dev))
    scored.sort(key=lambda x: -x[1])
    pos = [(k, d) for k, d in scored if d > 0.02][:3]
    neg = [(k, d) for k, d in scored if d <= 0.02][:2]
    def describe(name, dev):
        value = feats[name]; typical = medians.get(name, value)
        try:
            pct = (value-typical)/abs(typical)*100 if typical else 0
        except (TypeError, ZeroDivisionError, ValueError):
            pct = 0
        label = FEAT_LABELS.get(name, name)
        if name in ("balance_trend","txn_trend"):
            return f"{label} {'fell' if value<0 else 'weakened'} ({value:.0%})"
        if pct < 0: return f"{label} {pct:.0f}% below typical"
        if pct > 0: return f"{label} up {pct:.0f}% vs typical"
        return f"{label} at {value}"
    if pos:
        sent = ("Churn risk " + ("is high " if proba >= 0.6 else "increased ") + "primarily because " +
                ", ".join(describe(k, d) for k, d in pos) + ".")
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


def audience_query(db, tenant_id, filters: dict):
    from .models import Customer, ChurnPrediction, CustomerValue
    query = db.query(Customer, ChurnPrediction, CustomerValue).join(
        ChurnPrediction, ChurnPrediction.customer_id == Customer.id).join(
        CustomerValue, CustomerValue.customer_id == Customer.id).filter(
        Customer.tenant_id == tenant_id)
    if filters.get("min_proba") is not None:
        query = query.filter(ChurnPrediction.proba >= filters["min_proba"])
    if filters.get("min_clv"):
        query = query.filter(CustomerValue.clv >= filters["min_clv"])
    if filters.get("segment"):
        query = query.filter(Customer.segment == filters["segment"])
    return query.all()


def product_risk_rows(db, tenant_id):
    """Per-product risk aggregation, sorted by revenue at risk desc (3 queries, no N+1)."""
    from .models import CustomerProduct, CustomerValue, ChurnPrediction, Product
    links = db.query(CustomerProduct).filter_by(tenant_id=tenant_id).all()
    if not links:
        return []
    by_product: dict[int, list[int]] = {}
    for link in links:
        by_product.setdefault(link.product_id, []).append(link.customer_id)
    cust_ids = [link.customer_id for link in links]
    rar_by_cust = {v.customer_id: v.revenue_at_risk for v in db.query(CustomerValue).filter(
        CustomerValue.customer_id.in_(cust_ids)).all()}
    band_by_cust = {p.customer_id: p.band for p in db.query(ChurnPrediction).filter(
        ChurnPrediction.customer_id.in_(cust_ids)).all()}
    names = {p.id: p.name for p in db.query(Product).all()}
    out = [{"product": names.get(pid, "?"), "customers": len(ids),
            "high_risk": sum(1 for c in ids if band_by_cust.get(c) == "High"),
            "rar": round(sum(rar_by_cust.get(c, 0) for c in ids), 2)}
           for pid, ids in by_product.items()]
    return sorted(out, key=lambda x: -x["rar"])


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
    for camp in db.query(Campaign).filter_by(tenant_id=tenant_id).all():
        exp = db.query(Experiment).filter_by(campaign_id=camp.id).first()
        res = db.query(ExperimentResult).filter_by(experiment_id=exp.id).first() if exp else None
        camps.append({"name": camp.name, "status": camp.status, "intervention": camp.intervention,
            "roi_pct": round(res.roi * 100, 1) if res else None,
            "revenue": res.revenue if res else 0, "lift": res.lift if res else 0,
            "cost": res.cost if res else 0})
    prods = product_risk_rows(db, tenant_id)
    model = None
    try:
        mp = os.path.join(os.path.dirname(__file__), "ml", "artifacts", "metrics.json")
        if os.path.exists(mp):
            with open(mp) as f:
                m = json.load(f)
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
    names = re.findall(r'"([^"]+)"', question)
    names += re.findall(r"(?:customer|about|for|of|named|called)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)",
                         question, flags=re.IGNORECASE)
    for name in names:
        name = name.strip()
        if len(name) < 3 or name.lower() in ("the", "top", "best", "high", "risk", "churn"):
            continue
        # Escape LIKE wildcards so names containing % or _ can't broaden the match.
        cust = db.query(Customer).filter(Customer.tenant_id == tenant_id,
                                      Customer.name.ilike(f"%{escape_like(name)}%", escape="\\")).first()
        if cust:
            pred = db.query(ChurnPrediction).filter_by(customer_id=cust.id).first()
            val = db.query(CustomerValue).filter_by(customer_id=cust.id).first()
            reco = db.query(Recommendation).filter_by(customer_id=cust.id).first()
            bal = sum(a.balance for a in db.query(Account).filter_by(customer_id=cust.id).all())
            nprod = db.query(CustomerProduct).filter_by(customer_id=cust.id).count()
            return {"name": cust.name, "segment": cust.segment, "region": cust.region,
                "tenure": cust.tenure_months, "proba": pred.proba if pred else 0,
                "band": pred.band if pred else "?", "trajectory": pred.trajectory if pred else {},
                "drivers": (pred.drivers or [])[:3] if pred else [],
                "explanation": pred.explanation if pred else "",
                "clv": val.clv if val else 0, "rar": val.revenue_at_risk if val else 0,
                "balance": round(bal, 2), "products": nprod,
                "action": reco.action if reco else "?", "cost": reco.cost if reco else 0,
                "success": reco.success if reco else 0, "priority": reco.priority if reco else "?"}
    return None

def _parse_money(question: str):
    """Parse ₹ amounts ('10 lakh', '₹5,00,000', '2 crore'). None without a money cue."""
    text = question.lower().replace(",", "")
    if not re.search(r"₹|\brs\.?\b|rupee|\blakh\b|\blac\b|\bcrore\b|\bcr\b|thousand|budget|spend|allocate|invest", text):
        return None
    m = re.search(r"₹?\s*(\d+(?:\.\d+)?)\s*(lakh|lac|l\b|crore|cr\b|million|thousand|k\b)?", text)
    if not m:
        return None
    val, unit = float(m.group(1)), (m.group(2) or "").strip()
    mult = {"lakh": 1e5, "lac": 1e5, "l": 1e5, "crore": 1e7, "cr": 1e7,
            "million": 1e6, "thousand": 1e3, "k": 1e3}.get(unit, 1)
    return val * mult

def _parse_topn(question: str, default=10, cap=20):
    m = re.search(r"top\s*(\d+)", question.lower())
    return max(1, min(cap, int(m.group(1)))) if m else default

def analyst_fallback(question: str, ctx: dict) -> str:
    """Deterministic analyst: routes ANY question to real aggregates. Never invents numbers."""
    text = question.lower().strip()
    def inr(x):
        return f"₹{x:,.0f}"
    top = ctx.get("top", [])

    # greeting / help
    if re.match(r"^(hi+|hello|hey|namaste|good\s+(morning|afternoon|evening))\b", text) or \
       ("what can you" in text) or text in ("help", "help?"):
        return ("Namaste! I can answer from live portfolio data — try: which segment has the highest "
                "revenue at risk · show top 10 customers · how should we spend ₹5 lakh · how did our "
                "campaigns perform · why is customer \"<name>\" at risk · which product is riskiest · "
                "how accurate is the model?")

    # specific customer (route pre-attaches ctx['customer'])
    cust = ctx.get("customer")
    if cust and ("customer" in text or cust["name"].lower() in text or
                 any(w in text for w in ("who is", "about", "tell me", "why", "detail", "should we"))):
        traj = cust.get("trajectory", {})
        delta = traj.get("today", 0) - traj.get("d30", traj.get("today", 0))
        drv = ", ".join(d.get("label", "") for d in cust.get("drivers", [])) or "mixed factors"
        return (f"{cust['name']} ({cust['segment']}, {cust['region']}, tenure {cust['tenure']} mo): "
                f"churn risk {cust['proba']:.0%} ({cust['band']}), CLV {inr(cust['clv'])}, "
                f"revenue at risk {inr(cust['rar'])}. {cust['explanation']} "
                f"Key drivers: {drv}. 30-day change {delta:+.0%}. Recommended: "
                f"{cust['action'].replace('_', ' ')} (cost {inr(cust['cost'])}, success "
                f"{cust['success']:.0%}) — priority {cust['priority']}. Open Customer 360 for the full view.")

    # budget / spend / allocate (any amount)
    if any(w in text for w in ("budget", "spend", "allocate", "invest", "lakh", "crore")):
        amt = _parse_money(question) or 1_000_000
        unit, succ = 1000, 0.28
        for item in ctx.get("interventions", []):
            if item["action"] == "rm_call":
                unit, succ = item["cost"] or 1000, item["avg_success"] or 0.28
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

    # top / list / prioritize customers
    if any(w in text for w in ("top", "priorit", "list", "show me", "which customers", "whom", "who should")):
        n = _parse_topn(question)
        lines = "; ".join(
            f"{i+1}. {t['name']} (risk {t['proba']:.0%}, RaR {inr(t['rar'])}, {t['action'].replace('_', ' ')})"
            for i, t in enumerate(top[:n]))
        return (f"Top {min(n, len(top))} by revenue at risk: {lines}." if lines
                else "No customers found.")

    # segments
    if "segment" in text:
        ranked = sorted(ctx.get("by_segment", []), key=lambda x: -x["rar"])
        if not ranked:
            return "No segment data yet."
        return (f"{ranked[0]['segment']} carries the highest estimated revenue at risk at {inr(ranked[0]['rar'])} "
                f"across {ranked[0]['n']} customers. " +
                " ".join(f"{x['segment']}: {inr(x['rar'])} ({x['n']} cust)." for x in ranked))

    # interventions / actions / ROI compare
    mentions_action = bool(re.search(r"\b(interventions?|actions?|offers?|cashback|fee|call|recovery|upgrade|loans?|roi)\b", text))
    if mentions_action or \
       any(w in text for w in ("best roi", "best action", "best offer", "best intervention",
                            "works best for", "which action", "which offer")):
        rows = sorted(ctx.get("interventions", []), key=lambda x: -x["avg_success"])
        if rows:
            compare = "; ".join(f"{r['action'].replace('_', ' ')}: {r['count']} customers, "
                            f"{r['avg_success']:.0%} success, {inr(r['cost'])}/each" for r in rows)
            return (f"Modeled intervention performance on your book: {compare}. Highest success wins per "
                    f"customer via expected net = success × CLV − cost — see Next Best Actions.")
        return ("Service recovery (~35%, ₹700) for complaint churn; RM calls (~30%, ₹1,000) for "
                "high-value disengaged; cashback (~28%, ₹1,200) for spend decline. Expected net = "
                "success × CLV − cost.")

    # campaigns / experiments
    if any(w in text for w in ("campaign", "experiment", "launch", "treatment", "control", "lift", "a/b")):
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

    # products
    if "product" in text:
        prods = ctx.get("products", [])
        if not prods:
            return "No product data yet."
        lines = "; ".join(f"{p['product']}: {inr(p['rar'])} at risk, {p['high_risk']} high-risk "
                          f"of {p['customers']}" for p in prods)
        return f"Riskiest products by revenue at risk: {lines}."

    # trend / why risk changed
    if any(w in text for w in ("trend", "increas", "decreas", "chang", "why", "spike", "deteriorat",
                            "month", "engagement", "complaint")):
        return (f"{ctx['high']} of {ctx['total']} customers are high risk (≥60%), {ctx['medium']} "
                f"medium, {ctx.get('low', 0)} low; average predicted risk {ctx.get('avg_proba', 0):.1%}. "
                f"Across the book the sharpest deterioration signals are falling transaction frequency, "
                f"balance decline, engagement drops and rising complaints — see Analytics → Deterioration. "
                f"Estimated revenue at risk is {inr(ctx['rar'])}.")

    # value / CLV / worth
    if any(w in text for w in ("clv", "lifetime", "value", "worth", "valuable", "hni")):
        return (f"Total estimated customer value is {inr(ctx.get('total_clv', 0))} across "
                f"{ctx['total']} customers; {inr(ctx['rar'])} of it is at risk "
                f"(churn probability × CLV). Highest-value at-risk accounts sit in "
                f"{(sorted(ctx.get('by_segment', []), key=lambda x: -x['rar']) or [{}])[0].get('segment', '?')} — "
                f"open Segments to prioritize.")

    # model accuracy / performance
    if any(w in text for w in ("model", "accura", "auc", "precision", "recall", "perform", "predict")):
        m = ctx.get("model")
        if m:
            return (f"Churn model (XGBoost primary, logistic baseline, trained on {m['n']} customers): "
                    f"AUC {m['auc']}, precision {m['precision']}, recall {m['recall']}, F1 {m['f1']}. "
                    f"Full confusion matrix on the Risk page.")
        return ("Model metrics appear on the Risk page after training (Data → Retrain).")

    # counts
    if any(w in text for w in ("how many", "count", "number of")):
        if "campaign" in text:
            return f"{len(ctx.get('campaigns', []))} campaigns exist."
        if "high" in text:
            return f"{ctx['high']} high-risk customers (≥60% churn probability)."
        if "medium" in text:
            return f"{ctx['medium']} medium-risk customers."
        if "low" in text:
            return f"{ctx.get('low', 0)} low-risk customers."
        return f"{ctx['total']} customers in this workspace ({ctx['high']} high risk)."

    # definitions (only for known terms — other "what..." falls to smart default)
    if re.match(r"^(what\s+(is|are)|define|meaning\s+of|explain\s+(what|the\s+term))", text) or \
       ("what" in text.split()[:2] and any(t in text for t in
        ("revenue at risk", "rar", "clv", "lifetime value", "roi", "churn", "priority", "retainiq"))):
        if "revenue at risk" in text or text.strip() == "what is rar":
            return ("Revenue at Risk = churn probability × CLV, summed per customer. It is a predicted "
                    f"estimate ({inr(ctx['rar'])} here), not money already lost.")
        if "clv" in text or "lifetime" in text:
            return ("CLV = (balance margin + transaction margin + product income − complaint cost) × "
                    "expected years. A transparent estimate used to rank who is worth saving.")
        if "roi" in text:
            return ("ROI = (revenue protected − campaign cost) / campaign cost. Revenue protected = "
                    "retained customers × avg CLV. Simulate it live in the ROI Simulator.")
        if "churn" in text:
            return (f"Churn probability is the model's 90-day leave-risk per customer; bands are Low <35%, "
                    f"Medium 35–60%, High ≥60%. Right now {ctx['high']} customers are High.")
        return ("RetainIQ = detect who is at risk → explain why → value them → recommend the action → "
                "simulate ROI → run A/B campaigns → measure. Ask me about segments, budgets, customers, "
                "campaigns, products or the model.")

    # smart default: still answers with the most useful numbers, not a dead end
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
    # httpx stays a local import so the app runs without it when no LLM keys are set.
    import httpx
    gem_key = os.getenv("GEMINI_API_KEY"); oai_key = os.getenv("OPENAI_API_KEY")
    ctx_json = json.dumps(ctx)[:6000]
    system = ("You are RetainIQ analyst. Answer ONLY from the JSON context. "
           "All money is INR estimates/predictions, never realized. Be concise.")
    try:
        if gem_key:
            r = httpx.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gem_key}",
                json={"system_instruction": {"parts": [{"text": system}]},
                      "contents": [{"parts": [{"text": f"Context: {ctx_json}\nQuestion: {question}"}]}]},
                timeout=15)
            if r.status_code == 200:
                return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        elif oai_key:
            r = httpx.post("https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {oai_key}"},
                json={"model": "gpt-4o-mini", "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": f"Context: {ctx_json}\nQuestion: {question}"}]},
                timeout=15)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
    except Exception:
        return None
    return None
