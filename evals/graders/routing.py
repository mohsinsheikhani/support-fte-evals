"""Q1 Grader: Routing correctness (Objective + Ground Truth).

Verifies that the agent correctly routed user queries to the appropriate specialist.

Covers test cases: 1, 2, 4, 5, 6, 8, 9 (7 cases total)

Expected routing rules:
- FAQAgent: Policy questions, general information
- BillingAgent: Billing, charges, refunds
- TechnicalAgent: API errors, technical issues
- EscalationAgent: Security concerns, complex issues
"""

from typing import Dict, Any


# Supported agent names for validation
VALID_AGENT_NAMES = {
    "FAQAgent",
    "BillingAgent",
    "TechnicalAgent",
    "EscalationAgent"
}


def grade_routing(result: dict, expected: dict) -> dict:
    """
    Check if the agent routed to the correct specialist.

    Args:
        result: Output from handle_message() containing:
            - agent: str - Name of the agent that handled the request
            - response: str (optional) - Agent's response
        expected: Expected values from test case containing:
            - agent: str - Expected agent name (e.g., "FAQAgent", "BillingAgent")
            - should_succeed: bool (optional) - Whether routing should succeed

    Returns:
        dict: Standardized grader result with:
            - passed: bool - Whether the grading passed
            - score: float - Score between 0.0 and 1.0
            - checks: dict - Individual check results
            - failed_checks: list - Names of failed checks
            - details: dict - Additional context for debugging

    Examples:
        >>> result = {"agent": "FAQAgent", "response": "Our refund policy..."}
        >>> expected = {"agent": "FAQAgent", "should_succeed": True}
        >>> grade_result = grade_routing(result, expected)
        >>> grade_result["passed"]
        True
        >>> grade_result["score"]
        1.0

        >>> result = {"agent": "BillingAgent", "response": "..."}
        >>> expected = {"agent": "FAQAgent", "should_succeed": True}
        >>> grade_result = grade_routing(result, expected)
        >>> grade_result["passed"]
        False
        >>> grade_result["failed_checks"]
        ['correct_agent']
    """
    # Extract actual and expected agents
    # Note: handle_message() returns "agent_used" field
    actual_agent = result.get("agent_used", None) or result.get("agent", None)
    expected_agent = expected.get("agent")
    should_succeed = expected.get("should_succeed", True)

    # Define checks
    checks = {
        "agent_present": actual_agent is not None,
        "correct_agent": actual_agent == expected_agent
    }

    # Additional check: validate agent is recognized
    if actual_agent and actual_agent not in VALID_AGENT_NAMES:
        checks["agent_recognized"] = False
    else:
        checks["agent_recognized"] = True if actual_agent else False

    # If routing should fail (edge case), invert the logic
    if not should_succeed:
        checks["routing_failed_as_expected"] = actual_agent is None or actual_agent != expected_agent

    # Calculate score
    score = sum(checks.values()) / len(checks)

    # Determine pass/fail - routing must be exact match
    passed = checks["correct_agent"] and checks["agent_present"] and checks["agent_recognized"]

    # Identify failed checks
    failed_checks = [check_name for check_name, check_passed in checks.items() if not check_passed]

    # Build result
    result_dict = {
        "passed": passed,
        "score": score,
        "checks": checks,
        "failed_checks": failed_checks,
        "details": {
            "expected_agent": expected_agent,
            "actual_agent": actual_agent,
            "should_succeed": should_succeed
        }
    }

    return result_dict
