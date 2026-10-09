"""Explainability stub (SHAP when available, else services fallback)."""
def shap_drivers(feats: dict, medians: dict):
    try:
        import shap  # optional
        return None  # SHAP path used in train-time analysis; per-request uses fallback for speed
    except Exception:
        return None
