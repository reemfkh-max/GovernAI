"""Persistence for GovernanceReport objects.

Two interchangeable backends:

* **Firestore** — one document per use case in the
  ``governance_reports`` collection, used when Firebase is configured.
* **Local files** — one JSON file per use case under ``data/reports/``,
  the default for local development and the test suite.
"""
from typing import List, Optional

from app import config, firebase
from app.models import GovernanceReport


def _collection():
    """Return the Firestore reports collection, or None when disabled."""
    client = firebase.get_firestore()
    if client is None:
        return None
    return client.collection(config.FIRESTORE_REPORTS_COLLECTION)


def save_report(report: GovernanceReport) -> None:
    collection = _collection()

    if collection is not None:
        collection.document(report.use_case.id).set(report.model_dump(mode="json"))
        return

    path = config.REPORTS_DIR / f"{report.use_case.id}.json"
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")


def load_report(use_case_id: str) -> Optional[GovernanceReport]:
    collection = _collection()

    if collection is not None:
        snapshot = collection.document(use_case_id).get()
        if not snapshot.exists:
            return None
        return GovernanceReport.model_validate(snapshot.to_dict())

    path = config.REPORTS_DIR / f"{use_case_id}.json"
    if not path.exists():
        return None
    return GovernanceReport.model_validate_json(path.read_text(encoding="utf-8"))


def list_reports() -> List[GovernanceReport]:
    collection = _collection()

    if collection is not None:
        query = collection.order_by("created_at")
        return [
            GovernanceReport.model_validate(snapshot.to_dict())
            for snapshot in query.stream()
        ]

    reports = []
    for path in sorted(config.REPORTS_DIR.glob("*.json")):
        reports.append(GovernanceReport.model_validate_json(path.read_text(encoding="utf-8")))
    return reports
