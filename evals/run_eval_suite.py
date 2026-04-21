"""Unified Eval Suite Runner (Q1 + Q2).

Runs all Q1 code-based graders (6 graders, 14 cases) plus Q2 response
quality grader (3 cases) and checks for regressions against baseline.

Usage:
    uv run evals/run_eval_suite.py              # Run suite, compare against baseline
    uv run evals/run_eval_suite.py --save-baseline   # Save current run as new baseline
    uv run evals/run_eval_suite.py --threshold 0.10  # Override 5% default threshold
"""

import argparse
import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from src.main import handle_message
from src.tools.billing import PROCESSED_REFUNDS

# Q1 graders (sync)
from evals.graders.routing import grade_routing
from evals.graders.guardrails import grade_guardrail
from evals.graders.tools import grade_tool_usage
from evals.graders.citation import grade_citation
from evals.graders.output_guardrail import grade_output_guardrail
from evals.graders.routing_flexible import grade_routing_flexible

# Q2 graders (async)
from evals.graders.quality import grade_response_quality

# Regression detection
from evals.regression import (
    RegressionConfig,
    compare_versions,
    check_regression,
    identify_improvement_target,
    load_baseline,
    print_regression_report,
    results_to_eval_run,
)


# Q1 graders (all sync)
Q1_GRADERS = {
    "routing": grade_routing,
    "input_guardrail": grade_guardrail,
    "tool_usage": grade_tool_usage,
    "citation": grade_citation,
    "output_guardrail": grade_output_guardrail,
    "routing_flexible": grade_routing_flexible,
}

# Q2 graders (all async)
Q2_GRADERS = {
    "response_quality": grade_response_quality,
}

RESULTS_DIR = Path(__file__).parent / "results"
BASELINE_PATH = RESULTS_DIR / "q1_baseline_results.json"
LATEST_PATH = RESULTS_DIR / "latest_results.json"


async def run_single_case(
    case: dict[str, Any], grader_name: str
) -> dict[str, Any]:
    """Run a single test case with the specified grader.

    Handles both Q1 (sync) and Q2 (async) graders.
    """
    # Clear global state before each test case
    PROCESSED_REFUNDS.clear()

    # Determine if we need tool capture
    capture_tools = grader_name in ["tool_usage"]

    # Call the agent
    try:
        agent_result = await handle_message(
            message=case["input"],
            session_id=f"eval-{case['id']}-{grader_name}-{uuid4().hex[:8]}",
            context=None,
            capture_tools=capture_tools,
        )
        # Add input to result for quality grader
        agent_result["input"] = case["input"]
    except Exception as e:
        return {
            "case_id": case["id"],
            "grader": grader_name,
            "error": str(e),
            "passed": False,
            "score": 0.0,
        }

    # Grade the result
    try:
        if grader_name in Q2_GRADERS:
            # Q2 graders are async
            grade_result = await Q2_GRADERS[grader_name](agent_result, case["expected"])
        else:
            # Q1 graders are sync
            grade_result = Q1_GRADERS[grader_name](agent_result, case["expected"])
    except Exception as e:
        return {
            "case_id": case["id"],
            "grader": grader_name,
            "error": f"Grader error: {str(e)}",
            "passed": False,
            "score": 0.0,
        }

    return {
        "case_id": case["id"],
        "grader": grader_name,
        "input": case["input"][:100],
        "agent_used": agent_result.get("agent_used"),
        "passed": grade_result["passed"],
        "score": grade_result["score"],
        "checks": grade_result.get("checks", {}),
        "failed_checks": grade_result.get("failed_checks", []),
        "error": None,
    }


