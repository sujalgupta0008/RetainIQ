"""Synthetic seed. Run: python -m backend.seed [--reset]  (deterministic, SEED=42)"""
import os, sys, random, math
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, SessionLocal, Base
from backend import models as M
from backend.services import (calc_clv, calc_rar, band, priority_of, pick_action,
    explain_fallback, deterioration, hash_pw, audit, FEATURES, ACTIONS)

SEED = int(os.getenv("SEED", "42"))
FIRST = ["Aarav","Priya","Rohan","Sneha","Arjun","Meera","Kabir","Ananya","Vikram","Divya","Aditya","Kavya","Nikhil","Riya","Suresh","Lakshmi","Manoj","Pooja","Kiran","Anil"]
LAST = ["Sharma","Patel","Iyer","Reddy","Khan","Gupta","Nair","Singh","Das","Kulkarni","Mehta","Joshi","Chopra","Verma","Rao"]
REGIONS = ["Mumbai","Delhi","Bengaluru","Hyderabad","Chennai","Pune","Kolkata","Ahmedabad"]
PRODUCTS = [("Everyday Savings","deposit"),("Salary Current","deposit"),("Platinum Credit Card","card"),
            ("Personal Loan","loan"),("Life Insurance","insurance"),("Wealth Invest","investment")]
SEGMENTS = ["Mass","Affluent","HNI","SME"]

