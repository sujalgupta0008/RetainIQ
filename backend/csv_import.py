"""CSV import adapter: banking / telco / generic -> normalized RetainIQ customer rows.

Flow: uploaded CSV -> detect schema -> normalize -> validate -> insert ->
derive 16 ML features -> predictions -> dashboard.

Telco fields are DOMAIN-ADAPTED PROXIES (documented below), not real banking
measurements. Deterministic: same file always yields same rows (no random calls).
"""
import pandas as pd
import numpy as np

BANKING_COLS = {"name", "age", "income", "tenure_months", "region",
                "avg_balance", "txn_freq", "avg_txn"}

# Telco -> RetainIQ feature map (proxies, see docstrings in _telco_record).
# Preserved telco signal: tenure, monthly/total charges, service count,
# contract, support flags, payment method, churn score -> 16 ML features.
TELCO_PREVIEW = [
    ("CustomerID", "Customer Name"),
    ("Tenure Months", "Tenure (months)"),
    ("Monthly Charges", "Value Proxy (spend rate)"),
    ("Total Charges / CLTV", "Customer Value Proxy (not a bank balance)"),
    ("Churn Value", "Churn Label (preserved as ML target)"),
    ("City / State", "Region"),
    ("Contract", "Segment signal"),
    ("Services count", "Product holdings proxy"),
]


def _key(c: str) -> str:
    return str(c).strip().lower()


def _num(v, default: float = 0.0) -> float:
    """Parse '$1,200.50' / '  ' / None safely; never returns NaN/inf."""
    try:
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return float(default)
        s = str(v).replace("$", "").replace(",", "").strip()
        if s == "" or s.lower() in ("nan", "none", "null", "n/a"):
            return float(default)
        out = float(s)
        if np.isnan(out) or np.isinf(out):
            return float(default)
        return out
    except (ValueError, TypeError):
        return float(default)


def _det(key: str, lo: int, hi: int) -> int:
    """Deterministic pseudo-value in [lo, hi] from a string key (stable across uploads)."""
    return lo + (sum(ord(c) for c in str(key)) % max(1, hi - lo + 1))


def _yes(v) -> bool:
    return str(v).strip().lower() in ("yes", "1", "true", "y")


def detect_dataset_type(df: pd.DataFrame) -> str:
    keys = {_key(c) for c in df.columns}
    if {"customerid", "monthly charges"} <= keys and (
            "churn value" in keys or "churn label" in keys):
        return "telco"
    if BANKING_COLS <= keys:
        return "banking"
    if keys & {"customerid", "customer id", "name", "customer"}:
        return "generic"
    return "unknown"


def _banking_record(row: dict) -> dict:
    return {
        "name": str(row.get("name", "")).strip(),
        "age": int(_num(row.get("age"), 35)),
        "income": _num(row.get("income"), 600000),
        "tenure_months": int(_num(row.get("tenure_months"), 12)),
        "region": str(row.get("region", "")).strip() or "Mumbai",
        "segment": "Mass",
        "avg_balance": _num(row.get("avg_balance"), 50000),
        "txn_freq": _num(row.get("txn_freq"), 8),
        "avg_txn": _num(row.get("avg_txn"), 4000),
        "label": 0,
        "n_products": 1, "has_loan": 0, "complaints": 0,
    }


