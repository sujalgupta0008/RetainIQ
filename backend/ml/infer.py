"""Inference: loads artifacts or deterministic rule fallback so app always runs."""
import os, json, math
import numpy as np
from . import explain as _ex  # noqa (keeps package importable)

ART = os.path.join(os.path.dirname(__file__), "artifacts")
FEATS = ["tenure_months","age","income","avg_balance","balance_trend","txn_freq","avg_txn",
 "txn_trend","card_usage","product_count","has_loan","complaints","resolution_days",
 "logins","engagement_decline","inactivity_days","failed_rate"]

_model = _scaler = None

def _load():
    global _model, _scaler
    import pickle
    try:
        with open(os.path.join(ART, "model.pkl"), "rb") as f: _model = pickle.load(f)
        with open(os.path.join(ART, "scaler.pkl"), "rb") as f: _scaler = pickle.load(f)
        return True
    except Exception:
        _model = _scaler = None
        return False

def _rule(feats: dict) -> float:
    z = (-0.05*feats.get("tenure_months", 24)/12 + 0.9*feats.get("complaints", 0)
         - 2.2*feats.get("txn_trend", 0) - 1.8*feats.get("balance_trend", 0)
         + 1.5*feats.get("engagement_decline", 0) + 0.04*feats.get("inactivity_days", 0)
         - 0.5*feats.get("product_count", 1) - 0.06*feats.get("logins", 8)
         + 3.0*feats.get("failed_rate", 0) - 0.8)
    return 1/(1+math.exp(-z))

def predict_proba(feats: dict) -> float:
    if _model is None: _load()
    if _model is not None and _scaler is not None:
        try:
            import numpy as np
            v = np.array([[float(feats.get(k, 0)) for k in FEATS]])
            v = _scaler.transform(v)
            p = float(_model.predict_proba(v)[0][1])
            return max(0.01, min(0.99, p))
        except Exception:
            pass
    return round(max(0.01, min(0.99, _rule(feats))), 4)
