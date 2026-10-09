"""Synthetic seed. Run: python -m backend.seed [--reset] (deterministic, SEED=42)"""
import os
import random
import sys
from datetime import datetime, timedelta, timezone

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, SessionLocal, Base
from backend import models as M
from backend.ml.infer import predict_proba
from backend.services import (calc_clv, calc_rar, band, priority_of, pick_action,
    explain_fallback, hash_pw, ACTIONS)

SEED = int(os.getenv("SEED", "42"))
FIRST = ["Aarav","Priya","Rohan","Sneha","Arjun","Meera","Kabir","Ananya","Vikram","Divya","Aditya","Kavya","Nikhil","Riya","Suresh","Lakshmi","Manoj","Pooja","Kiran","Anil"]
LAST = ["Sharma","Patel","Iyer","Reddy","Khan","Gupta","Nair","Singh","Das","Kulkarni","Mehta","Joshi","Chopra","Verma","Rao"]
REGIONS = ["Mumbai","Delhi","Bengaluru","Hyderabad","Chennai","Pune","Kolkata","Ahmedabad"]
PRODUCTS = [("Everyday Savings","deposit"),("Salary Current","deposit"),("Platinum Credit Card","card"),
            ("Personal Loan","loan"),("Life Insurance","insurance"),("Wealth Invest","investment")]

