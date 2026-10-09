"""API smoke: login -> dashboard -> customer -> simulate -> campaign -> experiment -> AI."""
import os
os.environ["DATABASE_URL"] = "sqlite:///./test_smoke.db"
if os.path.exists("test_smoke.db"): os.remove("test_smoke.db")
from fastapi.testclient import TestClient
from backend.main import app
from backend.seed import run

run(reset=True)
c = TestClient(app)
tok = c.post("/api/auth/login", json={"email": "admin@demobank.in", "password": "demo123"}).json()["token"]
H = {"Authorization": f"Bearer {tok}"}
assert c.get("/api/dashboard/summary", headers=H).json()["total"] > 100
custs = c.get("/api/customers", headers=H).json()
cid = custs["items"][0]["id"]
assert c.get(f"/api/customers/{cid}", headers=H).json()["explanation"]
sim = c.post("/api/roi/simulate", headers=H, json={"min_proba": 0.5, "success_rate": 0.25, "intervention_cost": 1000}).json()
assert sim["targeted"] > 0 and sim["roi_pct"] != 0
camp = c.post("/api/campaigns", headers=H, json={"name": "Smoke Test", "min_proba": 0.5}).json()
lau = c.post(f"/api/campaigns/{camp['id']}/launch", headers=H).json()
assert lau["ok"] and lau["treat_n"] > 0
assert len(c.get("/api/experiments", headers=H).json()) > 0
ai = c.post("/api/ai/ask", headers=H, json={"question": "Which segment has highest revenue at risk?"}).json()
assert "answer" in ai and len(ai["answer"]) > 20
print("SMOKE OK")
