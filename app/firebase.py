"""Firebase Admin SDK integration (authentication + Firestore).

Firebase is optional: when no credentials are configured the platform keeps
working exactly as before — local JSON files for reports and the audit log,
and no token verification on the API. That keeps `pytest` and local demos
runnable without a Firebase project.

Credentials are resolved in this order:

1. ``FIREBASE_CREDENTIALS_JSON`` — the full service-account JSON, inline
   (handy for container/CI secrets).
2. ``FIREBASE_CREDENTIALS_FILE`` / ``GOOGLE_APPLICATION_CREDENTIALS`` — path
   to a service-account JSON file downloaded from the Firebase console
   (Project settings → Service accounts → Generate new private key).
3. Application Default Credentials — e.g. when running on Google Cloud.
"""
import json
import threading
from typing import Any, Dict

from app import config

_lock = threading.Lock()
_app = None
_firestore_client = None
_init_attempted = False


class FirebaseNotConfiguredError(RuntimeError):
    """Raised when Firebase is required but no credentials are available."""


def _load_credentials():
    """Build a firebase_admin credential object, or None for ADC."""
    from firebase_admin import credentials

    if config.FIREBASE_CREDENTIALS_JSON:
        info = json.loads(config.FIREBASE_CREDENTIALS_JSON)
        return credentials.Certificate(info)

    if config.FIREBASE_CREDENTIALS_FILE:
        return credentials.Certificate(config.FIREBASE_CREDENTIALS_FILE)

    return None


def get_app():
    """Initialise (once) and return the firebase_admin app, or None.

    Returns None when Firebase is not configured for this deployment.
    """
    global _app, _init_attempted

    if _app is not None:
        return _app

    with _lock:
        if _app is not None:
            return _app
        if _init_attempted:
            return _app
        _init_attempted = True

        if not config.firebase_configured():
            return None

        import firebase_admin

        options: Dict[str, Any] = {}
        if config.FIREBASE_PROJECT_ID:
            options["projectId"] = config.FIREBASE_PROJECT_ID

        try:
            _app = firebase_admin.get_app()
        except ValueError:
            _app = firebase_admin.initialize_app(_load_credentials(), options or None)

        return _app


def is_enabled() -> bool:
    """True when Firebase credentials/project are configured."""
    return get_app() is not None


def get_firestore():
    """Return a Firestore client, or None when Firestore is not enabled."""
    global _firestore_client

    if not config.FIRESTORE_ENABLED:
        return None

    app = get_app()
    if app is None:
        return None

    if _firestore_client is None:
        with _lock:
            if _firestore_client is None:
                from firebase_admin import firestore

                _firestore_client = firestore.client(app)

    return _firestore_client


def firestore_enabled() -> bool:
    """True when reports/audit entries should be stored in Firestore."""
    return get_firestore() is not None


def verify_id_token(token: str) -> Dict[str, Any]:
    """Verify a Firebase ID token and return its decoded claims.

    Raises FirebaseNotConfiguredError when Firebase is not set up, and
    ValueError when the token is missing, expired, or invalid.
    """
    app = get_app()
    if app is None:
        raise FirebaseNotConfiguredError(
            "Firebase is not configured. Set FIREBASE_PROJECT_ID and service "
            "account credentials to enable authentication."
        )

    from firebase_admin import auth as firebase_auth

    try:
        return firebase_auth.verify_id_token(token, app=app)
    except Exception as exc:  # firebase_admin raises several token subclasses
        raise ValueError(f"Invalid Firebase ID token: {exc}") from exc


def reset_for_tests() -> None:
    """Drop cached clients so tests can toggle configuration."""
    global _app, _firestore_client, _init_attempted
    with _lock:
        _app = None
        _firestore_client = None
        _init_attempted = False

