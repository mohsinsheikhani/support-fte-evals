"""
Tool Usage Grader (Q1 - Code-Based)

Verifies that the agent:
1. Calls the correct tool
2. Tool returns the expected result

Test Cases: 8, 9
"""

from typing import Dict, Any


def _classify_tool_result(tool_output: str, tool_name: str) -> str:
    """
    Classify tool output into expected result categories.

    For process_refund:
    - Contains "approved and processed" → "success"
    - Contains "requires escalation" → "escalation_needed"

    Args:
        tool_output: The string output from the tool
        tool_name: Name of the tool

    Returns:
        Classified result string
    """
    if not tool_output:
        return "no_output"

    output_lower = tool_output.lower()

    if tool_name == "process_refund":
        if "approved and processed" in output_lower:
            return "success"
        elif "requires escalation" in output_lower:
            return "escalation_needed"
        elif "error" in output_lower:
            return "error"

    # Default: return first 50 chars as-is
    return tool_output[:50]


def grade_tool_usage(result: Dict[str, Any], expected: Dict[str, Any]) -> Dict[str, Any]:
    """
    Grade whether the agent used the correct tool and got the expected result.

    ASSUMES: result contains 'tool_called' and 'tool_result' fields
    (This assumption will be tested when we run the integration test)

    Args:
        result: Agent execution result (ASSUMED to have tool data)
        expected: Expected values from dataset

    Returns:
        {
            "passed": bool,
            "score": float (0.0-1.0),
            "checks": dict of individual check results,
            "failed_checks": list of failed check names
        }
    """
    # Extract actual values (assuming they exist)
    actual_tool = result.get("tool_called", None)
    actual_tool_output = result.get("tool_result", "")

    # Extract expected values
    expected_tool = expected.get("tool_called")
    expected_result = expected.get("tool_result")

    # Classify the actual tool output
    classified_result = _classify_tool_result(actual_tool_output, actual_tool or "")

    # Perform checks
    checks = {
        "tool_was_called": actual_tool is not None,
        "correct_tool": actual_tool == expected_tool,
        "correct_result": classified_result == expected_result,
    }

    # Calculate score
    score = sum(checks.values()) / len(checks)

    # Overall pass: all checks must pass
    passed = all(checks.values())

    # Identify failed checks
    failed_checks = [check_name for check_name, check_result in checks.items() if not check_result]

    return {
        "passed": passed,
        "score": score,
        "checks": checks,
        "failed_checks": failed_checks,
        "details": {
            "expected_tool": expected_tool,
            "actual_tool": actual_tool,
            "expected_result": expected_result,
            "classified_result": classified_result,
            "raw_tool_output": actual_tool_output[:200] if actual_tool_output else None,
        }
    }
