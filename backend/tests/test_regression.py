"""Bug regressions for audit fixes B01–B12 + edge cases (empty retrain, ROI clamps, S09 sidecars)."""
import uuid

from backend.schemas import RegisterIn
from backend.services import calc_roi, decode_token, escape_like, make_token


def _fresh_tenant_headers(client):
    """Register a user in a brand-new tenant (isolated workspace, zero customers)."""
    tag = uuid.uuid4().hex[:8]
    resp = client.post("/api/auth/register", json={
        "email": f"fresh_{tag}@example.com", "password": "StrongPass123",
        "tenant": f"Fresh Tenant {tag}", "role": "manager"})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['token']}"}, resp.json()["tenant_id"]


# B02: retrain on empty workspace

def test_retrain_empty_tenant_400_not_500(client):
    headers, _ = _fresh_tenant_headers(client)
    resp = client.post("/api/predictions/retrain", headers=headers)
    assert resp.status_code == 400
    assert "upload" in resp.text.lower() or "no customer" in resp.text.lower()


# B05: upload uses priority_of like seed/retrain

BANKING_CSV = (
    "name,age,income,tenure_months,region,avg_balance,txn_freq,avg_txn\n"
    "Reg Test Alpha,38,900000,30,Mumbai,120000,10,4500\n"
    "Reg Test Beta,52,2500000,80,Pune,800000,4,6000\n"
)


def test_upload_priority_consistent_with_priority_of(client):
    from backend.services import priority_of
    headers, _ = _fresh_tenant_headers(client)
    up = client.post("/api/data/upload", headers=headers,
                     files={"f": ("bank.csv", BANKING_CSV.encode())})
    assert up.status_code == 200, up.text
    assert up.json()["added"] == 2
    recs = client.get("/api/recommendations", headers=headers).json()
    assert len(recs) == 2
    # Batch normalization (like seed/retrain): maxima over the whole tenant batch.
    clv_max = max(r["clv"] for r in recs + [{"clv": 1}])
    rar_max = max(r["rar"] for r in recs + [{"rar": 1}])
    for rec in recs:
        # Previously hardcoded to Monitor/p*50; now real priority_of output.
        assert rec["priority"] in ("Critical", "High Priority", "Monitor", "Low Priority")
        assert 0 <= rec["score"] <= 100
        score, seg = priority_of(rec["proba"], rec["clv"], rec["rar"],
                             rec["cost"], rec["success"], clv_max, rar_max)
        assert rec["priority"] == seg and rec["score"] == score


def test_upload_duplicate_names_skipped(client):
    headers, _ = _fresh_tenant_headers(client)
    once = client.post("/api/data/upload", headers=headers,
                       files={"f": ("bank.csv", BANKING_CSV.encode())}).json()
    assert once["added"] == 2
    twice = client.post("/api/data/upload", headers=headers,
                        files={"f": ("bank.csv", BANKING_CSV.encode())}).json()
    assert twice["added"] == 0
    assert twice["rejected"] == 2


# ROI / finance edge cases

def test_calc_roi_clamps_nonsense():
    resp = calc_roi(-50, 5.0, -1000, -20, reach=99)
    assert resp["targeted"] >= 0 and resp["cost"] >= 0 and resp["revenue"] >= 0
    resp = calc_roi(0, 0.25, 100000, 800)
    assert resp["targeted"] == 0 and resp["retained"] == 0


def test_calc_roi_zero_audience_scenarios(client, bank_admin):
    from backend.services import scenarios
    base = calc_roi(0, 0.25, 100000, 800)
    rows = scenarios(base, 0.25)
    assert set(rows) == {"conservative", "expected", "optimistic"}


# auth token claims (B01 follow-on)

def test_token_has_iat_exp():
    token = make_token(7, 3, "manager")
    payload = decode_token(token)
    assert payload["sub"] == "7" and payload["tenant_id"] == 3
    assert "iat" in payload and "exp" in payload and payload["exp"] > payload["iat"]


def test_schema_role_clamp_unit():
    assert RegisterIn(email="a@b.co", password="StrongPass1", role="admin").role == "manager"
    assert RegisterIn(email="a@b.co", password="StrongPass1", role="weird").role == "manager"
    assert RegisterIn(email="A@B.CO", password="StrongPass1").email == "a@b.co"


# CSV / data edge cases

def test_csv_empty_and_malformed_handled(client, bank_admin):
    resp = client.post("/api/data/preview", headers=bank_admin,
                    files={"f": ("empty.csv", b"")})
    assert resp.status_code in (400, 422)
    resp = client.post("/api/data/preview", headers=bank_admin,
                    files={"f": ("bin.csv", bytes(range(256)) * 100)})
    assert resp.status_code in (200, 400)  # must never 500


def test_customer_404_and_empty_search(client, bank_admin):
    assert client.get("/api/customers/99999999", headers=bank_admin).status_code == 404
    resp = client.get("/api/customers?search=zzz_no_such_name_qqq", headers=bank_admin).json()
    assert resp["total"] == 0 and resp["items"] == []


def test_escape_like_special_chars():
    assert "%" not in escape_like("a%b").replace("\\%", "")
    assert escape_like("a_b") == "a\\_b"
