"""
Comprehensive Q1 Baseline Evaluation

Runs all Q1 code-based graders across all test cases and generates
a complete baseline report.

Q1 Graders (6 total):
- routing_grader (7 cases)
- input_guardrail_grader (2 cases)
- tool_usage_grader (2 cases)
- citation_grader (1 case)
- output_guardrail_grader (1 case)
- routing_flexible_grader (1 case)

Total: 14 test cases (12 unique + 2 shared with routing)

Run with: uv run evals/run_q1_baseline.py
"""

import asyncio
import sys
import os
import json
from pathlib import Path
from uuid import uuid4
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import handle_message
from evals.graders.routing import grade_routing
from evals.graders.guardrails import grade_guardrail
from evals.graders.tools import grade_tool_usage
from evals.graders.citation import grade_citation
from evals.graders.output_guardrail import grade_output_guardrail
from evals.graders.routing_flexible import grade_routing_flexible
from src.tools.billing import PROCESSED_REFUNDS


# Grader mapping
GRADER_FUNCTIONS = {
    "routing": grade_routing,
    "input_guardrail": grade_guardrail,
    "tool_usage": grade_tool_usage,
    "citation": grade_citation,
    "output_guardrail": grade_output_guardrail,
    "routing_flexible": grade_routing_flexible,
}


async def run_single_case(case: Dict[str, Any], grader_name: str) -> Dict[str, Any]:
    """
    Run a single test case with the specified grader.

    Args:
        case: Test case from dataset
        grader_name: Name of grader to use

    Returns:
        Result dict with case info and grade
    """
    # Clear global state before each test case to prevent contamination
    PROCESSED_REFUNDS.clear()

    # Determine if we need tool capture
    capture_tools = grader_name in ["tool_usage"]

    # Call the agent
    try:
        agent_result = await handle_message(
            message=case["input"],
            session_id=f"baseline-{case['id']}-{uuid4().hex[:8]}",
            context=None,
            capture_tools=capture_tools,
        )
    except Exception as e:
        return {
            "case_id": case["id"],
            "grader": grader_name,
            "error": str(e),
            "passed": False,
            "score": 0.0,
        }

    # Get grader function
    grader_fn = GRADER_FUNCTIONS[grader_name]

    # Grade the result
    try:
        grade_result = grader_fn(agent_result, case["expected"])
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


async def run_q1_baseline():
    """
    Run complete Q1 baseline evaluation across all graders and test cases.
    """
    start_time = datetime.now()

    # Clear global state
    PROCESSED_REFUNDS.clear()

    # Load dataset
    dataset_path = Path(__file__).parent / "dataset.json"
    with open(dataset_path) as f:
        dataset = json.load(f)

    print(f"\n{'='*70}")
    print(f"Q1 BASELINE EVALUATION - ALL GRADERS")
    print(f"{'='*70}\n")
    print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Q1 graders: {len(GRADER_FUNCTIONS)}\n")

    # Collect all Q1 test cases organized by grader
    grader_cases = {grader: [] for grader in GRADER_FUNCTIONS.keys()}

    for case in dataset["cases"]:
        for grader in case.get("graders", []):
            if grader in GRADER_FUNCTIONS:
                grader_cases[grader].append(case)

    # Calculate total test cases
    total_cases = sum(len(cases) for cases in grader_cases.values())

    print(f"Test case distribution:")
    for grader, cases in grader_cases.items():
        print(f"  {grader}: {len(cases)} cases")
    print(f"\nTotal test cases: {total_cases}\n")

    # Run all graders
    all_results = []
    grader_summaries = {}

    for grader_name, cases in grader_cases.items():
        if not cases:
            continue

        print(f"\n{'─'*70}")
        print(f"Running: {grader_name}")
        print(f"{'─'*70}")

        grader_results = []
        passed = 0

        for case in cases:
            result = await run_single_case(case, grader_name)
            grader_results.append(result)
            all_results.append(result)

            if result["passed"]:
                passed += 1

            # Print progress
            status = "✓ PASS" if result["passed"] else "✗ FAIL"
            print(f"  Case {result['case_id']}: {status} ({result['score']:.2f})")

        # Grader summary
        pass_rate = passed / len(cases) if cases else 0
        grader_summaries[grader_name] = {
            "total": len(cases),
            "passed": passed,
            "failed": len(cases) - passed,
            "pass_rate": pass_rate,
        }

        print(f"\n  {grader_name} summary: {passed}/{len(cases)} passed ({pass_rate*100:.1f}%)")

    # Overall summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    total_passed = sum(r["passed"] for r in all_results)
    overall_pass_rate = total_passed / total_cases if total_cases > 0 else 0

    print(f"\n{'='*70}")
    print(f"OVERALL SUMMARY")
    print(f"{'='*70}\n")
    print(f"Total test cases: {total_cases}")
    print(f"Total passed: {total_passed}")
    print(f"Total failed: {total_cases - total_passed}")
    print(f"Overall pass rate: {overall_pass_rate*100:.1f}%")
    print(f"Duration: {duration:.2f}s")
    print(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Breakdown by grader
    print(f"{'─'*70}")
    print(f"BREAKDOWN BY GRADER")
    print(f"{'─'*70}\n")

    for grader_name, summary in grader_summaries.items():
        status = "✓" if summary["pass_rate"] == 1.0 else "✗"
        print(f"{status} {grader_name:25s} {summary['passed']:2d}/{summary['total']:2d}  ({summary['pass_rate']*100:5.1f}%)")

    # Show failures if any
    failures = [r for r in all_results if not r["passed"]]
    if failures:
        print(f"\n{'─'*70}")
        print(f"FAILURES ({len(failures)} total)")
        print(f"{'─'*70}\n")

        for failure in failures:
            print(f"Case {failure['case_id']} ({failure['grader']}):")
            print(f"  Input: {failure['input']}...")
            print(f"  Agent: {failure.get('agent_used', 'N/A')}")
            if failure.get('error'):
                print(f"  Error: {failure['error']}")
            else:
                print(f"  Failed checks: {failure['failed_checks']}")
            print()

    print(f"{'='*70}\n")

    # Save results to JSON
    results_file = Path(__file__).parent / "q1_baseline_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": start_time.isoformat(),
            "duration_seconds": duration,
            "total_cases": total_cases,
            "total_passed": total_passed,
            "total_failed": total_cases - total_passed,
            "overall_pass_rate": overall_pass_rate,
            "grader_summaries": grader_summaries,
            "all_results": all_results,
        }, f, indent=2)

    print(f"Results saved to: {results_file}")
    print(f"Overall pass rate: {overall_pass_rate*100:.1f}%\n")

    return {
        "pass_rate": overall_pass_rate,
        "total_passed": total_passed,
        "total_cases": total_cases,
        "grader_summaries": grader_summaries,
        "failures": failures,
    }


if __name__ == "__main__":
    result = asyncio.run(run_q1_baseline())

    # Exit with non-zero if not 100%
    if result["pass_rate"] < 1.0:
        print(f"⚠️  Baseline incomplete: {result['pass_rate']*100:.1f}% pass rate")
        sys.exit(1)
    else:
        print(f"✓ Baseline complete: 100% pass rate")
        sys.exit(0)
