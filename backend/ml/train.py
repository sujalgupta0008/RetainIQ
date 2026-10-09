"""Train churn model from DB. Run: python -m backend.ml.train"""
import os, json, pickle  # nosec: B403 - pickle writes trusted local artifacts; loads are sha256-verified in ml/infer.py
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score, confusion_matrix

FEATS = ["tenure_months","age","income","avg_balance","balance_trend","txn_freq","avg_txn",
 "txn_trend","card_usage","product_count","has_loan","complaints","resolution_days",
 "logins","engagement_decline","inactivity_days","failed_rate"]

def get_model():
    try:
        from xgboost import XGBClassifier
        return XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.06,
            subsample=0.9, colsample_bytree=0.9, random_state=42, n_jobs=2)
    except Exception:
        from sklearn.ensemble import HistGradientBoostingClassifier
        print("xgboost not available, using HistGradientBoostingClassifier fallback")
        return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.06, random_state=42)

def main():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from backend.database import SessionLocal
    from backend.models import CustomerFeature
    db = SessionLocal()
    rows = db.query(CustomerFeature).all()
    if len(rows) < 50:
        print("Not enough data to train (need 50+), skipping.")
        return
    X = pd.DataFrame([{**r.f} for r in rows])[FEATS].fillna(0)
    y = np.array([r.label for r in rows])
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    sc = StandardScaler().fit(Xtr)
    base = LogisticRegression(max_iter=1000).fit(sc.transform(Xtr), ytr)
    model = get_model().fit(sc.transform(Xtr), ytr)
    for name, m in [("baseline", base), ("primary", model)]:
        p = m.predict_proba(sc.transform(Xte))[:, 1]
        print(f"{name}: AUC={roc_auc_score(yte,p):.3f} P={precision_score(yte,p>0.5,zero_division=0):.3f} "
              f"R={recall_score(yte,p>0.5,zero_division=0):.3f} F1={f1_score(yte,p>0.5,zero_division=0):.3f}")
    p = model.predict_proba(sc.transform(Xte))[:, 1]
    metrics = {"auc": roc_auc_score(yte, p), "precision": precision_score(yte, p > 0.5, zero_division=0),
        "recall": recall_score(yte, p > 0.5, zero_division=0), "f1": f1_score(yte, p > 0.5, zero_division=0),
        "confusion": confusion_matrix(yte, p > 0.5).tolist(), "n": len(rows)}
    art = os.path.join(os.path.dirname(__file__), "artifacts")
    os.makedirs(art, exist_ok=True)
    with open(os.path.join(art, "model.pkl"), "wb") as f: pickle.dump(model, f)
    with open(os.path.join(art, "baseline.pkl"), "wb") as f: pickle.dump(base, f)
    with open(os.path.join(art, "scaler.pkl"), "wb") as f: pickle.dump(sc, f)
    with open(os.path.join(art, "features.json"), "w") as f: json.dump(FEATS, f)
    with open(os.path.join(art, "metrics.json"), "w") as f: json.dump(metrics, f, indent=2)
    # Integrity sidecars verified by ml/infer.py (S09). Hash the exact bytes written.
    import hashlib
    for name in ("model.pkl", "baseline.pkl", "scaler.pkl"):
        p = os.path.join(art, name)
        h = hashlib.sha256()
        with open(p, "rb") as f:
            h.update(f.read())
        with open(p + ".sha256", "w") as f:
            f.write(f"{h.hexdigest()}  {name}\n")
    print("saved artifacts ->", art)

if __name__ == "__main__":
    main()
