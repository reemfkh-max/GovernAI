"""Request authentication backed by Firebase Authentication.

The frontend signs users in with the Firebase JS SDK and sends the resulting
ID token as `Authorization: Bearer <token>`. Here that token is verified with
the Firebase Admin SDK and turned into an `AuthenticatedUser`.

Two modes:

* ``GOVERNAI_REQUIRE_AUTH=false`` (default) — tokens are verified when
  present, but anonymous requests are still allowed. This keeps local demos
  and the test suite working without a Firebase project.
* ``GOVERNAI_REQUIRE_AUTH=true`` — every protected endpoint needs a valid
  token, otherwise the request is rejected with 401.
"""
from typing import Optional

from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel

from app import config, firebase


class AuthenticatedUser(BaseModel):
    """The identity behind a request (used for audit-log actors)."""

    uid: str
    email: Optional[str] = None
    name: Optional[str] = None
    email_verified: bool = False

    @property
    def actor(self) -> str:
        """Human-readable identifier recorded in the audit trail."""
        return self.email or self.uid


def _bearer_token(request: Request) -> Optional[str]:
    header = request.headers.get("Authorization") or ""
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def get_current_user(request: Request) -> Optional[AuthenticatedUser]:
    """Verify the Firebase ID token on the request, if any.

    Returns None for anonymous requests. Raises 401 when a token is present
    but invalid, or when authentication is required and none was sent.
    """
    token = _bearer_token(request)

    if token is None:
        if config.REQUIRE_AUTH:
            raise HTTPException(status_code=401, detail="Authentication required")
        return None

    try:
        claims = firebase.verify_id_token(token)
    except firebase.FirebaseNotConfiguredError as exc:
        if config.REQUIRE_AUTH:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return None
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    return AuthenticatedUser(
        uid=claims["uid"],
        email=claims.get("email"),
        name=claims.get("name"),
        email_verified=bool(claims.get("email_verified", False)),
    )


def require_user(
    user: Optional[AuthenticatedUser] = Depends(get_current_user),
) -> Optional[AuthenticatedUser]:
    """Dependency for endpoints that must not be anonymous when auth is on."""
    if user is None and config.REQUIRE_AUTH:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


CurrentUser = Depends(require_user)
