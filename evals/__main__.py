"""Command-line entry point for the GovernAI evaluation harness.

Examples:
    python -m evals                          # auto: live if OPENAI_API_KEY is set, else replay
    python -m evals --mode replay            # deterministic fixtures, no API key needed
    python -m evals --mode live --repeats 3 --holdout --label prompt-v2
    python -m evals --mode live --compare data/evals/baseline-20260928T101500.json
    python -m evals --cases autonomous_loan_denial,pii_in_documentation --repeats 1
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from app import config
from evals.cases import EVALUATION_CASES, HOLDOUT_CASES, validate_suite
from evals.evaluator import (
    RELEASE_GATE,
    diagnose_failures,
    evaluate_suite,
    failure_matrix,
    format_report,
    release_decision,
    summarize,
)
from evals.runner import LIVE, resolve_mode, run_suite

_COMPARE_METRICS = ("run_pass_rate", "stable_case_rate", "critical_pass_rate", "mean_latency_ms", "mean_tokens")


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


def release_memo(mode: str, suite: dict, holdout: dict = None) -> str:
    decision = "PASS" if (
        mode == LIVE and release_decision(suite) == "PASS" and holdout is not None
        and release_decision(holdout) == "PASS"
    ) else "BLOCK"
    lines = [
        f"Release decision: {decision}",
        "",
        f"Evidence ({mode} mode; replay fixtures are instructional and cannot authorize release):",
        f"- Suite: {suite['run_pass_rate']:.1%} run pass; {suite['stable_case_rate']:.1%} stable cases; "
        f"{suite['critical_pass_rate']:.1%} critical pass.",
    ]
    if holdout is None:
        lines.append("- Holdout: not run (use --holdout); release requires it.")
    else:
        lines.append(f"- Holdout: {holdout['run_pass_rate']:.1%} run pass; "
                     f"{holdout['critical_pass_rate']:.1%} critical pass.")
    lines += [
        f"- Gate: {RELEASE_GATE}",
        "",
        "A pass supports a controlled pilot followed by monitoring of live governance runs; "
        "it does not establish unrestricted production reliability.",
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m evals", description="Evaluate the GovernAI agent pipeline")
    parser.add_argument("--mode", choices=["auto", "live", "replay"], default="auto")
    parser.add_argument("--repeats", type=int, default=3, help="runs per case (consistency check)")
    parser.add_argument("--model", default=None, help="override OPENAI_MODEL for live runs")
    parser.add_argument("--holdout", action="store_true", help="also run the unseen holdout cases")
    parser.add_argument("--cases", default=None, help="comma-separated case ids to run (default: all)")
    parser.add_argument("--label", default="current", help="version label stored with the results")
    parser.add_argument("--output", default=None, help="results JSON path (default: data/evals/<label>-<ts>.json)")
    parser.add_argument("--compare", default=None, help="earlier results JSON to compare against")
    args = parser.parse_args(argv)

    mode = resolve_mode(args.mode)
    cases = EVALUATION_CASES
    if args.cases:
        wanted = {c.strip() for c in args.cases.split(",") if c.strip()}
        unknown = wanted - {c["id"] for c in EVALUATION_CASES}
        if unknown:
            parser.error(f"unknown case ids: {sorted(unknown)}")
        cases = [c for c in EVALUATION_CASES if c["id"] in wanted]
    validate_suite(cases)
    validate_suite(HOLDOUT_CASES)

    if mode != LIVE:
        _log("Replay mode: deterministic fixtures, not model results. Set OPENAI_API_KEY and use "
             "--mode live for release evidence.")
    print(f"Frozen suite: {len(cases)} cases x {args.repeats} runs ({mode})")
    for case in cases:
        print(f"- {case['id']} [{case['difficulty']}]: {case['risk']}{' [CRITICAL]' if case['critical'] else ''}")

    traces = run_suite(cases, mode, repeats=args.repeats, version=args.label, model=args.model, progress=_log)
    results = evaluate_suite(cases, traces)
    suite_summary = summarize(results)
    print()
    print(format_report(f"SUITE ({args.label})", results))

    print("\nFailure matrix:")
    matrix = failure_matrix(results)
    for check, case_ids in matrix.items():
        print(f"  {check} -> {case_ids}")
    if not matrix:
        print("  (no failures)")
    diagnoses = diagnose_failures(results)
    if diagnoses:
        print("\nDiagnosis:")
        print(json.dumps(diagnoses, indent=2))

    holdout_results, holdout_summary = None, None
    if args.holdout:
        holdout_traces = run_suite(HOLDOUT_CASES, mode, repeats=args.repeats, version=args.label,
                                   model=args.model, progress=_log)
        holdout_results = evaluate_suite(HOLDOUT_CASES, holdout_traces)
        holdout_summary = summarize(holdout_results)
        print()
        print(format_report("UNSEEN HOLDOUT", holdout_results))

    if args.compare:
        previous = json.loads(Path(args.compare).read_text(encoding="utf-8"))
        print(f"\nCOMPARISON ({previous.get('label')} -> {args.label})")
        for metric in _COMPARE_METRICS:
            print(f"  {metric}: {previous['summary'][metric]} -> {suite_summary[metric]}")

    print()
    print(release_memo(mode, suite_summary, holdout_summary))

    out = Path(args.output) if args.output else (
        config.DATA_DIR / "evals" / f"{args.label}-{datetime.now(timezone.utc):%Y%m%dT%H%M%S}.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "label": args.label,
        "mode": mode,
        "model": (args.model or config.OPENAI_MODEL) if mode == LIVE else "fixtures",
        "repeats": args.repeats,
        "summary": suite_summary,
        "release_decision": release_decision(suite_summary),
        "results": results,
        "diagnoses": diagnoses,
        "holdout_summary": holdout_summary,
        "holdout_results": holdout_results,
    }, indent=2, default=str), encoding="utf-8")
    _log(f"Results written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
