"""Central configuration for the GovernAI platform.

All settings are read from environment variables (optionally loaded from a
.env file) so the platform can be configured without touching code.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _flag(name: str, default: bool = False) -> bool:
    """Read a boolean environment variable ("1", "true", "yes" are truthy)."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


BASE_DIR = Path(__file__).resolve().parent.parent

# --- Storage locations -----------------------------------------------------
DATA_DIR = Path(os.environ.get("GOVERNAI_DATA_DIR", BASE_DIR / "data"))
REPORTS_DIR = DATA_DIR / "reports"
POLICIES_FILE = DATA_DIR / "policies.yaml"
RISK_RULES_FILE = DATA_DIR / "risk_rules.yaml"
AUDIT_LOG_FILE = DATA_DIR / "audit_log.jsonl"
USERS_FILE = DATA_DIR / "users.json"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# --- OpenAI (LLM provider) --------------------------------------------------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

MAX_TOOL_ITERATIONS = int(os.environ.get("GOVERNAI_MAX_TOOL_ITERATIONS", "5"))

# --- Firebase (authentication + Firestore) ----------------------------------
# All optional: without them GovernAI falls back to local file storage and
# leaves the API unauthenticated (fine for local demos and the test suite).
FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID")
FIREBASE_CREDENTIALS_JSON = os.environ.get("FIREBASE_CREDENTIALS_JSON")
FIREBASE_CREDENTIALS_FILE = os.environ.get("FIREBASE_CREDENTIALS_FILE") or os.environ.get(
    "GOOGLE_APPLICATION_CREDENTIALS"
)

# Store reports + audit entries in Firestore instead of local files.
FIRESTORE_ENABLED = _flag("GOVERNAI_USE_FIRESTORE", default=True)
FIRESTORE_REPORTS_COLLECTION = os.environ.get(
    "FIRESTORE_REPORTS_COLLECTION", "governance_reports"
)
FIRESTORE_AUDIT_COLLECTION = os.environ.get("FIRESTORE_AUDIT_COLLECTION", "audit_log")
FIRESTORE_USERS_COLLECTION = os.environ.get("FIRESTORE_USERS_COLLECTION", "users")

# Reject API requests that carry no valid Firebase ID token.
REQUIRE_AUTH = _flag("GOVERNAI_REQUIRE_AUTH", default=False)


def firebase_configured() -> bool:
    """True when enough Firebase settings are present to initialise the SDK."""
    return bool(
        FIREBASE_PROJECT_ID
        or FIREBASE_CREDENTIALS_JSON
        or FIREBASE_CREDENTIALS_FILE
    )
