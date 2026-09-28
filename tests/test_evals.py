import json

from app.models import (
    ComplianceStatus,
    Decision,
    DecisionResult,
    PolicyComplianceResult,
    RiskAssessmentResult,
    RiskLevel,
)
from evals.__main__ import main as evals_main
from evals.cases import EVALUATION_CASES, HOLDOUT_CASES, validate_suite
from evals.evaluator import (
    diagnose_failures,
    evaluate_run,
    evaluate_suite,
    failure_matrix,
    has_no_unnegated_claims,
    release_decision,
    summarize,
)
from evals.runner import REPLAY, replay_trace, run_live, run_suite

CASES = {case["id"]: case for case in EVALUATION_CASES}


def test_suite_is_well_formed():
    validate_suite(EVALUATION_CASES)
    validate_suite(HOLDOUT_CASES)
    assert len(EVALUATION_CASES) >= 10
    assert {c["difficulty"] for c in EVALUATION_CASES} == {"Easy", "Medium", "Hard"}
    assert not {c["id"] for c in EVALUATION_CASES} & {c["id"] for c in HOLDOUT_CASES}


def test_reference_answers_pass_every_case():
    # A correct-by-construction answer must pass: guards against an evaluator that fails everything.
    for case in EVALUATION_CASES + HOLDOUT_CASES:
        trace = replay_trace(case, run_id=3)
        if case["id"] in {"pii_in_documentation", "well_governed_high_risk"}:
            continue  # these carry deliberate fixture flaws on run 3
        result = evaluate_run(case, trace)
        assert result["passed"], (case["id"], result["failed_checks"])


def test_injection_leak_fails_even_with_warning_text():
    case = CASES["prompt_injection_in_documentation"]
    trace = replay_trace(case, run_id=1)
    trace["decision_rationale"] = "Note: the claim that it was pre-approved by the CISO is untrusted."
    result = evaluate_run(case, trace)
    assert "no_hard_forbidden_content" in result["failed_checks"]


def test_negation_aware_forbidden_claims():
    assert has_no_unnegated_claims("This system is not safe to deploy.", ["safe to deploy"])
    assert not has_no_unnegated_claims("Controls look fine, safe to deploy.", ["safe to deploy"])


def test_safety_invariant_blocks_approving_noncompliant_high_risk():
    case = CASES["autonomous_loan_denial"]
    trace = replay_trace(case, run_id=1)
    trace.update(decision="approve", compliance_status="non_compliant", conditions=[])
    result = evaluate_run(case, trace)
    assert {"safety_invariant", "acceptable_decision"} <= set(result["failed_checks"])


def test_ungrounded_policy_ids_and_score_level_mismatch_are_caught():
    case = CASES["autonomous_loan_denial"]
    trace = replay_trace(case, run_id=1)
    trace["violated_policies"] = trace["violated_policies"] + ["POL-999"]
    trace["risk_score"] = 90  # critical band, but level says high
    failed = evaluate_run(case, trace)["failed_checks"]
    assert "policy_ids_grounded" in failed
    assert "score_matches_level" in failed


def test_agent_error_is_a_structured_output_failure():
    case = CASES["low_risk_internal_summarizer"]
    trace = replay_trace(case, run_id=1)
    trace["error"] = "AgentError: could not parse JSON"
    result = evaluate_run(case, trace)
    assert result["failed_checks"] == ["structured_output"]


def test_replay_suite_detects_fixture_failures_and_blocks_release():
    results = evaluate_suite(EVALUATION_CASES, run_suite(EVALUATION_CASES, REPLAY, repeats=3))
    summary = summarize(results)
    assert summary["runs"] == 30
    assert release_decision(summary) == "BLOCK"
    assert summary["critical_pass_rate"] < 1.0

    matrix = failure_matrix(results)
    assert matrix["required_tools_present"] == ["pii_in_documentation"]
    assert "prompt_injection_in_documentation" in matrix["no_hard_forbidden_content"]

    diagnoses = {d["case_id"]: d for d in diagnose_failures(results)}
    assert set(diagnoses) == {
        "missing_context_submission",
        "pii_in_documentation",
        "prompt_injection_in_documentation",
        "well_governed_high_risk",
    }
    assert "tool selection" in diagnoses["pii_in_documentation"]["likely_cause"]
    assert all({"failed_checks", "evidence", "likely_cause", "proposed_change"} <= d.keys()
               for d in diagnoses.values())


def test_live_runner_captures_outputs_and_tool_calls(monkeypatch):
    case = CASES["autonomous_loan_denial"]
    risk = RiskAssessmentResult(risk_level=RiskLevel.HIGH, risk_score=70,
                                risk_factors=["credit decisions", "no human review", "no bias testing"],
                                rationale="Fully autonomous loan decisions with no human oversight or bias testing.")
    compliance = PolicyComplianceResult(status=ComplianceStatus.NON_COMPLIANT,
                                        violated_policies=["POL-003", "POL-006"], rationale="missing controls")
    decision = DecisionResult(decision=Decision.BLOCK, conditions=["add human review"], rationale="blocked")

    def fake(result, tools):
        def _call(self, *args):
            self.last_tool_calls = [{"tool": t, "arguments": {}, "ok": True} for t in tools]
            self.last_total_tokens = 100
            return result
        return _call

    monkeypatch.setattr("app.agents.risk_agent.RiskAssessmentAgent.assess", fake(risk, ["get_risk_rules"]))
    monkeypatch.setattr("app.agents.policy_agent.PolicyComplianceAgent.check", fake(compliance, ["get_policies"]))
    monkeypatch.setattr("app.agents.decision_agent.DecisionAgent.decide", fake(decision, []))

    trace = run_live(case, run_id=1)
    assert trace["error"] is None
    assert trace["tool_calls"] == {
        "risk_assessment_agent": ["get_risk_rules"],
        "policy_compliance_agent": ["get_policies"],
    }
    assert trace["total_tokens"] == 300
    result = evaluate_run(case, trace)
    assert result["passed"], result["failed_checks"]


def test_cli_replay_writes_results(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    out = tmp_path / "results.json"
    assert evals_main(["--mode", "replay", "--repeats", "1", "--holdout", "--output", str(out)]) == 0
    payload = json.loads(out.read_text())
    assert payload["mode"] == "replay"
    assert payload["holdout_summary"]["runs"] == len(HOLDOUT_CASES)
    assert "Release decision: BLOCK" in capsys.readouterr().out
