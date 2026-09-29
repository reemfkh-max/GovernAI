"""User profiles: username + job level stored alongside Firebase Auth."""
import pytest
from fastapi.testclient import TestClient

from app import firebase, users
from app.api import app
from app.users import JobLevel, ProfileUpdate, UsernameTakenError

from tests.test_firestore_storage import fake_firestore  # noqa: F401 - fixture

client = TestClient(app)

TOKENS = {
    "token-a": {"uid": "uid-a", "email": "a@acme.com"},
    "token-b": {"uid": "uid-b", "email": "b@acme.com"},
}


@pytest.fixture(autouse=True)
def fake_firebase(monkeypatch):
    def verify(token: str):
        if token not in TOKENS:
            raise ValueError("Invalid Firebase ID token")
        return TOKENS[token]

    monkeypatch.setattr(firebase, "verify_id_token", verify)


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_profile_round_trip():
    resp = client.put(
        "/users/me",
        json={"username": "lujain", "job_level": "senior"},
        headers=auth("token-a"),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["uid"] == "uid-a"
    assert body["email"] == "a@acme.com"
    assert body["username"] == "lujain"
    assert body["job_level"] == "senior"

    resp = client.get("/users/me", headers=auth("token-a"))
    assert resp.status_code == 200
    assert resp.json()["username"] == "lujain"


def test_update_keeps_created_at():
    first = client.put(
        "/users/me", json={"username": "lujain", "job_level": "mid"}, headers=auth("token-a")
    ).json()
    second = client.put(
        "/users/me", json={"username": "lujain", "job_level": "lead"}, headers=auth("token-a")
    ).json()
    assert second["job_level"] == "lead"
    assert second["created_at"] == first["created_at"]


def test_missing_profile_is_404():
    assert client.get("/users/me", headers=auth("token-b")).status_code == 404


def test_profile_needs_a_signed_in_user():
    assert client.get("/users/me").status_code == 401
    resp = client.put("/users/me", json={"username": "anon", "job_level": "junior"})
    assert resp.status_code == 401


def test_username_is_unique_case_insensitively():
    client.put(
        "/users/me", json={"username": "Lujain", "job_level": "mid"}, headers=auth("token-a")
    )
    resp = client.put(
        "/users/me", json={"username": "lujain", "job_level": "mid"}, headers=auth("token-b")
    )
    assert resp.status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "ab", "job_level": "mid"},
        {"username": "has space", "job_level": "mid"},
        {"username": "lujain", "job_level": "wizard"},
        {"username": "lujain"},
    ],
)
def test_invalid_profiles_rejected(payload):
    resp = client.put("/users/me", json=payload, headers=auth("token-a"))
    assert resp.status_code == 422


def test_profiles_stored_in_firestore(fake_firestore):  # noqa: F811
    users.save_profile("uid-a", "a@acme.com", ProfileUpdate(username="lujain", job_level="manager"))

    stored = fake_firestore.collections["users"]["uid-a"]
    assert stored["username"] == "lujain"
    assert stored["job_level"] == "manager"

    assert users.get_profile("uid-a").job_level is JobLevel.MANAGER

    with pytest.raises(UsernameTakenError):
        users.save_profile("uid-b", None, ProfileUpdate(username="LUJAIN", job_level="mid"))
