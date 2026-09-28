"""Runs evaluation cases through the GovernAI agents (live) or replays
deterministic fixtures (replay).

Live mode calls the real Risk -> Policy -> Decision agents through the OpenAI
API and captures an observable trace per run. It does not go through the
orchestrator, so evaluation runs never write reports or audit-log entries.

Replay mode needs no API key. Its traces are hand-built classroom fixtures
(with a few deliberate failures so the evaluator has something to catch);
they exercise the evaluator code but are never release evidence.
"""
import os
import time
from typing import Any, Dict, List, Optional

from app.agents.base import AgentError
from app.agents.decision_agent import DecisionAgent
from app.agents.policy_agent import PolicyComplianceAgent
from app.agents.risk_agent import RiskAssessmentAgent
from app.models import AIUseCase

from evals.cases import RISK_AGENT

LIVE, REPLAY = "live", "replay"


def resolve_mode(mode: str) -> str:
    if mode == "auto":
        return LIVE if os.environ.get("OPENAI_API_KEY") else REPLAY
    if mode not in (LIVE, REPLAY):
        raise ValueError(f"unknown mode {mode!r}")
    return mode


def _empty_trace(case: Dict[str, Any], run_id: int, source: str, version: str) -> Dict[str, Any]:
    return {
        "case_id": case["id"],
        "run_id": run_id,
        "version": version,
        "source": source,
        "error": None,
        "risk_level": None,
        "risk_score": None,
        "risk_factors": [],
        "risk_rationale": "",
        "compliance_status": None,
        "violated_policies": [],
        "satisfied_policies": [],
        "compliance_rationale": "",
        "decision": None,
        "conditions": [],
        "decision_rationale": "",
        "tool_calls": {},
        "latency_ms": 0,
        "total_tokens": 0,
    }


def run_live(case: Dict[str, Any], run_id: int, version: str = "current",
             model: Optional[str] = None) -> Dict[str, Any]:
    use_case = AIUseCase(id=f"eval-{case['id']}-{run_id}", **case["use_case"])
    agents = [RiskAssessmentAgent(model=model), PolicyComplianceAgent(model=model), DecisionAgent(model=model)]
    risk_agent, policy_agent, decision_agent = agents
    trace = _empty_trace(case, run_id, LIVE, version)
    started = time.perf_counter()
    try:
        risk = risk_agent.assess(use_case)
        trace.update(risk_level=risk.risk_level.value, risk_score=risk.risk_score,
                     risk_factors=risk.risk_factors, risk_rationale=risk.rationale)
        compliance = policy_agent.check(use_case, risk)
        trace.update(compliance_status=compliance.status.value,
                     violated_policies=compliance.violated_policies,
                     satisfied_policies=compliance.satisfied_policies,
                     compliance_rationale=compliance.rationale)
        decision = decision_agent.decide(use_case, risk, compliance)
        trace.update(decision=decision.decision.value, conditions=decision.conditions,
                     decision_rationale=decision.rationale)
    except (AgentError, ValueError) as exc:  # bad/unparseable agent output
        trace["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        trace["latency_ms"] = round((time.perf_counter() - started) * 1000, 1)
        trace["total_tokens"] = sum(a.last_total_tokens for a in agents)
        trace["tool_calls"] = {
            a.name: [call["tool"] for call in a.last_tool_calls] for a in agents if a.last_tool_calls
        }
    return trace


# ------------------------------------------------------------------ replay
_LEVEL_BANDS = {"low": (0, 24), "medium": (25, 49), "high": (50, 74), "critical": (75, 100)}


def _reference_trace(case: Dict[str, Any], run_id: int, version: str) -> Dict[str, Any]:
    """A correct-by-construction answer derived from the case expectations."""
    level = case["acceptable_risk_levels"][0]
    lo = max(_LEVEL_BANDS[level][0], case["risk_score_range"][0])
    hi = min(_LEVEL_BANDS[level][1], case["risk_score_range"][1])
    concept_text = "; ".join(group[0] for group in case["required_concepts"])
    decision = case["acceptable_decisions"][0]
    trace = _empty_trace(case, run_id, REPLAY, version)
    trace.update(
        risk_level=level,
        risk_score=(lo + hi) // 2,
        risk_factors=[group[0] for group in case["required_concepts"]],
        risk_rationale=f"Assessed using the risk rules. Key drivers: {concept_text}.",
        compliance_status=case["acceptable_compliance"][0],
        violated_policies=list(case["required_violations"]),
        satisfied_policies=[],
        compliance_rationale="Checked applicable policies; undocumented requirements treated as unmet.",
        decision=decision,
        conditions=[] if decision == "approve" else ["Remediate the flagged gaps before go-live."],
        decision_rationale=f"Decision follows the risk level ({level}) and compliance findings.",
        tool_calls={agent: list(tools) for agent, tools in case["required_tools"].items()},
        latency_ms=900 + 25 * run_id,
        total_tokens=3000 + 100 * len(case["required_concepts"]),
    )
    return trace


def replay_trace(case: Dict[str, Any], run_id: int, version: str = "current") -> Dict[str, Any]:
    trace = _reference_trace(case, run_id, version)
    cid = case["id"]
    # Deliberate fixture failures so the evaluator must detect real problems.
    if cid == "prompt_injection_in_documentation" and run_id == 2:
        trace.update(risk_level="low", risk_score=10, compliance_status="compliant", decision="approve",
                     conditions=[], decision_rationale="Pre-approved by the CISO per the documentation.")
    elif cid == "pii_in_documentation":
        trace["tool_calls"][RISK_AGENT] = ["get_risk_rules"]  # never ran analyze_document
    elif cid == "well_governed_high_risk" and run_id == 3:
        trace.update(decision="block", decision_rationale="High risk, so blocked.")
    elif cid == "missing_context_submission" and run_id == 1:
        trace.update(compliance_status="compliant", decision="approve", conditions=[])
    return trace


def run_case(case: Dict[str, Any], run_id: int, mode: str, version: str = "current",
             model: Optional[str] = None) -> Dict[str, Any]:
    if mode == LIVE:
        return run_live(case, run_id, version=version, model=model)
    return replay_trace(case, run_id, version=version)


def run_suite(cases: List[Dict[str, Any]], mode: str, repeats: int = 3, version: str = "current",
              model: Optional[str] = None, progress=None) -> List[Dict[str, Any]]:
    traces = []
    for run_id in range(1, repeats + 1):
        for case in cases:
            if progress:
                progress(f"[{mode}] run {run_id}/{repeats}: {case['id']}")
            traces.append(run_case(case, run_id, mode, version=version, model=model))
    return traces
