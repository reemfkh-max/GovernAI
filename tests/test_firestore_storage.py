"""Reports + audit log against Firestore (backed by an in-memory fake)."""
import pytest

from app import firebase, reports
from app.models import (
    AIUseCase,
    ComplianceStatus,
    Decision,
    DecisionResult,
    GovernanceReport,
    PolicyComplianceResult,
    ReportStatus,
    RiskAssessmentResult,
    RiskLevel,
)
from app.tools import audit_log


class FakeSnapshot:
    def __init__(self, data):
        self._data = data

    @property
    def exists(self):
        return self._data is not None

    def to_dict(self):
        return self._data


class FakeDocument:
    def __init__(self, store, doc_id):
        self._store = store
        self._id = doc_id

    def set(self, data):
        self._store[self._id] = data

    def get(self):
        return FakeSnapshot(self._store.get(self._id))


class FakeQuery:
    def __init__(self, docs):
        self._docs = docs

    def where(self, filter=None):  # noqa: A002 - mirrors the Firestore API
        field, _, value = filter
        return FakeQuery([doc for doc in self._docs if doc.get(field) == value])

    def order_by(self, field):
        return FakeQuery(sorted(self._docs, key=lambda doc: doc.get(field, "")))

    def stream(self):
        return [FakeSnapshot(doc) for doc in self._docs]


class FakeCollection:
    def __init__(self, store):
        self._store = store

    def _query(self):
        return FakeQuery(list(self._store.values()))

    def document(self, doc_id):
        return FakeDocument(self._store, doc_id)

    def where(self, filter=None):  # noqa: A002 - mirrors the Firestore API
        return self._query().where(filter=filter)

    def order_by(self, field):
        return self._query().order_by(field)

    def stream(self):
        return self._query().stream()


class FakeFirestore:
    def __init__(self):
        self.collections = {}

    def collection(self, name):
        return FakeCollection(self.collections.setdefault(name, {}))


@pytest.fixture
def fake_firestore(monkeypatch):
    client = FakeFirestore()
    monkeypatch.setattr(firebase, "get_firestore", lambda: client)
    # FieldFilter is only imported inside get_audit_log; make it a plain tuple.
    monkeypatch.setattr(
        "google.cloud.firestore_v1.base_query.FieldFilter",
        lambda field, op, value: (field, op, value),
    )
    return client


def _report(use_case_id: str, created_at: str) -> GovernanceReport:
    return GovernanceReport(
        use_case=AIUseCase(id=use_case_id, name="n", description="d", owner="o"),
        risk_assessment=RiskAssessmentResult(
            risk_level=RiskLevel.LOW, risk_score=10, rationale="r"
        ),
        policy_compliance=PolicyComplianceResult(
            status=ComplianceStatus.COMPLIANT, rationale="r"
        ),
        decision=DecisionResult(decision=Decision.APPROVE, rationale="r"),
        status=ReportStatus.COMPLETED,
        created_at=created_at,
    )


def test_reports_round_trip_through_firestore(fake_firestore):
    reports.save_report(_report("uc-2", "2026-01-02T00:00:00+00:00"))
    reports.save_report(_report("uc-1", "2026-01-01T00:00:00+00:00"))

    loaded = reports.load_report("uc-1")
    assert loaded is not None
    assert loaded.use_case.id == "uc-1"

    assert reports.load_report("missing") is None

    listed = [report.use_case.id for report in reports.list_reports()]
    assert listed == ["uc-1", "uc-2"]  # ordered by created_at


def test_audit_entries_written_and_filtered_in_firestore(fake_firestore):
    audit_log.log_event("uc-1", "intake", "system")
    audit_log.log_event("uc-2", "intake", "system")
    audit_log.log_event("uc-1", "decision", "decision_agent")

    stages = [entry["stage"] for entry in audit_log.get_audit_log("uc-1")]
    assert stages == ["intake", "decision"]
    assert len(audit_log.get_audit_log()) == 3


def test_local_files_used_when_firestore_disabled():
    """Default (no Firebase) still writes JSON files, not Firestore."""
    reports.save_report(_report("uc-file", "2026-01-01T00:00:00+00:00"))

    from app import config

    assert (config.REPORTS_DIR / "uc-file.json").exists()
    assert reports.load_report("uc-file").use_case.id == "uc-file"
