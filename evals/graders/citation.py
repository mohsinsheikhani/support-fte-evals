"""
Citation Grader (Q1 - Code-Based)

Verifies that the agent:
1. Uses knowledge from its static FAQ_KNOWLEDGE base
2. Provides accurate information (no hallucination)
3. References the expected knowledge domain

NOTE: This is for STATIC knowledge (FAQ_KNOWLEDGE string), not real RAG/vector stores.

Test Cases: 4 (pricing question)
"""

from typing import Dict, Any


# Expected content from FAQ_KNOWLEDGE for pricing
PRICING_KEYWORDS = {
    "plans": ["free", "premium", "enterprise"],
    "free_plan": ["100", "api calls", "month", "basic support"],
    "premium_plan": ["99", "10,000", "10000", "priority support", "analytics"],
    "enterprise_plan": ["unlimited", "custom", "dedicated support", "sla"],
}

# Hallucination detection - prices NOT in FAQ_KNOWLEDGE
INVALID_PRICES = ["49", "149", "199", "299", "399", "499"]  # Common wrong prices


def _check_pricing_content(response: str) -> Dict[str, bool]:
    """
    Check if response contains expected pricing information.

    Args:
        response: Agent's response text

    Returns:
        Dict of content checks
    """
    response_lower = response.lower()

    checks = {
        "mentions_plans": any(plan in response_lower for plan in PRICING_KEYWORDS["plans"]),
        "free_plan_details": any(keyword in response_lower for keyword in PRICING_KEYWORDS["free_plan"]),
        "premium_plan_details": any(keyword in response_lower for keyword in PRICING_KEYWORDS["premium_plan"]),
        "enterprise_plan_details": any(keyword in response_lower for keyword in PRICING_KEYWORDS["enterprise_plan"]),
    }

    return checks


def _check_no_hallucination(response: str) -> Dict[str, bool]:
    """
    Check that response doesn't contain hallucinated pricing.

    Args:
        response: Agent's response text

    Returns:
        Dict of hallucination checks
    """
    response_lower = response.lower()

    # Check for invalid prices (common hallucinations)
    has_invalid_price = any(f"${price}" in response_lower or f"${price}/" in response_lower
                            for price in INVALID_PRICES)

    checks = {
        "no_invalid_prices": not has_invalid_price,
        "no_made_up_features": True,  # TODO: Could add feature hallucination detection
    }

    return checks


def grade_citation(result: Dict[str, Any], expected: Dict[str, Any]) -> Dict[str, Any]:
    """
    Grade whether the agent cited knowledge correctly (static FAQ_KNOWLEDGE).

    This is a Q1 grader for STATIC knowledge, not real RAG. It checks:
    1. Response contains information from the expected knowledge domain
    2. Information is accurate (matches FAQ_KNOWLEDGE)
    3. No hallucinated prices or features

    Args:
        result: Agent execution result from handle_message():
            - response: The agent's response text
            - agent_used: Which agent responded
        expected: Expected values from dataset:
            - citation_required: Knowledge domain (e.g., "pricing-guide.md")
            - quality_criteria: List of expected content points

    Returns:
        {
            "passed": bool,
            "score": float (0.0-1.0),
            "checks": dict of individual check results,
            "failed_checks": list of failed check names,
            "details": additional debugging info
        }
    """
    # Extract actual values
    response = result.get("response", "")
    agent_used = result.get("agent_used", "")

    # Extract expected values
    citation_required = expected.get("citation_required", "")

    # Determine knowledge domain from citation_required
    knowledge_domain = "pricing" if "pricing" in citation_required.lower() else "unknown"

    # Perform content checks based on knowledge domain
    if knowledge_domain == "pricing":
        content_checks = _check_pricing_content(response)
        hallucination_checks = _check_no_hallucination(response)
    else:
        # For other domains, basic checks
        content_checks = {"has_content": len(response) > 0}
        hallucination_checks = {"no_hallucination": True}

    # Combine all checks
    checks = {
        "correct_agent": agent_used == "FAQAgent",  # Should be FAQ agent
        "has_knowledge_content": any(content_checks.values()),  # At least some correct content
        "multiple_plan_details": sum(content_checks.values()) >= 2,  # Multiple pieces of info
        "no_hallucination": all(hallucination_checks.values()),  # No made-up content
    }

    # Calculate score
    score = sum(checks.values()) / len(checks)

    # Overall pass: all critical checks must pass
    critical_checks = ["correct_agent", "has_knowledge_content", "no_hallucination"]
    passed = all(checks[check] for check in critical_checks)

    # Identify failed checks
    failed_checks = [check_name for check_name, check_result in checks.items() if not check_result]

    return {
        "passed": passed,
        "score": score,
        "checks": checks,
        "failed_checks": failed_checks,
        "details": {
            "citation_required": citation_required,
            "knowledge_domain": knowledge_domain,
            "agent_used": agent_used,
            "content_checks": content_checks,
            "hallucination_checks": hallucination_checks,
            "response_length": len(response),
            "response_preview": response[:150] if response else None,
        }
    }