def _telco_record(orig: dict) -> dict:
    """Deterministic telco -> banking-compatible row. Money fields are proxies."""
    g = lambda *names: next((orig.get(n) for n in names if orig.get(n) is not None), "")
    cid = str(g("CustomerID", "customerID", "customer_id")).strip()
    tenure = int(max(0, min(120, _num(g("Tenure Months", "tenure months", "tenure"), 12))))
    monthly = _num(g("Monthly Charges", "monthly charges", "monthlycharges"), 65.0)
    total = _num(g("Total Charges", "total charges", "totalcharges"), monthly * max(1, tenure))
    cltv = _num(g("CLTV", "cltv"), 0.0)
    score = _num(g("Churn Score", "churn score", "churnscore"), 50.0)
    senior = str(g("Senior Citizen", "senior citizen", "seniorcitizen")).strip() == "1"
    contract = str(g("Contract", "contract")).strip() or "Month-to-month"
    pay = str(g("Payment Method", "payment method", "paymentmethod")).strip()
    internet = str(g("Internet Service", "internet service", "internetservice")).strip()
    phone = _yes(g("Phone Service", "phone service", "phoneservice"))
    online_yes = sum(_yes(g(c)) for c in
                     ["Online Security", "Online Backup", "Device Protection",
                      "Tech Support", "Streaming TV", "Streaming Movies"])
    services = (1 if phone else 0) + (1 if internet.lower() != "no" else 0) + online_yes
    city = str(g("City", "city", "State", "state")).strip() or "United States"

    cv = str(g("Churn Value", "churn value", "churnvalue")).strip().lower()
    if cv in ("1", "yes", "true"):
        label = 1
    elif cv in ("0", "no", "false"):
        label = 0
    else:
        label = 1 if str(g("Churn Label", "churn label")).strip().lower() == "yes" else 0

    # --- deterministic proxies (documented, demo-only) ---
    age = 68 if senior else 28 + _det(cid, 0, 29)
    mult = 10 if contract == "Two year" else (8 if contract == "One year" else 6)
    income = round(monthly * 12 * mult + 0.5 * cltv, 2)  # estimated demo feature
    avg_balance = round(cltv if cltv > 0 else total, 2)  # value proxy, NOT a bank balance
    txn_freq = round(2 + 3 * phone + 3 * (internet.lower() != "no")
                     + 2 * (contract != "Month-to-month") + min(4, monthly / 50), 1)
    nosupport = sum(not _yes(g(c)) for c in
                    ["Online Security", "Online Backup", "Tech Support"])
    complaints = min(3, nosupport) if score >= 50 else 0
    high_risk = score >= 75
    return {
        "name": cid,
        "age": age,
        "income": income,
        "tenure_months": tenure,
        "region": city,
        "segment": ("HNI" if cltv >= 5000 else "Affluent") if contract == "Two year"
                   else ("Mass" if contract == "Month-to-month" else "Affluent"),
        "avg_balance": avg_balance,
        "txn_freq": txn_freq,
        "avg_txn": round(monthly, 2),
        "label": label,
        "n_products": max(1, services),
        "has_loan": 0,
        "complaints": complaints,
        # extra derived 16-feature inputs carried through for transparency
        "_telco": {"contract": contract, "pay": pay, "score": score,
                   "logins": min(25, 3 + 2 * online_yes),
                   "inactivity": 30 if (contract == "Month-to-month" and score >= 70) else 5,
                   "failed": 0.08 if pay == "Electronic check" else 0.02,
                   "bal_trend": -0.3 if high_risk else (-0.1 if score >= 50 else 0.05),
                   "txn_trend": -0.35 if high_risk else (-0.1 if score >= 50 else 0.05),
                   "card": 0.5 if "automatic" in pay.lower() else 0.2,
                   "eng": round(score / 100 * 0.7, 3)},
    }


def _generic_record(row: dict, keys: dict) -> dict:
    pick = lambda *ns: next((row[k] for k in ns if k in row), "")
    name = str(pick("customerid", "customer id", "name", "customer", "id")).strip()
    tenure = int(_num(pick("tenure months", "tenure_months", "tenure"), 12))
    monthly = _num(pick("monthly charges", "avg_txn", "charges"), 4000)
    return {"name": name, "age": 35, "income": 600000, "tenure_months": tenure,
            "region": "Mumbai", "segment": "Mass",
            "avg_balance": _num(pick("avg_balance", "total charges"), 50000),
            "txn_freq": 8.0, "avg_txn": monthly, "label": 0,
            "n_products": 1, "has_loan": 0, "complaints": 0}


def normalize_customer_csv(df: pd.DataFrame):
    """Returns (dataset_type, records, mapping_preview, issues).

    records: normalized dicts ready for the ingestion pipeline.
    issues: human-readable row problems (identifier missing, dupes dropped).
    """
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    dtype = detect_dataset_type(df)
    keys = {_key(c): c for c in df.columns}
    records, issues, seen = [], [], set()
    for i, (_, s) in enumerate(df.iterrows(), start=2):
        row = { _key(k): v for k, v in s.to_dict().items() }
        try:
            sdict = s.to_dict()  # original-case keys for telco lookup
            if dtype == "banking":
                rec = _banking_record(row)
            elif dtype == "telco":
                rec = _telco_record(sdict)
            else:
                rec = _generic_record(row, keys)
        except Exception as e:
            issues.append(f"row {i}: cannot parse ({e})")
            continue
        if not rec["name"] or rec["name"].strip().lower() in ("nan", "none", "null"):
            issues.append(f"row {i}: missing customer identifier, skipped")
            continue
        if rec["name"] in seen:
            issues.append(f"row {i}: duplicate '{rec['name']}' in file, skipped")
            continue
        seen.add(rec["name"])
        records.append(rec)
    if dtype == "telco":
        mapping = TELCO_PREVIEW
    elif dtype == "banking":
        mapping = [(c, c) for c in sorted(BANKING_COLS)]
    else:
        mapping = [("identifier column", "Customer Name"),
                   ("tenure-like column", "Tenure (months, if present)"),
                   ("charges-like column", "Value Proxy (if present)")]
    return dtype, records, mapping, issues
