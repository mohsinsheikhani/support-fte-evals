"""
Integration test for tool_usage_grader.

ITERATION 3: After fixing BillingAgent instructions to always call process_refund

Run with: uv run evals/test_tool_usage_integration.py
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
from evals.graders.tools import grade_tool_usage
from src.tools.billing import PROCESSED_REFUNDS


async def test_tool_usage_grader():
    """Test tool_usage_grader with real agent execution."""

    # Clear any previously processed refunds (global state cleanup)
    PROCESSED_REFUNDS.clear()

    # Load dataset
    dataset_path = Path(__file__).parent / "dataset.json"
    with open(dataset_path) as f:
        dataset = json.load(f)

    # Filter for tool_usage test cases (cases 8, 9)
    test_cases = [
        case for case in dataset["cases"]
        if "tool_usage" in case.get("graders", [])
    ]

    print(f"\n{'='*60}")
    print(f"TOOL USAGE GRADER - ITERATION 3 TEST")
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
        print(f"Expected tool: {case['expected']['tool_called']}")
        print(f"Expected result: {case['expected']['tool_result']}")

        # Call the REAL agent with tool capture enabled
        # IMPORTANT: Use unique session ID to avoid session history contamination
        agent_result = await handle_message(
            message=case["input"],
            session_id=f"test-tool-{case['id']}-{uuid4().hex[:8]}",  # Unique per run
            context=None,
            capture_tools=True,  # Enable tool capture via SupportHooks
        )

        print(f"\nAgent response received:")
        print(f"  Keys in result: {list(agent_result.keys())}")
        print(f"  Agent used: {agent_result.get('agent_used')}")
        print(f"  Response text: {agent_result.get('response', '')[:150]}...")

        # Check if tool data exists
        if 'tool_called' not in agent_result:
            print(f"  ⚠️  WARNING: 'tool_called' not in result!")
        if 'tool_result' not in agent_result:
            print(f"  ⚠️  WARNING: 'tool_result' not in result!")

        # Debug: Show what we did get
        if 'tools_used' in agent_result:
            print(f"  ✓ tools_used: {agent_result['tools_used']}")
            if 'tool_called' in agent_result:
                print(f"  ✓ tool_called (last): {agent_result['tool_called']}")
            if 'tool_result' in agent_result:
                print(f"  ✓ tool_result: {agent_result['tool_result'][:100]}...")
        else:
            print(f"  ⚠️  'tools_used' also missing - hooks may not be working")

        # Grade the result (will fail if assumptions are wrong)
        grade_result = grade_tool_usage(agent_result, case["expected"])

        print(f"\nGrade result:")
        print(f"  Passed: {grade_result['passed']}")
        print(f"  Score: {grade_result['score']:.2f}")
        print(f"  Checks: {grade_result['checks']}")
        if grade_result['failed_checks']:
            print(f"  Failed checks: {grade_result['failed_checks']}")

        results.append({
            "case_id": case["id"],
            "grade": grade_result,
        })

        if grade_result["passed"]:
            passed_count += 1

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY - ITERATION 3")
    print(f"{'='*60}")
    print(f"Total cases: {len(test_cases)}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {len(test_cases) - passed_count}")
    print(f"Pass rate: {passed_count / len(test_cases) * 100:.1f}%")
    print(f"\n{'='*60}\n")

    return {
        "total": len(test_cases),
        "passed": passed_count,
        "pass_rate": passed_count / len(test_cases),
        "results": results,
    }


if __name__ == "__main__":
    result = asyncio.run(test_tool_usage_grader())
