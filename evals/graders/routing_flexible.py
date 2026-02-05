"""
Routing Flexible Grader (Q3 - Objective + No Ground Truth)

Verifies that the agent routes to ONE of the acceptable agents for ambiguous queries.

Unlike standard routing (Q1) which has ONE correct answer, flexible routing
accepts MULTIPLE valid answers because the query is inherently ambiguous.

Test Cases: 12 (payment failed + can't access account)
"""

from typing import Dict, Any, List


# Valid agent names
VALID_AGENT_NAMES = [
    "TriageAgent",
    "FAQAgent",
    "BillingAgent",
    "TechnicalAgent",
    "EscalationAgent",
]


def grade_routing_flexible(result: Dict[str, Any], expected: Dict[str, Any]) -> Dict[str, Any]:
    """
    Grade whether the agent routed to ONE of the acceptable agents.

    This grader is for ambiguous queries where multiple routes are valid.

    Args:
        result: Agent execution result from handle_message():
            - agent_used: Name of the agent that handled the request
            - (optional) agent: Alternative field name
        expected: Expected values from dataset:
            - agent_options: List of acceptable agent names (any one is valid)
            - should_succeed: Should request succeed?

    Returns:
        {
            "passed": bool,
            "score": float (0.0-1.0),
            "checks": dict of individual check results,
            "failed_checks": list of failed check names,
            "details": additional debugging info
        }
    """
    # Extract actual agent
    actual_agent = result.get("agent_used", None) or result.get("agent", None)

    # Extract expected values
    agent_options = expected.get("agent_options", [])
    should_succeed = expected.get("should_succeed", True)

    # Extract actual success status
    actual_success = result.get("success", True)

    # Perform checks
    checks = {
        "agent_present": actual_agent is not None,
        "agent_recognized": actual_agent in VALID_AGENT_NAMES if actual_agent else False,
        "acceptable_route": actual_agent in agent_options if actual_agent else False,
        "request_succeeded": actual_success == should_succeed,
    }

    # Calculate score
    score = sum(checks.values()) / len(checks)

    # Overall pass: Must route to one of the acceptable agents
    passed = checks["acceptable_route"] and checks["agent_present"] and checks["request_succeeded"]

    # Identify failed checks
    failed_checks = [check_name for check_name, check_result in checks.items() if not check_result]

    return {
        "passed": passed,
        "score": score,
        "checks": checks,
        "failed_checks": failed_checks,
        "details": {
            "expected_options": agent_options,
            "actual_agent": actual_agent,
            "should_succeed": should_succeed,
            "actual_success": actual_success,
            "is_valid_option": actual_agent in agent_options if actual_agent else False,
        }
    }
