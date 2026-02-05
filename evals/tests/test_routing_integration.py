"""
Integration test for routing grader using REAL agent responses.

This test actually calls the agent and evaluates real responses.
"""

import asyncio
import sys
import os
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import handle_message
from graders.routing import grade_routing


async def test_real_agent_routing():
    """Test routing grader with actual agent responses."""

    print("\n" + "="*70)
    print("INTEGRATION TEST: Routing Grader with Real Agent Responses")
    print("="*70 + "\n")

    # Load test cases from dataset
    dataset_path = os.path.join(os.path.dirname(__file__), "dataset.json")
    with open(dataset_path, "r") as f:
        dataset = json.load(f)

    # Test routing cases (cases 1, 2, 4, 5, 6, 8, 9)
    routing_test_ids = [1, 2, 4, 5, 6, 8, 9]

    results = []

    for case in dataset["cases"]:
        if case["id"] not in routing_test_ids:
            continue

        if "routing" not in case.get("graders", []):
            continue

        print(f"Test Case {case['id']}: {case['input'][:60]}...")
        print(f"Expected Agent: {case['expected']['agent']}")

        # Call the REAL agent
        try:
            agent_result = await handle_message(
                message=case["input"],
                session_id=f"test-{case['id']}",
                context=None
            )

            print(f"Actual Agent: {agent_result.get('agent_used', 'NONE')}")

            # Grade the result
            grade_result = grade_routing(agent_result, case["expected"])

            # Display results
            if grade_result["passed"]:
                print(f"✓ PASSED (score: {grade_result['score']:.2f})")
            else:
                print(f"✗ FAILED (score: {grade_result['score']:.2f})")
                print(f"  Failed checks: {grade_result['failed_checks']}")
                print(f"  Details: {grade_result['details']}")

            results.append({
                "case_id": case["id"],
                "passed": grade_result["passed"],
                "score": grade_result["score"],
                "expected": case["expected"]["agent"],
                "actual": agent_result.get("agent_used"),
                "response_preview": agent_result.get("response", "")[:100]
            })

        except Exception as e:
            print(f"✗ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append({
                "case_id": case["id"],
                "passed": False,
                "score": 0.0,
                "error": str(e)
            })

        print()

    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)

    passed_count = sum(1 for r in results if r.get("passed", False))
    total_count = len(results)
    avg_score = sum(r.get("score", 0.0) for r in results) / total_count if total_count > 0 else 0.0

    print(f"\nTests Passed: {passed_count}/{total_count}")
    print(f"Average Score: {avg_score:.2%}")

    if passed_count == total_count:
        print("\n✓ All routing tests PASSED!")
    else:
        print(f"\n✗ {total_count - passed_count} test(s) FAILED")
        print("\nFailed cases:")
        for r in results:
            if not r.get("passed", False):
                print(f"  - Case {r['case_id']}: Expected {r.get('expected')}, Got {r.get('actual')}")

    print("\n" + "="*70 + "\n")

    return results


async def test_single_case(case_id: int):
    """Test a single case by ID."""

    # Load dataset
    dataset_path = os.path.join(os.path.dirname(__file__), "dataset.json")
    with open(dataset_path, "r") as f:
        dataset = json.load(f)

    # Find case
    test_case = None
    for case in dataset["cases"]:
        if case["id"] == case_id:
            test_case = case
            break

    if not test_case:
        print(f"Case {case_id} not found")
        return

    print(f"\nTesting Case {case_id}:")
    print(f"Input: {test_case['input']}")
    print(f"Expected Agent: {test_case['expected']['agent']}\n")

    # Call agent
    result = await handle_message(
        message=test_case["input"],
        session_id=f"test-{case_id}",
        context=None
    )

    print(f"Actual Agent: {result.get('agent_used')}")
    print(f"Response: {result.get('response')}\n")

    # Grade
    grade_result = grade_routing(result, test_case["expected"])

    print(f"Grading Result:")
    print(f"  Passed: {grade_result['passed']}")
    print(f"  Score: {grade_result['score']:.2f}")
    print(f"  Checks: {grade_result['checks']}")
    if grade_result['failed_checks']:
        print(f"  Failed: {grade_result['failed_checks']}")

    return grade_result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test routing grader with real agent")
    parser.add_argument("--case", type=int, help="Test specific case ID")
    args = parser.parse_args()

    if args.case:
        asyncio.run(test_single_case(args.case))
    else:
        asyncio.run(test_real_agent_routing())
