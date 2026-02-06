"""
Component Eval: Routing Logic (Isolated)

Tests ONLY the routing decision logic without full agent execution.
Uses known-good inputs with expected agent assignments.

Comparison:
- E2E: Run full agent → check which agent responded (slow, noisy)
- Component: Test routing logic directly → check decision (fast, clear)

Benefits:
- Fast iteration (< 1 second per test)
- Clear signal (isolated from execution issues)
- Cheap (no LLM calls if using deterministic router)
- Gold standard inputs with verified expected outputs

Run with: uv run evals/tests/component_routing_test.py
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.triage import triage_agent
from agents import Runner


# Gold standard routing test cases
ROUTING_TEST_CASES = [
    {
        "id": "route_1",
        "input": "What's your refund policy?",
        "expected_agent": "FAQAgent",
        "category": "policy_question",
    },
    {
        "id": "route_2",
        "input": "How secure is the customer data?",
        "expected_agent": "EscalationAgent",
        "category": "security_concern",
    },
    {
        "id": "route_3",
        "input": "I was charged twice this month",
        "expected_agent": "BillingAgent",
        "category": "billing_issue",
    },
    {
        "id": "route_4",
        "input": "I'm getting a 500 error on /api/users",
        "expected_agent": "TechnicalAgent",
        "category": "technical_issue",
    },
    {
        "id": "route_5",
        "input": "Guide me on pricing structure?",
        "expected_agent": "FAQAgent",
        "category": "pricing_question",
    },
    {
        "id": "route_6",
        "input": "What features are included in Premium?",
        "expected_agent": "FAQAgent",
        "category": "features_question",
    },
    {
        "id": "route_7",
        "input": "My API key is not working",
        "expected_agent": "TechnicalAgent",
        "category": "api_technical",
    },
    {
        "id": "route_8",
        "input": "I need to update my payment method",
        "expected_agent": "BillingAgent",
        "category": "account_billing",
    },
]


async def test_routing_component(case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test routing component in isolation.

    This is a COMPONENT eval, not E2E:
    - Only tests routing decision
    - No full specialist execution
    - No tool calling
    - No response generation

    Args:
        case: Test case with input and expected agent

    Returns:
        dict with passed status and details
    """
    # Run ONLY the triage agent to get routing decision
    # NOTE: We stop before full execution - just want routing decision
    result = await Runner.run(
        starting_agent=triage_agent,
        input=case["input"],
        max_turns=1,  # Only one turn - just routing decision
    )

    # Extract which agent was selected
    # In our architecture, triage either responds or hands off
    routed_agent = None

    # Check if triage handed off to a specialist
    if hasattr(result, 'agent') and result.agent:
        routed_agent = result.agent.name
    # Or if it stayed at triage (asking for more info)
    elif "agent_used" in dir(result):
        routed_agent = result.agent_used
    else:
        # Fallback: check handoff in response
        response_text = str(result.final_output) if hasattr(result, 'final_output') else str(result)
        if "FAQAgent" in response_text or "faq" in response_text.lower():
            routed_agent = "FAQAgent"
        elif "BillingAgent" in response_text or "billing" in response_text.lower():
            routed_agent = "BillingAgent"
        elif "TechnicalAgent" in response_text or "technical" in response_text.lower():
            routed_agent = "TechnicalAgent"
        elif "EscalationAgent" in response_text or "escalation" in response_text.lower():
            routed_agent = "EscalationAgent"
        else:
            routed_agent = "TriageAgent"

    # Check if routing is correct
    expected = case["expected_agent"]
    passed = routed_agent == expected

    return {
        "case_id": case["id"],
        "input": case["input"],
        "expected_agent": expected,
        "routed_agent": routed_agent,
        "passed": passed,
        "category": case["category"],
    }


async def run_component_routing_eval():
    """Run all routing component tests."""
    print("\n" + "="*70)
    print("COMPONENT EVAL: Routing Logic (Isolated)")
    print("="*70)
    print("\nTesting routing decisions WITHOUT full agent execution")
    print("Fast iteration: ~1 second per test case\n")

    results = []

    for case in ROUTING_TEST_CASES:
        result = await test_routing_component(case)
        results.append(result)

        status = "✓ PASS" if result["passed"] else "✗ FAIL"
        print(f"{status} {result['case_id']:10} | {result['category']:20} | "
              f"Expected: {result['expected_agent']:15} | "
              f"Got: {result['routed_agent']:15}")

    # Summary
    print("\n" + "="*70)
    passed_count = sum(1 for r in results if r["passed"])
    total_count = len(results)
    pass_rate = (passed_count / total_count * 100) if total_count > 0 else 0

    print(f"Results: {passed_count}/{total_count} passed ({pass_rate:.1f}%)")
    print("="*70)

    # Show failures
    failures = [r for r in results if not r["passed"]]
    if failures:
        print("\nFailed Cases:")
        for f in failures:
            print(f"  - {f['case_id']}: Expected {f['expected_agent']}, "
                  f"got {f['routed_agent']}")
    else:
        print("\n✓ All routing decisions correct!")

    print("\n" + "="*70)
    print("Component Eval Benefits:")
    print("- Fast: No full agent execution")
    print("- Clear: Isolated routing logic only")
    print("- Cheap: Minimal LLM calls")
    print("- Debuggable: Direct routing decision visibility")
    print("="*70 + "\n")

    return results


if __name__ == "__main__":
    asyncio.run(run_component_routing_eval())
