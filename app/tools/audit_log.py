"""Tool: append-only audit log.

Every stage of the governance workflow (intake, risk assessment, policy
check, decision, human approval) writes an AuditEntry here.

Two interchangeable backends:

* **Firestore** — one document per entry in the ``audit_log`` collection,
  used when Firebase is configured, so the trail survives redeploys and is
  shared across instances.
* **Local JSON-lines file** — ``data/audit_log.jsonl``, the default for
  local development: human-inspectable and easy to ship to a SIEM/warehouse.
"""
import json
import threading
from typing import Any, Dict, List, Optional

from app import config, firebase
from app.models import AuditEntry

_lock = threading.Lock()


def _collection():
    """Return the Firestore audit collection, or None when disabled."""
    client = firebase.get_firestore()
    if client is None:
        return None
    return client.collection(config.FIRESTORE_AUDIT_COLLECTION)


def log_event(use_case_id: str, stage: str, actor: str, data: Optional[Dict[str, Any]] = None) -> AuditEntry:
    """Append an audit entry.

    Args:
        use_case_id: id of the AI use case this event relates to.
        stage: workflow stage, e.g. intake, risk_assessment, policy_compliance,
            decision, human_approval.
        actor: who/what produced this event (agent name, "system", or a
            human's identifier/email).
        data: arbitrary JSON-serializable payload for this event.
    """
    entry = AuditEntry(use_case_id=use_case_id, stage=stage, actor=actor, data=data or {})

    collection = _collection()
    if collection is not None:
        collection.document(entry.id).set(entry.model_dump(mode="json"))
        return entry

    config.AUDIT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        with open(config.AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry.model_dump_json() + "\n")
    return entry


def get_audit_log(use_case_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Read audit entries, optionally filtered to a single use case."""
    collection = _collection()
    if collection is not None:
        from google.cloud.firestore_v1.base_query import FieldFilter

        query = collection
        if use_case_id is not None:
            query = query.where(filter=FieldFilter("use_case_id", "==", use_case_id))
        # Sorted client-side so a filtered read needs no composite index.
        entries = [snapshot.to_dict() for snapshot in query.stream()]
        return sorted(entries, key=lambda entry: entry.get("timestamp", ""))

    if not config.AUDIT_LOG_FILE.exists():
        return []
    entries: List[Dict[str, Any]] = []
    with open(config.AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if use_case_id is None or entry.get("use_case_id") == use_case_id:
                entries.append(entry)
    return entries


LOG_EVENT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "log_event",
        "description": (
            "Append an entry to the compliance audit log for this use case. "
            "Use this to record notable findings or reasoning checkpoints, "
            "in addition to the automatic per-stage logging the platform does."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "use_case_id": {"type": "string", "description": "The AI use case id."},
                "stage": {"type": "string", "description": "Workflow stage this note belongs to."},
                "actor": {"type": "string", "description": "Name of the agent logging this event."},
                "data": {"type": "object", "description": "Arbitrary JSON payload to record."},
            },
            "required": ["use_case_id", "stage", "actor"],
        },
    },
}
