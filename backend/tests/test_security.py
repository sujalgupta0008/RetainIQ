"""Security regressions for audit fixes S01–S11. Tests are independent (fresh tenants)."""
import io
import uuid

from fastapi import UploadFile

from backend.deps import rate_limit
from backend.services import escape_like


def _unique(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"


def _register(client, email, password="StrongPass123", tenant=None, role="manager"):
    body = {"email": email, "password": password, "role": role}
    if tenant:
        body["tenant"] = tenant
    return client.post("/api/auth/register", json=body)


# S02: registration hardening

def test_register_role_admin_clamped(client):
    # Self-registration must not grant admin (privilege escalation).
    email = _unique("nobody")
    r = _register(client, email, role="admin")
    assert r.status_code == 200, r.text
    assert r.json()["role"] != "admin"
    # The clamped user is a plain manager: tenant switch must be forbidden.
    tok = r.json()["token"]
    h = {"Authorization": f"Bearer {tok}"}
    assert client.post("/api/auth/switch?tenant_id=1", headers=h).status_code == 403


def test_register_weak_password_rejected(client):
    r = _register(client, _unique("weak"), password="123")
    assert r.status_code == 422


def test_register_invalid_email_rejected(client):
    assert _register(client, "not-an-email").status_code == 422
    assert _register(client, "a@b").status_code == 422


def test_register_duplicate_rejected(client, bank_admin):
    r = _register(client, "admin@demobank.in", tenant="Demo Bank")
    assert r.status_code == 400


def test_login_wrong_password_generic(client):
    r = client.post("/api/auth/login",
                    json={"email": "admin@demobank.in", "password": "wrong-password-x"})
    assert r.status_code == 401
    # Must not reveal whether the email exists.
    assert "Invalid credentials" in r.text


def test_login_unknown_user_generic(client):
    r = client.post("/api/auth/login",
                    json={"email": _unique("ghost"), "password": "whatever123"})
    assert r.status_code == 401


# S01: tenant switch / isolation

def test_switch_non_admin_forbidden(client, bank_manager):
    assert client.post("/api/auth/switch?tenant_id=2", headers=bank_manager).status_code == 403


def test_switch_admin_roundtrip(client, bank_admin):
    # Admin switch works; unknown tenants 404. Switches back so fixtures keep home workspace.
    assert client.post("/api/auth/switch?tenant_id=999999", headers=bank_admin).status_code == 404
    me_before = client.get("/api/auth/me", headers=bank_admin).json()
    home = me_before["tenant_id"]
    other = 2 if home != 2 else 1
    assert client.post(f"/api/auth/switch?tenant_id={other}", headers=bank_admin).status_code == 200
    # Switch back so session fixtures keep pointing at the home workspace.
    back = client.post(f"/api/auth/switch?tenant_id={home}", headers=bank_admin).json()
    assert back["tenant_id"] == home
    assert client.get("/api/auth/me", headers=bank_admin).json()["tenant_id"] == home


def test_cross_tenant_customer_404(client, bank_admin, fin_admin):
    bank_cid = client.get("/api/customers", headers=bank_admin).json()["items"][0]["id"]
    assert client.get(f"/api/customers/{bank_cid}", headers=fin_admin).status_code == 404


def test_me_hides_tenants_from_non_admin(client, bank_manager):
    assert client.get("/api/auth/me", headers=bank_manager).json()["all_tenants"] == []


# input validation / caps

def test_customers_invalid_risk_rejected(client, bank_admin):
    assert client.get("/api/customers?risk=CRITICAL", headers=bank_admin).status_code == 400


def test_pagination_caps(client, bank_admin):
    assert client.get("/api/customers?page_size=1000", headers=bank_admin).status_code == 422
    assert client.get("/api/audit?limit=10000", headers=bank_admin).status_code == 422
    assert client.get("/api/recommendations?limit=10000", headers=bank_admin).status_code == 422


def test_search_wildcards_safe(client, bank_admin):
    r = client.get("/api/customers?search=%__%", headers=bank_admin)
    assert r.status_code == 200


def test_roi_validation(client, bank_admin):
    assert client.post("/api/roi/simulate", headers=bank_admin,
                       json={"success_rate": 5}).status_code == 422
    assert client.post("/api/roi/simulate", headers=bank_admin,
                       json={"intervention_cost": -10}).status_code == 422


def test_campaign_validation(client, bank_admin):
    assert client.post("/api/campaigns", headers=bank_admin,
                       json={"name": "", "offer_cost": -5}).status_code == 422


def test_ai_ask_validation_and_auth(client, bank_admin):
    assert client.post("/api/ai/ask", headers=bank_admin, json={"question": "x"}).status_code == 422
    assert client.post("/api/ai/ask", json={"question": "Which segment is riskiest?"}).status_code in (401, 403)


def test_upload_auth_and_schema(client, bank_admin):
    # No token.
    assert client.post("/api/data/preview", files={"f": ("x.csv", b"name\nA")}).status_code in (401, 403)
    # Unknown schema rejected, not 500.
    r = client.post("/api/data/preview", headers=bank_admin,
                    files={"f": ("x.csv", b"foo,bar\n1,2\n")})
    assert r.status_code == 400
    # Wrong extension rejected.
    r = client.post("/api/data/preview", headers=bank_admin,
                    files={"f": ("x.exe", b"foo,bar\n1,2\n")})
    assert r.status_code == 400


def test_upload_size_guard():
    # _read_csv must refuse oversized payloads before pandas ever sees them.
    import asyncio
    from backend.routes.data import _read_csv, MAX_UPLOAD_BYTES
    big = io.BytesIO(b"a,b\n" + b"1,2\n" * ((MAX_UPLOAD_BYTES // 4) + 100))
    f = UploadFile(filename="big.csv", file=big)
    try:
        _read_csv(f)
    except Exception as e:
        assert getattr(e, "status_code", None) == 413
    else:
        raise AssertionError("oversized CSV was not rejected")


def test_rate_limiter_trips():
    # Unit-test the limiter directly (no need to burn the shared login budget).

    class Req:
        client = type("C", (), {"host": "127.0.0.1"})()
        url = type("U", (), {"path": "/api/auth/login"})()

    check = rate_limit(3, 60)
    for _ in range(3):
        check(Req())
    try:
        check(Req())
    except Exception as e:
        assert getattr(e, "status_code", None) == 429
    else:
        raise AssertionError("rate limiter did not trip")


def test_escape_like_unit():
    assert escape_like("100%_x\\y") == "100\\%\\_x\\\\y"
    assert escape_like("") == ""


def test_unauthenticated_blocked(client):
    assert client.get("/api/dashboard/summary").status_code in (401, 403)
    assert client.get("/api/customers").status_code in (401, 403)


def test_google_unconfigured_returns_503(client, monkeypatch):
    # Default deploy has no GOOGLE_CLIENT_ID — endpoint must point at email/demo.
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    r = client.post("/api/auth/google", json={"credential": "bogus.token.here"})
    assert r.status_code == 503
    assert "email or" in r.text.lower() or "demo" in r.text.lower()


def test_google_rejects_short_credential(client):
    r = client.post("/api/auth/google", json={"credential": "x"})
    assert r.status_code == 422
