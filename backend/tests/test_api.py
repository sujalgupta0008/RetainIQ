"""API smoke: login -> dashboard -> customer -> simulate -> campaign -> experiment -> AI.

Converted from an import-time script (which executed seed + asserts on collection) to
real pytest test functions sharing the session-scoped seeded client from conftest.
`python -m backend.tests.test_api` still runs the same flow standalone for the README.
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
    custs = client.get("/api/customers", headers=h).json()
    cid = custs["items"][0]["id"]
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
    lau = client.post(f"/api/campaigns/{camp['id']}/launch", headers=h).json()
    assert lau["ok"] and lau["treat_n"] > 0
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
    c = TestClient(app)
    tok = c.post("/api/auth/login", json=BANK_ADMIN).json()["token"]
    H = {"Authorization": f"Bearer {tok}"}
    assert c.get("/api/dashboard/summary", headers=H).json()["total"] > 100
    custs = c.get("/api/customers", headers=H).json()
    cid = custs["items"][0]["id"]
    assert c.get(f"/api/customers/{cid}", headers=H).json()["explanation"]
    sim = c.post("/api/roi/simulate", headers=H,
                 json={"min_proba": 0.5, "success_rate": 0.25,
                       "intervention_cost": 1000}).json()
    assert sim["targeted"] > 0 and sim["roi_pct"] != 0
    camp = c.post("/api/campaigns", headers=H,
                  json={"name": "Smoke Test", "min_proba": 0.5}).json()
    lau = c.post(f"/api/campaigns/{camp['id']}/launch", headers=H).json()
    assert lau["ok"] and lau["treat_n"] > 0
    assert len(c.get("/api/experiments", headers=H).json()) > 0
    ai = c.post("/api/ai/ask", headers=H,
                json={"question": "Which segment has highest revenue at risk?"}).json()
    assert "answer" in ai and len(ai["answer"]) > 20
    print("SMOKE OK")
