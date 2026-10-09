"""Adapter tests: banking + telco normalization, labels, dupes, numerics."""
import io
import pandas as pd
from backend.csv_import import normalize_customer_csv, detect_dataset_type, _num

BANKING = """name,age,income,tenure_months,region,avg_balance,txn_freq,avg_txn
Test User,38,900000,30,Mumbai,120000,10,4500
Sample Saver,45,1500000,60,Pune,300000,14,6000
"""

TELCO = """CustomerID,Gender,Senior Citizen,Partner,Dependents,Tenure Months,Phone Service,Multiple Lines,Internet Service,Online Security,Online Backup,Device Protection,Tech Support,Streaming TV,Streaming Movies,Contract,Paperless Billing,Payment Method,Monthly Charges,Total Charges,Churn Label,Churn Value,Churn Score,CLTV,Churn Reason,City
7590-VHVEG,Female,0,Yes,No,1,No,No phone service,DSL,No,Yes,No,No,No,No,Month-to-month,Yes,Electronic check,$29.85,$29.85,Yes,1,86,3237,Better offer,San Diego
5575-GNVDE,Male,0,No,No,34,Yes,No,DSL,Yes,No,Yes,No,No,No,One year,No,Mailed check,$56.95,$1889.5,No,0,35,5098,,Los Angeles
7795-CFOCW,Male,0,No,No,45,No,No phone service,DSL,Yes,No,Yes,Yes,No,No,One year,No,Bank transfer (automatic),$42.30,,No,0,45,5003,,Sacramento
9237-HQITU,Female,0,No,No,2,Yes,No,Fiber optic,No,No,No,No,No,No,Month-to-month,Yes,Electronic check,$70.70,$151.65,Yes,1,90,3588,Price too high,
7590-VHVEG,Female,0,Yes,No,1,No,No phone service,DSL,No,Yes,No,No,No,No,Month-to-month,Yes,Electronic check,$29.85,$29.85,Yes,1,86,3237,Duplicate,San Diego
,Male,0,No,No,5,Yes,No,DSL,No,No,No,No,No,No,Month-to-month,Yes,Electronic check,$50.00,$250.00,No,0,40,3000,No id,
"""

def _df(s): return pd.read_csv(io.StringIO(s))

def test_banking_sample_unchanged():
    df = _df(BANKING)
    assert detect_dataset_type(df) == "banking"
    dtype, recs, mapping, issues = normalize_customer_csv(df)
    assert dtype == "banking" and len(recs) == 2 and issues == []
    assert recs[0]["name"] == "Test User" and recs[0]["tenure_months"] == 30
    assert recs[0]["avg_balance"] == 120000 and recs[0]["label"] == 0

def test_telco_detected_and_mapped():
    df = _df(TELCO)
    assert detect_dataset_type(df) == "telco"
    dtype, recs, mapping, issues = normalize_customer_csv(df)
    assert dtype == "telco"
    assert len(df) == 6 and len(recs) == 4  # 1 in-file dupe + 1 missing id rejected
    by_name = {r["name"]: r for r in recs}
    assert by_name["7590-VHVEG"]["tenure_months"] == 1
    assert by_name["7590-VHVEG"]["avg_txn"] == 29.85
    assert by_name["5575-GNVDE"]["region"] == "Los Angeles"
    assert any("Churn Value" in m[0] for m in mapping)

def test_churn_value_preserved_as_target():
    _, recs, _, _ = normalize_customer_csv(_df(TELCO))
    by_name = {r["name"]: r for r in recs}
    assert by_name["7590-VHVEG"]["label"] == 1
    assert by_name["9237-HQITU"]["label"] == 1
    assert by_name["5575-GNVDE"]["label"] == 0
    assert by_name["7795-CFOCW"]["label"] == 0

def test_deterministic_proxies():
    _, r1, _, _ = normalize_customer_csv(_df(TELCO))
    _, r2, _, _ = normalize_customer_csv(_df(TELCO))
    assert r1 == r2  # no randomness between uploads

def test_numeric_conversion():
    assert _num("$1,200.50") == 1200.50
    assert _num("  ") == 0.0 and _num(None, 5) == 5.0 and _num("abc", 7) == 7.0
    _, recs, _, _ = normalize_customer_csv(_df(TELCO))
    blank_total = {r["name"]: r for r in recs}["7795-CFOCW"]
    assert blank_total["avg_balance"] == 5003  # falls back to CLTV proxy, finite

def test_unknown_schema_rejected():
    df = pd.DataFrame([{"foo": 1, "bar": 2}])
    assert detect_dataset_type(df) == "unknown"