def run(reset=False):
    rnd = random.Random(SEED)  # nosec B311 -- deterministic synthetic demo data, not security use
    if reset:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = SessionLocal()
    if db.query(M.Tenant).count() > 0 and not reset:
        print("already seeded, use --reset")
        return
    if reset:
        for model in [M.AuditLog, M.ExperimentResult, M.Experiment, M.CampaignTarget, M.Campaign,
                  M.Recommendation, M.CustomerValue, M.ChurnPrediction, M.CustomerFeature,
                  M.Interaction, M.Transaction, M.CustomerProduct, M.Account, M.Customer, M.User, M.Tenant, M.Product]:
            db.query(model).delete()
        db.commit()
    bank = M.Tenant(name="Demo Bank")
    fin = M.Tenant(name="Demo Fintech")
    db.add_all([bank, fin]); db.flush()
    for pname, cat in PRODUCTS:
        db.add(M.Product(name=pname, category=cat))
    db.flush()
    products = db.query(M.Product).all()
    users = [("admin@demobank.in", bank.id, "admin"), ("manager@demobank.in", bank.id, "manager"),
             ("admin@demofintech.in", fin.id, "admin"), ("manager@demofintech.in", fin.id, "manager")]
    for email, tenant_id, role in users:
        salt = "".join(rnd.choices("abcdef0123456789", k=16))
        db.add(M.User(tenant_id=tenant_id, email=email, salt=salt, pw_hash=hash_pw("demo123", salt), role=role))
    db.flush()

    def make_customers(tenant_id, count):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        for _ in range(count):
            roll = rnd.random()  # loyal .45 / declining .25 / volatile .15 / new .15
            if roll < 0.45: risk = "loyal"
            elif roll < 0.70: risk = "declining"
            elif roll < 0.85: risk = "volatile"
            else: risk = "new"
            if risk == "loyal":
                tenure = rnd.randint(48, 120)
            elif risk == "new":
                tenure = rnd.randint(3, 14)
            else:
                tenure = rnd.randint(6, 60)
            age = rnd.randint(24, 65)
            income = rnd.choice([450000, 700000, 1200000, 2500000, 5000000])
            if income >= 2500000:
                seg = "HNI"
            elif income >= 1000000:
                seg = "Affluent"
            elif rnd.random() < 0.12:
                seg = "SME"
            else:
                seg = "Mass"
            cust = M.Customer(tenant_id=tenant_id, name=f"{rnd.choice(FIRST)} {rnd.choice(LAST)}",
                           age=age, income=income, tenure_months=tenure,
                           region=rnd.choice(REGIONS), segment=seg)
            db.add(cust); db.flush()
            avg_balance = rnd.uniform(80000, 900000) * (1.6 if seg in ("HNI", "Affluent") else 1.0)
            if risk == "declining": avg_balance *= rnd.uniform(0.5, 0.8)
            n_accts = rnd.randint(1, 3)
            for _ in range(n_accts):
                db.add(M.Account(tenant_id=tenant_id, customer_id=cust.id,
                       type=rnd.choice(["savings", "current", "fixed"]),
                       balance=round(avg_balance/n_accts*rnd.uniform(0.7, 1.3), 2)))
            if risk == "loyal":
                n_prods = rnd.randint(3, 5)
            elif risk == "new":
                n_prods = 1
            else:
                n_prods = rnd.randint(1, 3)
            for prod in rnd.sample(products, min(n_prods, len(products))):
                db.add(M.CustomerProduct(tenant_id=tenant_id, customer_id=cust.id, product_id=prod.id))
            has_loan = any(p.category == "loan" for p in rnd.sample(products, 1)) or (rnd.random() < 0.3)
            if risk == "loyal":
                txn_freq, avg_txn, card_usage, logins, eng_decline, inact_days, fail_rate = (
                    rnd.uniform(10, 25), rnd.uniform(3000, 9000), rnd.uniform(0.5, 0.9), rnd.uniform(12, 28),
                    rnd.uniform(0, 0.1), rnd.randint(0, 5), rnd.uniform(0, 0.02))
                bal_trend, txn_trend, complaints = (
                    rnd.uniform(-0.02, 0.08), rnd.uniform(-0.05, 0.1), 0 if rnd.random() < 0.9 else 1)
            elif risk == "declining":
                txn_freq, avg_txn, card_usage, logins, eng_decline, inact_days, fail_rate = (
                    rnd.uniform(2, 7), rnd.uniform(1500, 5000), rnd.uniform(0.05, 0.3), rnd.uniform(1, 6),
                    rnd.uniform(0.3, 0.7), rnd.randint(15, 60), rnd.uniform(0.03, 0.12))
                bal_trend, txn_trend, complaints = (
                    rnd.uniform(-0.45, -0.12), rnd.uniform(-0.5, -0.15), rnd.randint(1, 4))
            elif risk == "volatile":
                txn_freq, avg_txn, card_usage, logins, eng_decline, inact_days, fail_rate = (
                    rnd.uniform(5, 14), rnd.uniform(2000, 7000), rnd.uniform(0.2, 0.6), rnd.uniform(5, 14),
                    rnd.uniform(0.1, 0.35), rnd.randint(3, 20), rnd.uniform(0.01, 0.06))
                bal_trend, txn_trend, complaints = (
                    rnd.uniform(-0.15, 0.15), rnd.uniform(-0.2, 0.2), rnd.randint(0, 2))
            else:
                txn_freq, avg_txn, card_usage, logins, eng_decline, inact_days, fail_rate = (
                    rnd.uniform(3, 10), rnd.uniform(1500, 4500), rnd.uniform(0.2, 0.5), rnd.uniform(6, 16),
                    rnd.uniform(0, 0.2), rnd.randint(0, 10), rnd.uniform(0, 0.04))
                bal_trend, txn_trend, complaints = (
                    rnd.uniform(-0.05, 0.15), rnd.uniform(-0.05, 0.2), 0 if rnd.random() < 0.85 else 1)
            resolution_days = round(rnd.uniform(1, 12) if complaints else rnd.uniform(0.5, 2), 1)
            feats = {"tenure_months": tenure, "age": age, "income": income, "avg_balance": round(avg_balance, 2),
                "balance_trend": round(bal_trend, 3), "txn_freq": round(txn_freq, 1), "avg_txn": round(avg_txn, 2),
                "txn_trend": round(txn_trend, 3), "card_usage": round(card_usage, 3), "product_count": n_prods,
                "has_loan": 1 if has_loan else 0, "complaints": complaints, "resolution_days": resolution_days,
                "logins": round(logins, 1), "engagement_decline": round(eng_decline, 3),
                "inactivity_days": inact_days, "failed_rate": round(fail_rate, 4)}
            label = 1 if (risk == "declining" and rnd.random() < 0.75) or \
                (risk == "volatile" and rnd.random() < 0.3) or (rnd.random() < 0.05) else 0
            db.add(M.CustomerFeature(tenant_id=tenant_id, customer_id=cust.id, f=feats, label=label))
            for months_ago in range(12):
                decay = 1.0 if months_ago > 2 else (1 + txn_trend)  # recent months reflect trend
                amount = round(avg_txn*txn_freq*decay*rnd.uniform(0.8, 1.2), 2)
                db.add(M.Transaction(tenant_id=tenant_id, customer_id=cust.id, amount=amount,
                       ts=now - timedelta(days=30*months_ago + rnd.randint(0, 20)), type="debit"))
            for _ in range(complaints):
                db.add(M.Interaction(tenant_id=tenant_id, customer_id=cust.id, kind="complaint",
                       severity=rnd.randint(2, 5), resolved=rnd.random() < 0.7,
                       resolution_days=resolution_days, ts=now - timedelta(days=rnd.randint(5, 200)),
                       note="Service complaint (synthetic)"))
            for _ in range(rnd.randint(0, 3)):
                db.add(M.Interaction(tenant_id=tenant_id, customer_id=cust.id, kind=rnd.choice(["call", "visit", "login"]),
                       severity=1, resolved=True, resolution_days=0.5,
                       ts=now - timedelta(days=rnd.randint(1, 90)), note="Engagement (synthetic)"))
        db.flush()

    make_customers(bank.id, 400)
    make_customers(fin.id, 200)

    # Scores + values + recommendations (rule model; retrain upgrades artifacts later).
    for tenant_id in [bank.id, fin.id]:
        rows = db.query(M.CustomerFeature).filter_by(tenant_id=tenant_id).all()
        df = pd.DataFrame([r.f for r in rows])
        medians = {col: float(df[col].median()) for col in df.columns}
        clvs, rars = [], []
        by_customer = {}
        for row in rows:
            proba = predict_proba(row.f)
            annual_vol = row.f["avg_txn"]*row.f["txn_freq"]*12
            clv, contrib = calc_clv(row.f["avg_balance"], annual_vol, row.f["product_count"], row.f["complaints"], row.f["tenure_months"])
            rar = calc_rar(proba, clv)
            clvs.append(clv); rars.append(rar)
            by_customer[row.customer_id] = (proba, clv, contrib, rar)
        clv_max, rar_max = max(clvs), max(rars)
        for row in rows:
            proba, clv, contrib, rar = by_customer[row.customer_id]
            drivers, explanation = explain_fallback(row.f, proba, medians)
            trajectory = {"d90": round(max(0.01, min(0.99, proba*rnd.uniform(0.5, 0.8))), 3),
                    "d60": round(max(0.01, min(0.99, proba*rnd.uniform(0.65, 0.9))), 3),
                    "d30": round(max(0.01, min(0.99, proba*rnd.uniform(0.8, 1.0))), 3), "today": round(proba, 4)}
            db.add(M.ChurnPrediction(tenant_id=tenant_id, customer_id=row.customer_id, proba=round(proba, 4),
                   band=band(proba), trajectory=trajectory, drivers=drivers, explanation=explanation))
            db.add(M.CustomerValue(tenant_id=tenant_id, customer_id=row.customer_id, clv=clv,
                   annual_contrib=contrib, revenue_at_risk=rar))
            action, success, reason = pick_action(row.f, clv)
            score, priority = priority_of(proba, clv, rar, ACTIONS[action]["cost"], success, clv_max, rar_max)
            db.add(M.Recommendation(tenant_id=tenant_id, customer_id=row.customer_id, action=action,
                   cost=ACTIONS[action]["cost"], success=success,
                   expected_roi=round((success*clv - ACTIONS[action]["cost"])/max(1, ACTIONS[action]["cost"]), 3),
                   reason=reason, priority=priority, priority_score=score))
        db.flush()
        customers = db.query(M.Customer).filter_by(tenant_id=tenant_id).all()
        pool = [c.id for c in customers[:60]]
        for name, intervention, success in [
            ("Festive Win-back", "cashback", 0.28), ("HNI Save Desk", "rm_call", 0.30), ("Service Recovery Blitz", "service_recovery", 0.35)]:
            campaign = M.Campaign(tenant_id=tenant_id, name=name, intervention=intervention,
                    audience={"min_proba": 0.4}, offer_cost=ACTIONS[intervention]["cost"],
                    expected_success=success, duration_days=30, status="completed")
            db.add(campaign); db.flush()
            experiment = M.Experiment(tenant_id=tenant_id, campaign_id=campaign.id, name=f"{name} A/B"); db.add(experiment); db.flush()
            target_ids = rnd.sample(pool, 40)
            control_ids = set(rnd.sample(target_ids, 8))
            clv_by_id = {v.customer_id: v.clv for v in db.query(M.CustomerValue).filter_by(tenant_id=tenant_id).all()}
            treat_n = ctrl_n = treat_kept = ctrl_kept = 0
            for cid in target_ids:
                is_ctrl = cid in control_ids
                kept = rnd.random() < (0.15 if is_ctrl else success)
                db.add(M.CampaignTarget(tenant_id=tenant_id, campaign_id=campaign.id, customer_id=cid,
                       group="control" if is_ctrl else "treatment", reached=True, retained=kept))
                if is_ctrl: ctrl_n += 1; ctrl_kept += kept
                else: treat_n += 1; treat_kept += kept
            treat_rate = treat_kept/max(1, treat_n); ctrl_rate = ctrl_kept/max(1, ctrl_n); lift = treat_rate - ctrl_rate
            avg_clv = sum(clv_by_id.get(c, 50000) for c in target_ids)/max(1, len(target_ids))
            revenue = max(0, lift)*treat_n*avg_clv; cost = treat_n*ACTIONS[intervention]["cost"]
            db.add(M.ExperimentResult(tenant_id=tenant_id, experiment_id=experiment.id, treat_n=treat_n, ctrl_n=ctrl_n,
                    treat_ret=round(treat_rate, 3), ctrl_ret=round(ctrl_rate, 3), lift=round(lift, 3),
                    revenue=round(revenue, 2), cost=round(cost, 2), roi=round((revenue-cost)/max(1, cost), 3)))
        db.add(M.Campaign(tenant_id=tenant_id, name="Q4 Priority Save (draft)", intervention="rm_call",
               audience={"min_proba": 0.5, "min_clv": 100000}, offer_cost=1000,
               expected_success=0.3, duration_days=30, status="draft"))
        db.commit()
    print("seed done: Demo Bank (400) + Demo Fintech (200). login demo123")

if __name__ == "__main__":
    run(reset="--reset" in sys.argv)
