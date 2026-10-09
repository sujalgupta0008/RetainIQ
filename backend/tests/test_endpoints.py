"""Integration coverage for dashboard / segments / analytics / experiments / misc flows."""
import pytest


def test_dashboard_all(client, bank_admin):
    for path in ("summary", "risk-dist", "revenue-by-segment", "product-risk",
                 "risk-trend", "quadrant", "campaign-perf"):
        r = client.get(f"/api/dashboard/{path}", headers=bank_admin)
        assert r.status_code == 200, (path, r.text)
    s = client.get("/api/dashboard/summary", headers=bank_admin).json()
    assert s["total"] > 100 and "revenue_at_risk" in s
    q = client.get("/api/dashboard/quadrant", headers=bank_admin).json()
    assert q["hv_hr"] + q["hv_lr"] + q["lv_hr"] + q["lv_lr"] == s["total"]


def test_segments_overview(client, bank_admin):
    r = client.get("/api/segments/overview", headers=bank_admin).json()
    assert "median_clv" in r and len(r["segments"]) > 0
    assert sum(s["count"] for s in r["segments"]) > 100


def test_analytics(client, bank_admin):
    det = client.get("/api/analytics/deterioration", headers=bank_admin)
    assert det.status_code == 200 and isinstance(det.json(), list)
    alerts = client.get("/api/analytics/alerts", headers=bank_admin)
    assert alerts.status_code == 200 and isinstance(alerts.json(), list)
    prods = client.get("/api/analytics/products", headers=bank_admin)
    assert prods.status_code == 200 and len(prods.json()) > 0


def test_predictions_metrics_shape(client, bank_admin):
    m = client.get("/api/predictions/metrics", headers=bank_admin).json()
    assert "trained" in m
    if m["trained"]:
        for k in ("auc", "precision", "recall", "f1", "n"):
            assert k in m


def test_experiments_flow(client, bank_admin):
    lst = client.get("/api/experiments", headers=bank_admin).json()
    assert len(lst) > 0
    eid = lst[0]["id"]
    one = client.get(f"/api/experiments/{eid}", headers=bank_admin).json()
    assert one["id"] == eid and "results" in one
    assert client.get("/api/experiments/99999999", headers=bank_admin).status_code == 404


def test_campaign_detail_and_relaunch_guard(client, bank_admin):
    lst = client.get("/api/campaigns", headers=bank_admin).json()
    assert len(lst) > 0
    cid = lst[0]["id"]
    one = client.get(f"/api/campaigns/{cid}", headers=bank_admin).json()
    assert one["id"] == cid
    assert client.get("/api/campaigns/99999999", headers=bank_admin).status_code == 404
    # Completed campaigns cannot be launched twice (idempotency guard).
    done = [c for c in lst if c["status"] == "completed"]
    if done:
        r = client.post(f"/api/campaigns/{done[0]['id']}/launch", headers=bank_admin)
        assert r.status_code == 400


def test_recommendations_filter(client, bank_admin):
    all_r = client.get("/api/recommendations", headers=bank_admin).json()
    assert len(all_r) > 0
    crit = client.get("/api/recommendations?priority=Critical", headers=bank_admin).json()
    assert all(r["priority"] == "Critical" for r in crit)


def test_audit_roi_data_ai_misc(client, bank_admin):
    logs = client.get("/api/audit?limit=5", headers=bank_admin).json()
    assert isinstance(logs, list) and len(logs) > 0
    sim = client.post("/api/roi/simulate", headers=bank_admin, json={}).json()
    assert set(sim["scenarios"]) == {"conservative", "expected", "optimistic"}
    st = client.get("/api/data/status", headers=bank_admin).json()
    assert st["customers"] > 100
    assert "Test User" in client.get("/api/data/sample").text
    sug = client.get("/api/ai/suggested").json()
    assert len(sug) >= 5


def test_health_root_and_security_headers(client):
    assert client.get("/api/health").json()["ok"] is True
    r = client.get("/")
    assert r.json()["service"] == "retainiq"
    for h in ("x-content-type-options", "x-frame-options", "referrer-policy",
              "content-security-policy"):
        assert h in {k.lower() for k in r.headers}, h
