from backend.services import calc_roi, calc_clv, calc_rar, band, pick_action, priority_of, explain_fallback

def test_roi_math():
    r = calc_roi(100, 0.25, 100000, 800)
    assert r["targeted"] == 100 and r["retained"] == 25.0
    assert r["cost"] == 80000 and r["revenue"] == 2500000
    assert r["net"] == 2420000 and r["roi_pct"] > 0

def test_roi_zero_cost():
    r = calc_roi(10, 0.1, 50000, 0)
    assert r["roi"] == 0.0 and r["revenue"] == 50000

def test_clv_rar():
    clv, c = calc_clv(100000, 500000, 2, 0, 36)
    assert clv > 0 and c >= 500
    assert calc_rar(0.5, 100000) == 50000

def test_band_priority():
    assert band(0.7) == "High" and band(0.5) == "Medium" and band(0.1) == "Low"
    s, seg = priority_of(0.8, 200000, 160000, 1000, 0.3, 200000, 160000)
    assert seg == "Critical" and 0 <= s <= 100

def test_nba_complaint():
    feats = {"complaints": 3, "balance_trend": 0, "engagement_decline": 0, "product_count": 2}
    act, s, reason = pick_action(feats, 200000)
    assert act == "service_recovery" and "complaint" in reason.lower()

def test_explain_uses_real_deltas():
    feats = {"txn_freq": 2, "avg_balance": 20000, "complaints": 3, "logins": 2,
             "balance_trend": -0.3, "txn_trend": -0.4, "engagement_decline": 0.5,
             "product_count": 1, "card_usage": 0.1, "inactivity_days": 40, "failed_rate": 0.08,
             "tenure_months": 12, "age": 40, "income": 600000, "avg_txn": 2000,
             "has_loan": 0, "resolution_days": 8}
    med = {k: (8 if k == "txn_freq" else (100000 if k == "avg_balance" else (0 if k in ("complaints",) else v))) for k, v in feats.items()}
    med.update({"txn_freq": 10, "avg_balance": 100000, "logins": 12, "card_usage": 0.5, "product_count": 3})
    dr, sent = explain_fallback(feats, 0.8, med)
    assert len(dr) >= 3 and ("complaints" in sent.lower() or "transaction" in sent.lower())