async def run_eval_suite(threshold: float | None = None) -> dict[str, Any]:
    """Run complete evaluation suite (Q1 + Q2) across all graders."""
    start_time = datetime.now()
    PROCESSED_REFUNDS.clear()

    # Load dataset
    dataset_path = Path(__file__).parent / "dataset.json"
    with open(dataset_path) as f:
        dataset = json.load(f)

    all_graders = {**Q1_GRADERS, **Q2_GRADERS}

    print(f"\n{'='*70}")
    print(f"EVAL SUITE — Q1 + Q2 (ALL GRADERS)")
    print(f"{'='*70}\n")
    print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Q1 graders: {len(Q1_GRADERS)}  |  Q2 graders: {len(Q2_GRADERS)}")
    print(f"Total graders: {len(all_graders)}\n")

    # Collect test cases organized by grader
    grader_cases: dict[str, list] = {g: [] for g in all_graders}

    for case in dataset["cases"]:
        for grader in case.get("graders", []):
            if grader in all_graders:
                grader_cases[grader].append(case)

    # Calculate total test cases
    total_cases = sum(len(cases) for cases in grader_cases.values())

    print(f"Test case distribution:")
    for grader, cases in grader_cases.items():
        quadrant = "Q2" if grader in Q2_GRADERS else "Q1"
        print(f"  [{quadrant}] {grader}: {len(cases)} cases")
    print(f"\nTotal test cases: {total_cases}\n")

    # Run all graders
    all_results = []
    grader_summaries = {}

    for grader_name, cases in grader_cases.items():
        if not cases:
            continue

        quadrant = "Q2" if grader_name in Q2_GRADERS else "Q1"
        print(f"\n{'─'*70}")
        print(f"[{quadrant}] Running: {grader_name}")
        print(f"{'─'*70}")

        passed = 0

        for case in cases:
            result = await run_single_case(case, grader_name)
            all_results.append(result)

            if result["passed"]:
                passed += 1

            status = "PASS" if result["passed"] else "FAIL"
            print(f"  Case {result['case_id']}: {status} ({result['score']:.2f})")

        pass_rate = passed / len(cases) if cases else 0
        grader_summaries[grader_name] = {
            "total": len(cases),
            "passed": passed,
            "failed": len(cases) - passed,
            "pass_rate": pass_rate,
        }

        print(f"\n  {grader_name}: {passed}/{len(cases)} ({pass_rate*100:.1f}%)")

    # Overall summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    total_passed = sum(1 for r in all_results if r["passed"])
    overall_pass_rate = total_passed / total_cases if total_cases > 0 else 0

    print(f"\n{'='*70}")
    print(f"OVERALL SUMMARY")
    print(f"{'='*70}\n")
    print(f"Total test cases: {total_cases}")
    print(f"Total passed: {total_passed}")
    print(f"Total failed: {total_cases - total_passed}")
    print(f"Overall pass rate: {overall_pass_rate*100:.1f}%")
    print(f"Duration: {duration:.1f}s\n")

    # Breakdown by grader
    print(f"{'─'*70}")
    print(f"BREAKDOWN BY GRADER")
    print(f"{'─'*70}\n")

    for grader_name, summary in grader_summaries.items():
        quadrant = "Q2" if grader_name in Q2_GRADERS else "Q1"
        status = "+" if summary["pass_rate"] == 1.0 else "!"
        print(
            f"[{status}] [{quadrant}] {grader_name:25s} "
            f"{summary['passed']:2d}/{summary['total']:2d}  "
            f"({summary['pass_rate']*100:5.1f}%)"
        )

    # Show failures
    failures = [r for r in all_results if not r["passed"]]
    if failures:
        print(f"\n{'─'*70}")
        print(f"FAILURES ({len(failures)})")
        print(f"{'─'*70}\n")
        for failure in failures:
            print(f"Case {failure['case_id']} ({failure['grader']}):")
            print(f"  Input: {failure.get('input', 'N/A')}...")
            print(f"  Agent: {failure.get('agent_used', 'N/A')}")
            if failure.get("error"):
                print(f"  Error: {failure['error']}")
            else:
                print(f"  Failed checks: {failure.get('failed_checks', [])}")
            print()

    # Improvement target
    eval_run = results_to_eval_run({
        "total_cases": total_cases,
        "total_passed": total_passed,
        "overall_pass_rate": overall_pass_rate,
        "grader_summaries": grader_summaries,
    })
    target = identify_improvement_target(eval_run)
    if target and eval_run.by_criterion.get(target, 1.0) < 1.0:
        print(f"Improvement target: {target} ({eval_run.by_criterion[target]*100:.1f}%)")

    # Build results dict (same format as q1_baseline_results.json)
    results_data = {
        "timestamp": start_time.isoformat(),
        "duration_seconds": duration,
        "total_cases": total_cases,
        "total_passed": total_passed,
        "total_failed": total_cases - total_passed,
        "overall_pass_rate": overall_pass_rate,
        "grader_summaries": grader_summaries,
        "all_results": all_results,
    }

    # Save to latest_results.json
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(LATEST_PATH, "w") as f:
        json.dump(results_data, f, indent=2)
    print(f"\nResults saved to: {LATEST_PATH}")

    # --- Regression check ---
    if BASELINE_PATH.exists():
        print(f"\nComparing against baseline: {BASELINE_PATH}")
        baseline = load_baseline(str(BASELINE_PATH))
        current = results_to_eval_run(results_data)

        comparison = compare_versions(baseline, current)

        config = RegressionConfig()
        if threshold is not None:
            config.overall_threshold = threshold

        check_result = check_regression(comparison, config)
        print_regression_report(comparison, check_result)

        return {
            "results": results_data,
            "regression": check_result,
        }
    else:
        print(f"\nNo baseline found at {BASELINE_PATH}. Skipping regression check.")
        print("Run with --save-baseline to establish a baseline.\n")
        return {
            "results": results_data,
            "regression": None,
        }


def parse_args():
    parser = argparse.ArgumentParser(description="Run eval suite with regression check")
    parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="Save current run as the new baseline",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Override overall regression threshold (default: 0.05 = 5%%)",
    )
    return parser.parse_args()


async def main():
    args = parse_args()

    outcome = await run_eval_suite(threshold=args.threshold)

    # Save as baseline if requested
    if args.save_baseline:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(BASELINE_PATH, "w") as f:
            json.dump(outcome["results"], f, indent=2)
        print(f"Baseline saved to: {BASELINE_PATH}")

    # Exit code based on regression check
    regression = outcome.get("regression")
    if regression and regression.get("should_block"):
        print("Exiting with code 1 (regression detected).")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
