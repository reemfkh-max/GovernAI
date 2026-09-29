"""Persistence for user profiles (username + job level).

Firebase Authentication only holds the email/password credentials; the extra
profile fields collected at sign-up live here, keyed by the Firebase uid.

Two interchangeable backends, like reports and the audit log:

* **Firestore** — one document per user in the ``users`` collection, used
  when Firebase is configured.
* **Local file** — ``data/users.json`` (uid -> profile), the default for
  local development and the test suite.
"""
import json
import re
import threading
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field, field_validator

from app import config, firebase

_lock = threading.Lock()

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.]{3,30}$")


class JobLevel(str, Enum):
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    MANAGER = "manager"
    DIRECTOR = "director"
    EXECUTIVE = "executive"


class UsernameTakenError(ValueError):
    """Raised when another account already uses the requested username."""


class ProfileUpdate(BaseModel):
    """Fields the user supplies at sign-up (or edits later)."""

    username: str = Field(..., description="3-30 letters, digits, '_' or '.'")
    job_level: JobLevel

    @field_validator("username")
    @classmethod
    def _check_username(cls, value: str) -> str:
        value = value.strip()
        if not USERNAME_PATTERN.match(value):
            raise ValueError(
                "Username must be 3-30 characters: letters, digits, '_' or '.'"
            )
        return value


class UserProfile(ProfileUpdate):
    uid: str
    email: Optional[str] = None
    created_at: str
    updated_at: str


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _collection():
    """Return the Firestore users collection, or None when disabled."""
    client = firebase.get_firestore()
    if client is None:
        return None
    return client.collection(config.FIRESTORE_USERS_COLLECTION)


def _read_local() -> Dict[str, dict]:
    if not config.USERS_FILE.exists():
        return {}
    return json.loads(config.USERS_FILE.read_text(encoding="utf-8"))


def _write_local(users: Dict[str, dict]) -> None:
    config.USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")


def get_profile(uid: str) -> Optional[UserProfile]:
    collection = _collection()

    if collection is not None:
        snapshot = collection.document(uid).get()
        if not snapshot.exists:
            return None
        return UserProfile.model_validate(snapshot.to_dict())

    data = _read_local().get(uid)
    return UserProfile.model_validate(data) if data else None


def _username_owner(username: str) -> Optional[str]:
    """uid of the account using `username` (case-insensitive), if any."""
    key = username.lower()
    collection = _collection()

    if collection is not None:
        from google.cloud.firestore_v1.base_query import FieldFilter

        query = collection.where(filter=FieldFilter("username_lower", "==", key))
        for snapshot in query.stream():
            return snapshot.to_dict().get("uid")
        return None

    for uid, data in _read_local().items():
        if data.get("username", "").lower() == key:
            return uid
    return None


def save_profile(uid: str, email: Optional[str], update: ProfileUpdate) -> UserProfile:
    """Create or update the profile for `uid`.

    Raises UsernameTakenError when the username belongs to another account.
    """
    with _lock:
        owner = _username_owner(update.username)
        if owner is not None and owner != uid:
            raise UsernameTakenError(f"Username '{update.username}' is already taken.")

        existing = get_profile(uid)
        now = _now()
        profile = UserProfile(
            uid=uid,
            email=email,
            username=update.username,
            job_level=update.job_level,
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
        # username_lower backs the case-insensitive uniqueness lookup.
        record = {**profile.model_dump(mode="json"), "username_lower": update.username.lower()}

        collection = _collection()
        if collection is not None:
            collection.document(uid).set(record)
        else:
            users = _read_local()
            users[uid] = record
            _write_local(users)

        return profile
