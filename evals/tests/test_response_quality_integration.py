"""
Integration test for response_quality grader.

Tests LLM-as-judge with structured output on Q2 cases.

Run with: uv run evals/tests/test_response_quality_integration.py
"""

import asyncio
import sys
import os
import json
from pathlib import Path
from uuid import uuid4

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.main import handle_message
from evals.graders.quality import grade_response_quality


async def test_case_4_pricing():
    """Test case 4: Pricing explanation quality."""
    print("\n" + "="*70)
    print("TEST CASE 4: Pricing Explanation Quality")
    print("="*70)

    case = {
        "id": 4,
        "input": "Guide me on pricing structure?",
        "expected": {
            "agent": "FAQAgent",
            "should_succeed": True,
            "quality_criteria": [
                "Does the response explain pricing tiers clearly?",
                "Does the response mention key features per tier?",
                "Is the response free from hallucinated pricing not in the knowledge base?",
            ]
        }
    }

    print(f"\nInput: {case['input']}")
    print(f"Quality Criteria: {len(case['expected']['quality_criteria'])} criteria")

    # Run agent
    result = await handle_message(
        message=case["input"],
        session_id=f"test-quality-{case['id']}-{uuid4().hex[:8]}",
        context=None,
        capture_tools=False,
    )

    print(f"\nAgent: {result.get('agent_used')}")
    print(f"Response (first 200 chars): {result.get('response', '')[:200]}...")

    # Grade quality
    print("\n--- Running LLM Judge ---")
    grade_result = await grade_response_quality(result, case["expected"])

    print(f"\nPassed: {grade_result['passed']}")
    print(f"Score: {grade_result['score']:.2f}")
    print(f"Checks: {grade_result['checks']}")
    if grade_result['failed_checks']:
        print(f"Failed checks: {grade_result['failed_checks']}")

    if "error" in grade_result:
        print(f"Error: {grade_result['error']}")

    return grade_result


async def test_case_9_escalation():
    """Test case 9: Escalation explanation quality."""
    print("\n" + "="*70)
    print("TEST CASE 9: Escalation Explanation Quality")
    print("="*70)

    case = {
        "id": 9,
        "input": "I'm alice@example.com, please refund my $150 order ORD-1002",
        "expected": {
            "agent": "BillingAgent",
            "tool_called": "process_refund",
            "tool_result": "escalation_needed",
            "should_succeed": True,
            "quality_criteria": [
                "Does the response explain that the refund requires escalation?",
                "Does the response provide a reason for escalation (amount over threshold)?",
                "Does the response offer to create an escalation ticket?",
            ]
        }
    }

    print(f"\nInput: {case['input']}")
    print(f"Quality Criteria: {len(case['expected']['quality_criteria'])} criteria")

    # Run agent
    result = await handle_message(
        message=case["input"],
        session_id=f"test-quality-{case['id']}-{uuid4().hex[:8]}",
        context=None,
        capture_tools=False,
    )

    print(f"\nAgent: {result.get('agent_used')}")
    print(f"Response (first 200 chars): {result.get('response', '')[:200]}...")

    # Grade quality
    print("\n--- Running LLM Judge ---")
    grade_result = await grade_response_quality(result, case["expected"])

    print(f"\nPassed: {grade_result['passed']}")
    print(f"Score: {grade_result['score']:.2f}")
    print(f"Checks: {grade_result['checks']}")
    if grade_result['failed_checks']:
        print(f"Failed checks: {grade_result['failed_checks']}")

    if "error" in grade_result:
        print(f"Error: {grade_result['error']}")

    return grade_result


async def test_case_11_empathy():
    """Test case 11: Empathy and tone quality."""
    print("\n" + "="*70)
    print("TEST CASE 11: Empathy and Tone Quality")
    print("="*70)

    case = {
        "id": 11,
        "input": "I'm really frustrated, I've been a customer for 5 years and this is the worst experience",
        "expected": {
            "should_succeed": True,
            "quality_criteria": [
                "Does the response acknowledge the customer's frustration?",
                "Does the response recognize their loyalty (5 years)?",
                "Does the response apologize for the negative experience?",
                "Does the response avoid dismissing or minimizing their concerns?",
                "Does the response offer concrete next steps to help?",
            ]
        }
    }

    print(f"\nInput: {case['input']}")
    print(f"Quality Criteria: {len(case['expected']['quality_criteria'])} criteria")

    # Run agent
    result = await handle_message(
        message=case["input"],
        session_id=f"test-quality-{case['id']}-{uuid4().hex[:8]}",
        context=None,
        capture_tools=False,
    )

    print(f"\nAgent: {result.get('agent_used')}")
    print(f"Response (first 200 chars): {result.get('response', '')[:200]}...")

    # Grade quality
    print("\n--- Running LLM Judge ---")
    grade_result = await grade_response_quality(result, case["expected"])

    print(f"\nPassed: {grade_result['passed']}")
    print(f"Score: {grade_result['score']:.2f}")
    print(f"Checks: {grade_result['checks']}")
    if grade_result['failed_checks']:
        print(f"Failed checks: {grade_result['failed_checks']}")

    if "error" in grade_result:
        print(f"Error: {grade_result['error']}")

    return grade_result


async def main():
    """Run all response quality tests."""
    print("\n" + "="*70)
    print("RESPONSE QUALITY GRADER - INTEGRATION TEST")
    print("="*70)

    results = []

    # Test case 4 (pricing)
    try:
        result_4 = await test_case_4_pricing()
        results.append(("Case 4", result_4))
    except Exception as e:
        print(f"\n✗ Case 4 failed with error: {e}")
        results.append(("Case 4", {"passed": False, "error": str(e)}))

    # Test case 9 (escalation)
    try:
        result_9 = await test_case_9_escalation()
        results.append(("Case 9", result_9))
    except Exception as e:
        print(f"\n✗ Case 9 failed with error: {e}")
        results.append(("Case 9", {"passed": False, "error": str(e)}))

    # Test case 11 (empathy)
    try:
        result_11 = await test_case_11_empathy()
        results.append(("Case 11", result_11))
    except Exception as e:
        print(f"\n✗ Case 11 failed with error: {e}")
        results.append(("Case 11", {"passed": False, "error": str(e)}))

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    passed_count = sum(1 for _, r in results if r.get("passed", False))
    total_count = len(results)

    for case_name, result in results:
        status = "✓ PASS" if result.get("passed") else "✗ FAIL"
        score = result.get("score", 0.0)
        print(f"{status} {case_name}: {score:.2f}")

    print(f"\nTotal: {passed_count}/{total_count} passed")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
