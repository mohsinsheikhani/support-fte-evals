"""
Integration test for output_guardrail_grader.

Tests that the output guardrail prevents secrets leakage.

ITERATION 0: Initial test with real agent

Run with: uv run python evals/test_output_guardrail_integration.py
"""

import asyncio
import sys
import os
import json
from pathlib import Path
from uuid import uuid4

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import handle_message
from evals.graders.output_guardrail import grade_output_guardrail


async def test_output_guardrail_grader():
    """Test output_guardrail_grader with real agent execution."""

    # Load dataset
    dataset_path = Path(__file__).parent / "dataset.json"
    with open(dataset_path) as f:
        dataset = json.load(f)

    # Filter for output_guardrail test cases (case 10)
    test_cases = [
        case for case in dataset["cases"]
        if "output_guardrail" in case.get("graders", [])
    ]

    print(f"\n{'='*60}")
    print(f"OUTPUT GUARDRAIL GRADER - ITERATION 0 TEST")
    print(f"{'='*60}\n")
    print(f"Total test cases: {len(test_cases)}")
    print(f"Test case IDs: {[case['id'] for case in test_cases]}\n")

    results = []
    passed_count = 0

    for case in test_cases:
        print(f"\n{'─'*60}")
        print(f"Test Case {case['id']}")
        print(f"{'─'*60}")
        print(f"Input: {case['input']}")
        print(f"Expected guardrail trigger: {case['expected']['output_guardrail_triggered']}")
        print(f"Forbidden patterns: {case['expected']['forbidden_patterns']}")

        # Call the REAL agent with unique session
        agent_result = await handle_message(
            message=case["input"],
            session_id=f"test-output-{case['id']}-{uuid4().hex[:8]}",
            context=None,
            capture_tools=True,
        )

        print(f"\nAgent response received:")
        print(f"  Success: {agent_result.get('success')}")
        print(f"  Agent used: {agent_result.get('agent_used')}")
        print(f"  Response preview: {agent_result.get('response', '')[:200]}...")

        # Grade the result
        grade_result = grade_output_guardrail(agent_result, case["expected"])

        print(f"\nGrade result:")
        print(f"  Passed: {grade_result['passed']}")
        print(f"  Score: {grade_result['score']:.2f}")
        print(f"  Checks: {grade_result['checks']}")
        if grade_result['failed_checks']:
            print(f"  Failed checks: {grade_result['failed_checks']}")
        print(f"  Details:")
        print(f"    - Has forbidden patterns: {grade_result['details']['has_forbidden_patterns']}")
        print(f"    - Detected patterns: {grade_result['details']['detected_patterns']}")
        print(f"    - Is safe response: {grade_result['details']['is_safe_response']}")

        results.append({
            "case_id": case["id"],
            "input": case["input"],
            "expected": case["expected"],
            "actual": {
                "success": agent_result.get("success"),
                "agent_used": agent_result.get("agent_used"),
                "response": agent_result.get("response", "")[:300],
            },
            "grade": grade_result,
        })

        if grade_result["passed"]:
            passed_count += 1

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY - ITERATION 0")
    print(f"{'='*60}")
    print(f"Total cases: {len(test_cases)}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {len(test_cases) - passed_count}")
    print(f"Pass rate: {passed_count / len(test_cases) * 100:.1f}%")

    # Show failures
    failures = [r for r in results if not r["grade"]["passed"]]
    if failures:
        print(f"\n{'─'*60}")
        print("FAILURES:")
        print(f"{'─'*60}")
        for failure in failures:
            print(f"\nCase {failure['case_id']}:")
            print(f"  Input: {failure['input']}")
            print(f"  Expected: Guardrail should trigger")
            print(f"  Actual success: {failure['actual']['success']}")
            print(f"  Failed checks: {failure['grade']['failed_checks']}")
            print(f"  Response: {failure['actual']['response'][:200]}...")

    print(f"\n{'='*60}\n")

    return {
        "total": len(test_cases),
        "passed": passed_count,
        "failed": len(test_cases) - passed_count,
        "pass_rate": passed_count / len(test_cases),
        "results": results,
    }


if __name__ == "__main__":
    result = asyncio.run(test_output_guardrail_grader())
