"""Firebase authentication layer (token verification is mocked)."""
import pytest
from fastapi.testclient import TestClient

from app import config, firebase
from app.api import app

client = TestClient(app)


@pytest.fixture
def fake_firebase(monkeypatch):
    """Pretend Firebase is configured and accept one known ID token."""

    def verify(token: str):
        if token != "good-token":
            raise ValueError("Invalid Firebase ID token: expired")
        return {
            "uid": "uid-123",
            "email": "lujain@acme.com",
            "name": "Lujain",
            "email_verified": True,
        }

    monkeypatch.setattr(firebase, "verify_id_token", verify)


def test_anonymous_allowed_when_auth_not_required():
    resp = client.get("/auth/me")
    assert resp.status_code == 200
    assert resp.json() == {"authenticated": False}


def test_valid_token_identifies_the_caller(fake_firebase):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer good-token"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["authenticated"] is True
    assert body["uid"] == "uid-123"
    assert body["email"] == "lujain@acme.com"


def test_invalid_token_is_rejected(fake_firebase):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer bad-token"})
    assert resp.status_code == 401


def test_missing_token_rejected_when_auth_required(monkeypatch):
    monkeypatch.setattr(config, "REQUIRE_AUTH", True)
    resp = client.get("/use-cases")
    assert resp.status_code == 401


def test_token_without_firebase_configured_is_rejected_when_auth_required(monkeypatch):
    monkeypatch.setattr(config, "REQUIRE_AUTH", True)
    resp = client.get("/use-cases", headers={"Authorization": "Bearer whatever"})
    # No Firebase credentials in the test environment -> cannot verify.
    assert resp.status_code == 503


def test_approver_comes_from_the_verified_token(fake_firebase, monkeypatch):
    """A signed-in caller's identity wins over whatever the client sends."""
    captured = {}

    from app import api

    def fake_decision(self, use_case_id, *, approved, approver, notes=None):
        captured["approver"] = approver
        raise api.UseCaseNotFoundError(use_case_id)

    monkeypatch.setattr(
        api.GovernanceOrchestrator, "apply_human_decision", fake_decision
    )

    resp = client.post(
        "/use-cases/abc/approve",
        json={"approved": True, "approver": "someone-else@evil.test"},
        headers={"Authorization": "Bearer good-token"},
    )

    assert resp.status_code == 404
    assert captured["approver"] == "lujain@acme.com"


def test_approver_required_when_anonymous_and_unset():
    resp = client.post("/use-cases/abc/approve", json={"approved": True})
    assert resp.status_code == 422
