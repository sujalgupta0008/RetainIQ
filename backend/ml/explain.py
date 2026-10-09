"""Explainability stub (SHAP when available, else services fallback)."""
def shap_drivers(feats: dict, medians: dict):
    # No heavy optional deps: per-request explanations use the deterministic
    # services.explain_fallback (SHAP path reserved for offline train-time analysis).
    return None
