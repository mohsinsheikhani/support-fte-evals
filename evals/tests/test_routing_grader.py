"""
Test script for routing_grader.

Run with: python -m pytest evals/test_routing_grader.py -v
Or manually: python evals/test_routing_grader.py
"""

from graders.routing import grade_routing


def test_case_1_faq_routing():
    """Test Case 1: FAQ routing for refund policy question."""
    result = {"agent": "FAQAgent", "response": "Our refund policy allows..."}
    expected = {"agent": "FAQAgent", "should_succeed": True}

    grade_result = grade_routing(result, expected)

    assert grade_result["passed"] == True
    assert grade_result["score"] == 1.0
    assert grade_result["failed_checks"] == []
    print("✓ Test Case 1: FAQ routing - PASSED")


def test_case_2_escalation_routing():
    """Test Case 2: Escalation routing for security question."""
    result = {"agent": "EscalationAgent", "response": "Your data security..."}
    expected = {"agent": "EscalationAgent", "should_succeed": True}

    grade_result = grade_routing(result, expected)

    assert grade_result["passed"] == True
    assert grade_result["score"] == 1.0
    print("✓ Test Case 2: Escalation routing - PASSED")


def test_case_5_billing_routing():
    """Test Case 5: Billing routing for double charge."""
    result = {"agent": "BillingAgent", "response": "I see you were charged twice..."}
    expected = {"agent": "BillingAgent", "should_succeed": True}

    grade_result = grade_routing(result, expected)

    assert grade_result["passed"] == True
    assert grade_result["score"] == 1.0
    print("✓ Test Case 5: Billing routing - PASSED")


def test_case_6_technical_routing():
    """Test Case 6: Technical routing for API error."""
    result = {"agent": "TechnicalAgent", "response": "The 500 error indicates..."}
    expected = {"agent": "TechnicalAgent", "should_succeed": True}

    grade_result = grade_routing(result, expected)

    assert grade_result["passed"] == True
    assert grade_result["score"] == 1.0
    print("✓ Test Case 6: Technical routing - PASSED")


def test_incorrect_routing():
    """Test incorrect routing scenario."""
    result = {"agent": "BillingAgent", "response": "Our refund policy..."}
    expected = {"agent": "FAQAgent", "should_succeed": True}

    grade_result = grade_routing(result, expected)

    assert grade_result["passed"] == False
    assert grade_result["score"] < 1.0
    assert "correct_agent" in grade_result["failed_checks"]
    print("✓ Test: Incorrect routing detection - PASSED")


def test_missing_agent():
    """Test missing agent in result."""
    result = {"response": "Some response"}
    expected = {"agent": "FAQAgent", "should_succeed": True}

    grade_result = grade_routing(result, expected)

    assert grade_result["passed"] == False
    assert "agent_present" in grade_result["failed_checks"]
    print("✓ Test: Missing agent detection - PASSED")


def test_unrecognized_agent():
    """Test unrecognized agent name."""
    result = {"agent": "UnknownAgent", "response": "Some response"}
    expected = {"agent": "FAQAgent", "should_succeed": True}

    grade_result = grade_routing(result, expected)

    assert grade_result["passed"] == False
    assert "agent_recognized" in grade_result["failed_checks"]
    print("✓ Test: Unrecognized agent detection - PASSED")


def run_all_tests():
    """Run all tests manually."""
    print("\n" + "="*60)
    print("Running Routing Grader Tests")
    print("="*60 + "\n")

    try:
        test_case_1_faq_routing()
        test_case_2_escalation_routing()
        test_case_5_billing_routing()
        test_case_6_technical_routing()
        test_incorrect_routing()
        test_missing_agent()
        test_unrecognized_agent()

        print("\n" + "="*60)
        print("All tests passed! ✓")
        print("="*60 + "\n")

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}\n")
        raise


if __name__ == "__main__":
    run_all_tests()