def run(reset=False):
    rnd = random.Random(SEED)
    if reset:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = SessionLocal()
    if db.query(M.Tenant).count() > 0 and not reset:
        print("already seeded, use --reset"); return
    if reset:
        for t in [M.AuditLog, M.ExperimentResult, M.Experiment, M.CampaignTarget, M.Campaign,
                  M.Recommendation, M.CustomerValue, M.ChurnPrediction, M.CustomerFeature,
                  M.Interaction, M.Transaction, M.CustomerProduct, M.Account, M.Customer, M.User, M.Tenant, M.Product]:
            db.query(t).delete()
        db.commit()
    bank = M.Tenant(name="Demo Bank"); fin = M.Tenant(name="Demo Fintech")
    db.add_all([bank, fin]); db.flush()
    for p, c in PRODUCTS:
        db.add(M.Product(name=p, category=c))
    db.flush()
    prods = db.query(M.Product).all()
    users = [("admin@demobank.in", bank.id, "admin"), ("manager@demobank.in", bank.id, "manager"),
             ("admin@demofintech.in", fin.id, "admin"), ("manager@demofintech.in", fin.id, "manager")]
    for email, tid, role in users:
        salt = "".join(rnd.choices("abcdef0123456789", k=16))
        db.add(M.User(tenant_id=tid, email=email, salt=salt, pw_hash=hash_pw("demo123", salt), role=role))
    db.flush()

    def make_customers(tenant_id, n, tag):
        now = datetime.utcnow()
        for i in range(n):
            arch = rnd.random()  # loyal .45 / declining .25 / volatile .15 / new .15
            if arch < 0.45: risk_t = "loyal"
            elif arch < 0.70: risk_t = "declining"
            elif arch < 0.85: risk_t = "volatile"
            else: risk_t = "new"
            tenure = rnd.randint(48, 120) if risk_t == "loyal" else (rnd.randint(3, 14) if risk_t == "new" else rnd.randint(6, 60))
            age = rnd.randint(24, 65); income = rnd.choice([450000, 700000, 1200000, 2500000, 5000000])
            seg = "HNI" if income >= 2500000 else ("Affluent" if income >= 1000000 else ("SME" if rnd.random() < 0.12 else "Mass"))
            c = M.Customer(tenant_id=tenant_id, name=f"{rnd.choice(FIRST)} {rnd.choice(LAST)}",
                           age=age, income=income, tenure_months=tenure,
                           region=rnd.choice(REGIONS), segment=seg)
            db.add(c); db.flush()
            avg_bal = rnd.uniform(80000, 900000) * (1.6 if seg in ("HNI", "Affluent") else 1.0)
            if risk_t == "declining": avg_bal *= rnd.uniform(0.5, 0.8)
            n_acct = rnd.randint(1, 3)
            for a in range(n_acct):
                db.add(M.Account(tenant_id=tenant_id, customer_id=c.id,
                       type=rnd.choice(["savings", "current", "fixed"]),
                       balance=round(avg_bal/n_acct*rnd.uniform(0.7, 1.3), 2)))
            n_prod = rnd.randint(3, 5) if risk_t == "loyal" else (1 if risk_t == "new" else rnd.randint(1, 3))
            for p in rnd.sample(prods, min(n_prod, len(prods))):
                db.add(M.CustomerProduct(tenant_id=tenant_id, customer_id=c.id, product_id=p.id))
            has_loan = any(p.category == "loan" for p in rnd.sample(prods, 1)) or (rnd.random() < 0.3)
            # behavior params
            if risk_t == "loyal":
                freq, avg_txn, card, logins, eng, inact, fail = rnd.uniform(10, 25), rnd.uniform(3000, 9000), rnd.uniform(0.5, 0.9), rnd.uniform(12, 28), rnd.uniform(0, 0.1), rnd.randint(0, 5), rnd.uniform(0, 0.02)
                bal_tr, txn_tr, complaints = rnd.uniform(-0.02, 0.08), rnd.uniform(-0.05, 0.1), 0 if rnd.random() < 0.9 else 1
            elif risk_t == "declining":
                freq, avg_txn, card, logins, eng, inact, fail = rnd.uniform(2, 7), rnd.uniform(1500, 5000), rnd.uniform(0.05, 0.3), rnd.uniform(1, 6), rnd.uniform(0.3, 0.7), rnd.randint(15, 60), rnd.uniform(0.03, 0.12)
                bal_tr, txn_tr, complaints = rnd.uniform(-0.45, -0.12), rnd.uniform(-0.5, -0.15), rnd.randint(1, 4)
            elif risk_t == "volatile":
                freq, avg_txn, card, logins, eng, inact, fail = rnd.uniform(5, 14), rnd.uniform(2000, 7000), rnd.uniform(0.2, 0.6), rnd.uniform(5, 14), rnd.uniform(0.1, 0.35), rnd.randint(3, 20), rnd.uniform(0.01, 0.06)
                bal_tr, txn_tr, complaints = rnd.uniform(-0.15, 0.15), rnd.uniform(-0.2, 0.2), rnd.randint(0, 2)
            else:
                freq, avg_txn, card, logins, eng, inact, fail = rnd.uniform(3, 10), rnd.uniform(1500, 4500), rnd.uniform(0.2, 0.5), rnd.uniform(6, 16), rnd.uniform(0, 0.2), rnd.randint(0, 10), rnd.uniform(0, 0.04)
                bal_tr, txn_tr, complaints = rnd.uniform(-0.05, 0.15), rnd.uniform(-0.05, 0.2), 0 if rnd.random() < 0.85 else 1
            res_days = round(rnd.uniform(1, 12) if complaints else rnd.uniform(0.5, 2), 1)
            feats = {"tenure_months": tenure, "age": age, "income": income, "avg_balance": round(avg_bal, 2),
                "balance_trend": round(bal_tr, 3), "txn_freq": round(freq, 1), "avg_txn": round(avg_txn, 2),
                "txn_trend": round(txn_tr, 3), "card_usage": round(card, 3), "product_count": n_prod,
                "has_loan": 1 if has_loan else 0, "complaints": complaints, "resolution_days": res_days,
                "logins": round(logins, 1), "engagement_decline": round(eng, 3),
                "inactivity_days": inact, "failed_rate": round(fail, 4)}
            label = 1 if (risk_t == "declining" and rnd.random() < 0.75) or (risk_t == "volatile" and rnd.random() < 0.3) or (rnd.random() < 0.05) else 0
            db.add(M.CustomerFeature(tenant_id=tenant_id, customer_id=c.id, f=feats, label=label))
            # 12 months of transactions (1 aggregated row per month + noise rows for recency)
            for m in range(12):
                decay = 1.0 if m > 2 else (1 + txn_tr)  # recent months reflect trend
                amt = round(avg_txn*freq*decay*rnd.uniform(0.8, 1.2), 2)
                db.add(M.Transaction(tenant_id=tenant_id, customer_id=c.id, amount=amt,
                       ts=now - timedelta(days=30*m + rnd.randint(0, 20)), type="debit"))
            for _ in range(complaints):
                db.add(M.Interaction(tenant_id=tenant_id, customer_id=c.id, kind="complaint",
                       severity=rnd.randint(2, 5), resolved=rnd.random() < 0.7,
                       resolution_days=res_days, ts=now - timedelta(days=rnd.randint(5, 200)),
                       note="Service complaint (synthetic)"))
            for _ in range(rnd.randint(0, 3)):
                db.add(M.Interaction(tenant_id=tenant_id, customer_id=c.id, kind=rnd.choice(["call", "visit", "login"]),
                       severity=1, resolved=True, resolution_days=0.5,
                       ts=now - timedelta(days=rnd.randint(1, 90)), note="Engagement (synthetic)"))
        db.flush()

    make_customers(bank.id, 400, "bank")
    make_customers(fin.id, 200, "fintech")

    # predictions + values + recommendations (uses rule model; retrain later upgrades artifacts)
    from backend.ml.infer import predict_proba
    for tenant_id in [bank.id, fin.id]:
        cfs = db.query(M.CustomerFeature).filter_by(tenant_id=tenant_id).all()
        med = {}
        import pandas as pd
        df = pd.DataFrame([r.f for r in cfs])
        for col in df.columns: med[col] = float(df[col].median())
        clvs, rars = [], []
        tmp = {}
        for cf in cfs:
            p = predict_proba(cf.f)
            annual_vol = cf.f["avg_txn"]*cf.f["txn_freq"]*12
            clv, contrib = calc_clv(cf.f["avg_balance"], annual_vol, cf.f["product_count"], cf.f["complaints"], cf.f["tenure_months"])
            rar = calc_rar(p, clv)
            clvs.append(clv); rars.append(rar)
            tmp[cf.customer_id] = (p, clv, contrib, rar)
        cmax, rmax = max(clvs), max(rars)
        now = datetime.utcnow()
        for cf in cfs:
            p, clv, contrib, rar = tmp[cf.customer_id]
            drivers, sent = explain_fallback(cf.f, p, med)
            traj = {"d90": round(max(0.01, min(0.99, p*rnd.uniform(0.5, 0.8))), 3),
                    "d60": round(max(0.01, min(0.99, p*rnd.uniform(0.65, 0.9))), 3),
                    "d30": round(max(0.01, min(0.99, p*rnd.uniform(0.8, 1.0))), 3), "today": round(p, 4)}
            db.add(M.ChurnPrediction(tenant_id=tenant_id, customer_id=cf.customer_id, proba=round(p, 4),
                   band=band(p), trajectory=traj, drivers=drivers, explanation=sent))
            db.add(M.CustomerValue(tenant_id=tenant_id, customer_id=cf.customer_id, clv=clv,
                   annual_contrib=contrib, revenue_at_risk=rar))
            act, succ, reason = pick_action(cf.f, clv)
            sc, pr = priority_of(p, clv, rar, ACTIONS[act]["cost"], succ, cmax, rmax)
            db.add(M.Recommendation(tenant_id=tenant_id, customer_id=cf.customer_id, action=act,
                   cost=ACTIONS[act]["cost"], success=succ,
                   expected_roi=round((succ*clv - ACTIONS[act]["cost"])/max(1, ACTIONS[act]["cost"]), 3),
                   reason=reason, priority=pr, priority_score=sc))
        db.flush()
        # 3 completed campaigns with simulated results + 1 draft
        custs = db.query(M.Customer).filter_by(tenant_id=tenant_id).all()
        high = [c.id for c in custs[:60]]
        for ci, (nm, interv, succ) in enumerate([
            ("Festive Win-back", "cashback", 0.28), ("HNI Save Desk", "rm_call", 0.30), ("Service Recovery Blitz", "service_recovery", 0.35)]):
            camp = M.Campaign(tenant_id=tenant_id, name=nm, intervention=interv,
                    audience={"min_proba": 0.4}, offer_cost=ACTIONS[interv]["cost"],
                    expected_success=succ, duration_days=30, status="completed")
            db.add(camp); db.flush()
            exp = M.Experiment(tenant_id=tenant_id, campaign_id=camp.id, name=f"{nm} A/B"); db.add(exp); db.flush()
            tgt = rnd.sample(high, 40)
            ctrl = set(rnd.sample(tgt, 8))
            vals = {v.customer_id: v.clv for v in db.query(M.CustomerValue).filter_by(tenant_id=tenant_id).all()}
            tn = cn = tr = cr = 0
            for cid in tgt:
                is_ctrl = cid in ctrl
                base = 0.15
                retained = rnd.random() < (base if is_ctrl else succ)
                db.add(M.CampaignTarget(tenant_id=tenant_id, campaign_id=camp.id, customer_id=cid,
                       group="control" if is_ctrl else "treatment", reached=True, retained=retained))
                if is_ctrl: cn += 1; cr += retained
                else: tn += 1; tr += retained
            tr_r = tr/max(1, tn); cr_r = cr/max(1, cn); lift = tr_r - cr_r
            avgv = sum(vals.get(c, 50000) for c in tgt)/max(1, len(tgt))
            rev = max(0, lift)*tn*avgv; cost = tn*ACTIONS[interv]["cost"]
            db.add(M.ExperimentResult(tenant_id=tenant_id, experiment_id=exp.id, treat_n=tn, ctrl_n=cn,
                    treat_ret=round(tr_r, 3), ctrl_ret=round(cr_r, 3), lift=round(lift, 3),
                    revenue=round(rev, 2), cost=round(cost, 2), roi=round((rev-cost)/max(1, cost), 3)))
        db.add(M.Campaign(tenant_id=tenant_id, name="Q4 Priority Save (draft)", intervention="rm_call",
               audience={"min_proba": 0.5, "min_clv": 100000}, offer_cost=1000,
               expected_success=0.3, duration_days=30, status="draft"))
        db.commit()
    print("seed done: Demo Bank (400) + Demo Fintech (200). login demo123")

if __name__ == "__main__":
    run(reset="--reset" in sys.argv)
