"""Analyst answers ANY question type from real aggregates — never a dead end."""
from backend.services import analyst_fallback, _parse_money, _parse_topn

CTX = {
    "total": 400, "high": 104, "medium": 80, "low": 216,
    "rar": 8429262.0, "total_clv": 50000000.0, "avg_proba": 0.42,
    "by_segment": [{"segment": "HNI", "rar": 4000000.0, "n": 40},
                   {"segment": "Mass", "rar": 2000000.0, "n": 300}],
    "top": [{"name": "Aarav Sharma", "proba": 0.87, "clv": 250000.0,
             "rar": 217500.0, "action": "rm_call", "priority": "Critical"},
            {"name": "Priya Nair", "proba": 0.72, "clv": 180000.0,
             "rar": 129600.0, "action": "service_recovery", "priority": "Critical"}],
    "interventions": [{"action": "rm_call", "count": 50, "avg_success": 0.3, "cost": 1000},
                      {"action": "cashback", "count": 30, "avg_success": 0.28, "cost": 1200}],
    "campaigns": [{"name": "Festive Win-back", "status": "completed", "intervention": "cashback",
                   "roi_pct": 120.5, "revenue": 500000.0, "lift": 0.15, "cost": 200000.0}],
    "products": [{"product": "Personal Loan", "customers": 100, "high_risk": 30, "rar": 3000000.0}],
    "model": {"auc": 0.907, "precision": 0.8, "recall": 0.75, "f1": 0.774, "n": 600},
}

def test_greeting_and_help():
    a = analyst_fallback("hello", CTX)
    assert "segment" in a and "budget" in a or "try" in a.lower()

def test_custom_budget_amount():
    a = analyst_fallback("How should we spend ₹5 lakh?", CTX)
    assert "500,000" in a and "Aarav Sharma" in a  # real number + real name, not canned 10L

def test_top_n_parsing():
    assert _parse_topn("show top 3 customers") == 3
    a = analyst_fallback("list top 2 customers", CTX)
    assert "Priya Nair" in a

def test_segments_interventions_campaigns_products():
    assert "HNI" in analyst_fallback("Which segment is riskiest?", CTX)
    assert "rm call" in analyst_fallback("Compare interventions", CTX)
    c = analyst_fallback("How did campaigns perform?", CTX)
    assert "Festive Win-back" in c and "120.5%" in c
    assert "Personal Loan" in analyst_fallback("Which product is riskiest?", CTX)

def test_trend_value_model_counts_definitions():
    assert "104" in analyst_fallback("Why is risk rising?", CTX)
    assert "50,000,000" in analyst_fallback("What is our total CLV?", CTX)
    assert "0.907" in analyst_fallback("How accurate is the model?", CTX)
    assert "104" in analyst_fallback("How many high risk customers?", CTX)
    assert "probability × CLV" in analyst_fallback("What is revenue at risk?", CTX)

def test_customer_detail():
    ctx = dict(CTX, customer={"name": "Aarav Sharma", "segment": "HNI", "region": "Mumbai",
        "tenure": 60, "proba": 0.87, "band": "High",
        "trajectory": {"d30": 0.6, "today": 0.87}, "drivers": [{"label": "complaints"}],
        "explanation": "Risk high because complaints rose.", "clv": 250000.0, "rar": 217500.0,
        "balance": 300000.0, "products": 3, "action": "rm_call", "cost": 1000,
        "success": 0.3, "priority": "Critical"})
    a = analyst_fallback('Why is customer "Aarav Sharma" at risk?', ctx)
    assert "Aarav Sharma" in a and "87%" in a and "rm call" in a

def test_unknown_question_still_useful():
    a = analyst_fallback("What should we do about branch timings next quarter?", CTX)
    assert "Aarav Sharma" in a and "8,429,262" in a  # real numbers, suggestions, no dead end
    assert len(a) > 100

def test_money_parsing():
    assert _parse_money("spend ₹10 lakh") == 1000000
    assert _parse_money("budget of 500000") is None or _parse_money("budget of 500000") == 500000
    assert _parse_money("top 20 customers") is None  # no money cue → not a budget
    assert _parse_money("2 crore for retention") == 20000000
