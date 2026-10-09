"""CSV adapter: banking / telco / generic -> normalized customer rows.

Telco money fields are domain-adapted proxies, not bank balances.
Deterministic: same file always yields same rows.
"""
import pandas as pd
import numpy as np

BANKING_COLS = {"name", "age", "income", "tenure_months", "region",
                "avg_balance", "txn_freq", "avg_txn"}

# Telco -> RetainIQ proxies. Preserved signal: tenure, charges, service count,
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


def _key(col: str) -> str:
    return str(col).strip().lower()


def _num(value, default: float = 0.0) -> float:
    """Parse '$1,200.50' / '  ' / None safely; never returns NaN/inf."""
    try:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return float(default)
        s = str(value).replace("$", "").replace(",", "").strip()
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
    return lo + (sum(ord(ch) for ch in str(key)) % max(1, hi - lo + 1))


def _yes(value) -> bool:
    return str(value).strip().lower() in ("yes", "1", "true", "y")


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
    def get(*names):
        return next((orig.get(n) for n in names if orig.get(n) is not None), "")
    cid = str(get("CustomerID", "customerID", "customer_id")).strip()
    tenure = int(max(0, min(120, _num(get("Tenure Months", "tenure months", "tenure"), 12))))
    monthly = _num(get("Monthly Charges", "monthly charges", "monthlycharges"), 65.0)
    total = _num(get("Total Charges", "total charges", "totalcharges"), monthly * max(1, tenure))
    cltv = _num(get("CLTV", "cltv"), 0.0)
    score = _num(get("Churn Score", "churn score", "churnscore"), 50.0)
    senior = str(get("Senior Citizen", "senior citizen", "seniorcitizen")).strip() == "1"
    contract = str(get("Contract", "contract")).strip() or "Month-to-month"
    pay_method = str(get("Payment Method", "payment method", "paymentmethod")).strip()
    internet = str(get("Internet Service", "internet service", "internetservice")).strip()
    phone = _yes(get("Phone Service", "phone service", "phoneservice"))
    online_yes = sum(_yes(get(c)) for c in
                     ["Online Security", "Online Backup", "Device Protection",
                      "Tech Support", "Streaming TV", "Streaming Movies"])
    services = (1 if phone else 0) + (1 if internet.lower() != "no" else 0) + online_yes
    city = str(get("City", "city", "State", "state")).strip() or "United States"

    churn_flag = str(get("Churn Value", "churn value", "churnvalue")).strip().lower()
    if churn_flag in ("1", "yes", "true"):
        label = 1
    elif churn_flag in ("0", "no", "false"):
        label = 0
    else:
        label = 1 if str(get("Churn Label", "churn label")).strip().lower() == "yes" else 0

    age = 68 if senior else 28 + _det(cid, 0, 29)
    income_mult = 10 if contract == "Two year" else (8 if contract == "One year" else 6)
    income = round(monthly * 12 * income_mult + 0.5 * cltv, 2)  # estimated demo feature
    avg_balance = round(cltv if cltv > 0 else total, 2)  # value proxy, NOT a bank balance
    txn_freq = round(2 + 3 * phone + 3 * (internet.lower() != "no")
                     + 2 * (contract != "Month-to-month") + min(4, monthly / 50), 1)
    missing_support = sum(not _yes(get(c)) for c in
                    ["Online Security", "Online Backup", "Tech Support"])
    complaints = min(3, missing_support) if score >= 50 else 0
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
        "_telco": {"contract": contract, "pay": pay_method, "score": score,
                   "logins": min(25, 3 + 2 * online_yes),
                   "inactivity": 30 if (contract == "Month-to-month" and score >= 70) else 5,
                   "failed": 0.08 if pay_method == "Electronic check" else 0.02,
                   "bal_trend": -0.3 if high_risk else (-0.1 if score >= 50 else 0.05),
                   "txn_trend": -0.35 if high_risk else (-0.1 if score >= 50 else 0.05),
                   "card": 0.5 if "automatic" in pay_method.lower() else 0.2,
                   "eng": round(score / 100 * 0.7, 3)},
    }


def _generic_record(row: dict) -> dict:
    def get(*names):
        return next((row[k] for k in names if k in row), "")
    name = str(get("customerid", "customer id", "name", "customer", "id")).strip()
    tenure = int(_num(get("tenure months", "tenure_months", "tenure"), 12))
    monthly = _num(get("monthly charges", "avg_txn", "charges"), 4000)
    return {"name": name, "age": 35, "income": 600000, "tenure_months": tenure,
            "region": "Mumbai", "segment": "Mass",
            "avg_balance": _num(get("avg_balance", "total charges"), 50000),
            "txn_freq": 8.0, "avg_txn": monthly, "label": 0,
            "n_products": 1, "has_loan": 0, "complaints": 0}


def normalize_customer_csv(df: pd.DataFrame):
    """Normalize an uploaded CSV. Returns (dataset_type, records, mapping, issues)."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    dtype = detect_dataset_type(df)
    records, issues, seen = [], [], set()
    for line_no, (_, series) in enumerate(df.iterrows(), start=2):
        row = {_key(k): v for k, v in series.to_dict().items()}
        try:
            raw = series.to_dict()  # original-case keys for telco lookup
            if dtype == "banking":
                record = _banking_record(row)
            elif dtype == "telco":
                record = _telco_record(raw)
            else:
                record = _generic_record(row)
        except Exception as e:
            issues.append(f"row {line_no}: cannot parse ({e})")
            continue
        if not record["name"] or record["name"].strip().lower() in ("nan", "none", "null"):
            issues.append(f"row {line_no}: missing customer identifier, skipped")
            continue
        if record["name"] in seen:
            issues.append(f"row {line_no}: duplicate '{record['name']}' in file, skipped")
            continue
        seen.add(record["name"])
        records.append(record)
    if dtype == "telco":
        mapping = TELCO_PREVIEW
    elif dtype == "banking":
        mapping = [(c, c) for c in sorted(BANKING_COLS)]
    else:
        mapping = [("identifier column", "Customer Name"),
                   ("tenure-like column", "Tenure (months, if present)"),
                   ("charges-like column", "Value Proxy (if present)")]
    return dtype, records, mapping, issues
