"""Pytest fixtures: isolated sqlite DB (test_audit.db), seeded once per session.

DATABASE_URL is set before any backend import so the engine points at the
throwaway file and the real retainiq.db is never touched by tests.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_audit.db")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

DB_FILE = "test_audit.db"


def _seed_once():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    # Import AFTER env is set + stale file removed so engine binds to the fresh file.
    from backend.seed import run
    run(reset=True)


@pytest.fixture(scope="session")
def client():
    _seed_once()
    from backend.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def bank_admin(client):
    """Seeded Demo Bank admin (admin@demobank.in / demo123)."""
    token = client.post("/api/auth/login",
                      json={"email": "admin@demobank.in", "password": "demo123"}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def fin_admin(client):
    token = client.post("/api/auth/login",
                      json={"email": "admin@demofintech.in", "password": "demo123"}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def bank_manager(client):
    token = client.post("/api/auth/login",
                      json={"email": "manager@demobank.in", "password": "demo123"}).json()["token"]
    return {"Authorization": f"Bearer {token}"}
