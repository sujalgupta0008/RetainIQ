"""Train churn model from DB. Run: python -m backend.ml.train"""
import hashlib
import json
import os
import pickle  # nosec: B403 - pickle writes trusted local artifacts; loads are sha256-verified in ml/infer.py

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

FEATS = ["tenure_months","age","income","avg_balance","balance_trend","txn_freq","avg_txn",
 "txn_trend","card_usage","product_count","has_loan","complaints","resolution_days",
 "logins","engagement_decline","inactivity_days","failed_rate"]

def get_model():
    try:
        from xgboost import XGBClassifier
        return XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.06,
            subsample=0.9, colsample_bytree=0.9, random_state=42, n_jobs=2)
    except Exception:
        # XGBoost is optional; the sklearn fallback trains on the same features.
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
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    scaler = StandardScaler().fit(X_train)
    baseline = LogisticRegression(max_iter=1000).fit(scaler.transform(X_train), y_train)
    model = get_model().fit(scaler.transform(X_train), y_train)
    for name, clf in [("baseline", baseline), ("primary", model)]:
        proba = clf.predict_proba(scaler.transform(X_test))[:, 1]
        print(f"{name}: AUC={roc_auc_score(y_test,proba):.3f} P={precision_score(y_test,proba>0.5,zero_division=0):.3f} "
              f"R={recall_score(y_test,proba>0.5,zero_division=0):.3f} F1={f1_score(y_test,proba>0.5,zero_division=0):.3f}")
    proba = model.predict_proba(scaler.transform(X_test))[:, 1]
    metrics = {"auc": roc_auc_score(y_test, proba), "precision": precision_score(y_test, proba > 0.5, zero_division=0),
        "recall": recall_score(y_test, proba > 0.5, zero_division=0), "f1": f1_score(y_test, proba > 0.5, zero_division=0),
        "confusion": confusion_matrix(y_test, proba > 0.5).tolist(), "n": len(rows)}
    art_dir = os.path.join(os.path.dirname(__file__), "artifacts")
    os.makedirs(art_dir, exist_ok=True)
    with open(os.path.join(art_dir, "model.pkl"), "wb") as fh:
        pickle.dump(model, fh)
    with open(os.path.join(art_dir, "baseline.pkl"), "wb") as fh:
        pickle.dump(baseline, fh)
    with open(os.path.join(art_dir, "scaler.pkl"), "wb") as fh:
        pickle.dump(scaler, fh)
    with open(os.path.join(art_dir, "features.json"), "w") as fh:
        json.dump(FEATS, fh)
    with open(os.path.join(art_dir, "metrics.json"), "w") as fh:
        json.dump(metrics, fh, indent=2)
    # Integrity sidecars verified by ml/infer.py (S09). Hash the exact bytes written.
    for fname in ("model.pkl", "baseline.pkl", "scaler.pkl"):
        path = os.path.join(art_dir, fname)
        digest = hashlib.sha256()
        with open(path, "rb") as fh:
            digest.update(fh.read())
        with open(path + ".sha256", "w") as fh:
            fh.write(f"{digest.hexdigest()}  {fname}\n")
    print("saved artifacts ->", art_dir)

if __name__ == "__main__":
    main()
