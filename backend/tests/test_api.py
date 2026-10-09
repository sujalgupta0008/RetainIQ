"""API smoke: login -> dashboard -> customer -> simulate -> campaign -> experiment -> AI.

`python -m backend.tests.test_api` runs the same flow standalone (own throwaway DB).
"""

BANK_ADMIN = {"email": "admin@demobank.in", "password": "demo123"}


def test_login_dashboard(client):
    tok = client.post("/api/auth/login", json=BANK_ADMIN).json()["token"]
    h = {"Authorization": f"Bearer {tok}"}
    s = client.get("/api/dashboard/summary", headers=h).json()
    assert s["total"] > 100


def _headers(client):
    tok = client.post("/api/auth/login", json=BANK_ADMIN).json()["token"]
    return {"Authorization": f"Bearer {tok}"}


def test_customer_detail(client):
    h = _headers(client)
    customers = client.get("/api/customers", headers=h).json()
    cid = customers["items"][0]["id"]
    assert client.get(f"/api/customers/{cid}", headers=h).json()["explanation"]


def test_simulate(client):
    h = _headers(client)
    sim = client.post("/api/roi/simulate", headers=h,
                      json={"min_proba": 0.5, "success_rate": 0.25,
                            "intervention_cost": 1000}).json()
    assert sim["targeted"] > 0 and sim["roi_pct"] != 0


def test_campaign_launch_experiment(client):
    h = _headers(client)
    camp = client.post("/api/campaigns", headers=h,
                       json={"name": "Smoke Test", "min_proba": 0.5}).json()
    launched = client.post(f"/api/campaigns/{camp['id']}/launch", headers=h).json()
    assert launched["ok"] and launched["treat_n"] > 0
    assert len(client.get("/api/experiments", headers=h).json()) > 0


def test_ai_ask(client):
    h = _headers(client)
    ai = client.post("/api/ai/ask", headers=h,
                     json={"question": "Which segment has highest revenue at risk?"}).json()
    assert "answer" in ai and len(ai["answer"]) > 20


if __name__ == "__main__":
    # Standalone README flow (own throwaway DB, no pytest needed).
    import os
    os.environ["DATABASE_URL"] = "sqlite:///./test_smoke.db"
    if os.path.exists("test_smoke.db"):
        os.remove("test_smoke.db")
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.seed import run
    run(reset=True)
    smoke = TestClient(app)
    tok = smoke.post("/api/auth/login", json=BANK_ADMIN).json()["token"]
    headers = {"Authorization": f"Bearer {tok}"}
    assert smoke.get("/api/dashboard/summary", headers=headers).json()["total"] > 100
    customers = smoke.get("/api/customers", headers=headers).json()
    cid = customers["items"][0]["id"]
    assert smoke.get(f"/api/customers/{cid}", headers=headers).json()["explanation"]
    sim = smoke.post("/api/roi/simulate", headers=headers,
                  json={"min_proba": 0.5, "success_rate": 0.25,
                        "intervention_cost": 1000}).json()
    assert sim["targeted"] > 0 and sim["roi_pct"] != 0
    camp = smoke.post("/api/campaigns", headers=headers,
                   json={"name": "Smoke Test", "min_proba": 0.5}).json()
    launched = smoke.post(f"/api/campaigns/{camp['id']}/launch", headers=headers).json()
    assert launched["ok"] and launched["treat_n"] > 0
    assert len(smoke.get("/api/experiments", headers=headers).json()) > 0
    ai = smoke.post("/api/ai/ask", headers=headers,
                json={"question": "Which segment has highest revenue at risk?"}).json()
    assert "answer" in ai and len(ai["answer"]) > 20
    print("SMOKE OK")
