"""FastAPI application exposing the governance workflow over HTTP."""

import os
from typing import List, Optional

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app import config, firebase
from app.auth import AuthenticatedUser, require_user
from app.llm_client import ConfigurationError
from app.models import AIUseCase, AuditEntry, GovernanceReport
from app.orchestrator import (
    GovernanceOrchestrator,
    InvalidApprovalStateError,
    UseCaseNotFoundError,
)
from app.reports import list_reports, load_report
from app.tools.audit_log import get_audit_log
from app.tools.document_extract import (
    MAX_FILE_SIZE,
    DocumentExtractionError,
    UnsupportedFileTypeError,
    extract_text,
)
from app.tools.policy_repository import add_policy, get_policies
from app.tools.risk_rules import add_risk_rule, get_risk_rules
from app.users import ProfileUpdate, UserProfile, UsernameTakenError, get_profile, save_profile


app = FastAPI(
    title="GovernAI",
    description="Multi-Agent AI Governance Platform",
    version="0.1.0",
)

# Extra origins (e.g. a Firebase Hosting domain) can be added with
# GOVERNAI_CORS_ORIGINS as a comma-separated list.
CORS_ORIGINS = ["http://localhost:5173"] + [
    origin.strip()
    for origin in os.environ.get("GOVERNAI_CORS_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UseCaseSubmission(BaseModel):
    name: str
    description: str
    owner: str
    data_classification: Optional[str] = None
    deployment_context: Optional[str] = None
    autonomy_level: Optional[str] = None
    documentation: Optional[str] = None


class ApprovalRequest(BaseModel):
    approved: bool
    # Optional: when the caller is signed in with Firebase, their verified
    # identity is used instead of whatever the client sends.
    approver: Optional[str] = None
    notes: Optional[str] = None


class PolicySubmission(BaseModel):
    id: str
    title: str
    category: str
    description: str
    status: str = "active"
    coverage: int = 100
    min_risk_level: str = "low"


class RiskRuleSubmission(BaseModel):
    id: str
    title: str
    category: str
    severity: str
    condition: str
    action: str


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "firebase": firebase.is_enabled(),
        "firestore": firebase.firestore_enabled(),
        "auth_required": config.REQUIRE_AUTH,
    }


@app.get("/auth/me")
def whoami(user: Optional[AuthenticatedUser] = Depends(require_user)) -> dict:
    """Echo back the identity behind the caller's Firebase ID token."""
    if user is None:
        return {"authenticated": False}
    return {"authenticated": True, **user.model_dump()}


# =========================================================
# USER PROFILES
# =========================================================

def _signed_in(user: Optional[AuthenticatedUser]) -> AuthenticatedUser:
    """Profiles are keyed by uid, so they always need a verified caller."""
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in to manage your profile")
    return user


@app.get("/users/me", response_model=UserProfile)
def read_my_profile(
    user: Optional[AuthenticatedUser] = Depends(require_user),
) -> UserProfile:
    profile = get_profile(_signed_in(user).uid)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not set up yet")
    return profile


@app.put("/users/me", response_model=UserProfile)
def update_my_profile(
    payload: ProfileUpdate,
    user: Optional[AuthenticatedUser] = Depends(require_user),
) -> UserProfile:
    user = _signed_in(user)
    try:
        return save_profile(user.uid, user.email, payload)
    except UsernameTakenError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


# =========================================================
# POLICIES
# =========================================================

@app.get("/policies")
def list_policies(user: Optional[AuthenticatedUser] = Depends(require_user)) -> list:
    return get_policies()


@app.post("/policies")
def create_policy(
    payload: PolicySubmission,
    user: Optional[AuthenticatedUser] = Depends(require_user),
) -> dict:
    policy = payload.model_dump()

    try:
        return add_policy(policy)
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


# =========================================================
# RISK RULES
# =========================================================

@app.get("/risk-rules")
def list_risk_rules(user: Optional[AuthenticatedUser] = Depends(require_user)) -> list:
    return get_risk_rules()


@app.post("/risk-rules")
def create_risk_rule(
    payload: RiskRuleSubmission,
    user: Optional[AuthenticatedUser] = Depends(require_user),
) -> dict:
    rule = payload.model_dump()

    try:
        return add_risk_rule(rule)
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


# =========================================================
# AI USE CASES
# =========================================================

@app.post(
    "/use-cases",
    response_model=GovernanceReport,
)
def submit_use_case(
    payload: UseCaseSubmission,
    user: Optional[AuthenticatedUser] = Depends(require_user),
) -> GovernanceReport:
    use_case = AIUseCase(**payload.model_dump())

    orchestrator = GovernanceOrchestrator()

    try:
        return orchestrator.run(use_case)
    except ConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc


@app.get(
    "/use-cases",
    response_model=List[GovernanceReport],
)
def get_all_reports(
    user: Optional[AuthenticatedUser] = Depends(require_user),
) -> List[GovernanceReport]:
    return list_reports()


@app.get(
    "/use-cases/{use_case_id}",
    response_model=GovernanceReport,
)
def get_report(
    use_case_id: str,
    user: Optional[AuthenticatedUser] = Depends(require_user),
) -> GovernanceReport:
    report = load_report(use_case_id)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Use case not found",
        )

    return report


@app.post(
    "/use-cases/{use_case_id}/approve",
    response_model=GovernanceReport,
)
def approve_use_case(
    use_case_id: str,
    payload: ApprovalRequest,
    user: Optional[AuthenticatedUser] = Depends(require_user),
) -> GovernanceReport:
    approver = user.actor if user is not None else payload.approver

    if not approver:
        raise HTTPException(
            status_code=422,
            detail="An approver is required (sign in, or send an approver field).",
        )

    orchestrator = GovernanceOrchestrator()

    try:
        return orchestrator.apply_human_decision(
            use_case_id,
            approved=payload.approved,
            approver=approver,
            notes=payload.notes,
        )

    except UseCaseNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Use case not found",
        ) from exc

    except InvalidApprovalStateError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


# =========================================================
# DOCUMENTS
# =========================================================

@app.post("/documents/extract")
async def extract_document(
    file: UploadFile = File(...),
    user: Optional[AuthenticatedUser] = Depends(require_user),
) -> dict:
    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"{file.filename} exceeds the 25 MB upload limit.",
        )

    try:
        result = extract_text(file.filename, content)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except DocumentExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "filename": file.filename,
        "size": len(content),
        "text": result.text,
        "word_count": result.word_count,
        "pages": result.pages,
    }


# =========================================================
# AUDIT LOG
# =========================================================

@app.get(
    "/audit-log",
    response_model=List[AuditEntry],
)
def audit_log(
    use_case_id: Optional[str] = None,
    user: Optional[AuthenticatedUser] = Depends(require_user),
) -> List[AuditEntry]:
    return get_audit_log(use_case_id)