"""
Integration test for citation_grader.

Tests that the agent uses static FAQ_KNOWLEDGE correctly.

ITERATION 0: Initial test with real agent

Run with: uv run python evals/test_citation_integration.py
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
from evals.graders.citation import grade_citation


async def test_citation_grader():
    """Test citation_grader with real agent execution."""

    # Load dataset
    dataset_path = Path(__file__).parent / "dataset.json"
    with open(dataset_path) as f:
        dataset = json.load(f)

    # Filter for citation test cases (case 4)
    test_cases = [
        case for case in dataset["cases"]
        if "citation" in case.get("graders", [])
    ]

    print(f"\n{'='*60}")
    print(f"CITATION GRADER - ITERATION 0 TEST")
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
        print(f"Expected citation: {case['expected']['citation_required']}")
        print(f"Expected agent: {case['expected'].get('agent', 'N/A')}")

        # Call the REAL agent with unique session
        agent_result = await handle_message(
            message=case["input"],
            session_id=f"test-citation-{case['id']}-{uuid4().hex[:8]}",
            context=None,
            capture_tools=True,
        )

        print(f"\nAgent response received:")
        print(f"  Agent used: {agent_result.get('agent_used')}")
        print(f"  Response preview: {agent_result.get('response', '')[:200]}...")

        # Grade the result
        grade_result = grade_citation(agent_result, case["expected"])

        print(f"\nGrade result:")
        print(f"  Passed: {grade_result['passed']}")
        print(f"  Score: {grade_result['score']:.2f}")
        print(f"  Checks: {grade_result['checks']}")
        if grade_result['failed_checks']:
            print(f"  Failed checks: {grade_result['failed_checks']}")
        print(f"  Knowledge domain: {grade_result['details']['knowledge_domain']}")
        print(f"  Content checks: {grade_result['details']['content_checks']}")
        print(f"  Hallucination checks: {grade_result['details']['hallucination_checks']}")

        results.append({
            "case_id": case["id"],
            "input": case["input"],
            "expected": case["expected"],
            "actual": {
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
            print(f"  Expected citation: {failure['expected']['citation_required']}")
            print(f"  Actual agent: {failure['actual']['agent_used']}")
            print(f"  Failed checks: {failure['grade']['failed_checks']}")
            print(f"  Response preview: {failure['actual']['response'][:150]}...")

    print(f"\n{'='*60}\n")

    return {
        "total": len(test_cases),
        "passed": passed_count,
        "failed": len(test_cases) - passed_count,
        "pass_rate": passed_count / len(test_cases),
        "results": results,
    }


if __name__ == "__main__":
    result = asyncio.run(test_citation_grader())
