"""
Component Eval: LLM Judge (Isolated)

Tests ONLY the LLM judge evaluation logic with known-good inputs.
Uses gold standard agent responses with expert-verified expected judgments.

Comparison:
- E2E: Run full agent → get response → judge evaluates (slow, noisy)
- Component: Provide known response → judge evaluates (fast, clear)

Benefits:
- Fast iteration (5-10 seconds per test)
- Clear signal (isolated from agent execution issues)
- Gold standard inputs (manually verified good/bad responses)
- Rapid prompt tuning (test judge prompts quickly)

Run with: uv run evals/tests/component_llm_judge_test.py
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from evals.graders.quality import grade_response_quality
from src.agents.faq import FAQ_KNOWLEDGE


# Gold standard test cases for LLM judge
# Each case has:
# - Known-good or known-bad agent response
# - Quality criteria to evaluate
# - Expert-verified expected judgments

JUDGE_TEST_CASES = [
    {
        "id": "judge_1",
        "name": "Good pricing explanation",
        "input": "Guide me on pricing structure?",
        "response": """Our pricing structure has three main plans:

1. Free Plan:
   - 100 API calls/month
   - Basic support (48h response)
   - 1 user

2. Premium Plan ($99/month):
   - 10,000 API calls/month
   - Priority support (24h response)
   - 5 users
   - Advanced analytics

3. Enterprise Plan (Custom pricing):
   - Unlimited API calls
   - Dedicated support (4h response)
   - Unlimited users
   - Custom integrations
   - SLA guarantees

Would you like to know more about any specific plan?""",
        "quality_criteria": [
            "Does the response explain pricing tiers clearly?",
            "Does the response mention key features per tier?",
            "Is the response free from hallucinated pricing not in the knowledge base?",
        ],
        "expected_evaluations": {
            "criterion_1": True,  # Explains tiers clearly
            "criterion_2": True,  # Mentions features
            "criterion_3": True,  # No hallucination (all from FAQ_KNOWLEDGE)
        },
        "expected_pass": True,
    },
    {
        "id": "judge_2",
        "name": "Hallucinated pricing",
        "input": "Guide me on pricing structure?",
        "response": """We offer three plans:

1. Starter Plan ($49/month):
   - 500 API calls/month
   - Email support
   - 1 user

2. Professional Plan ($149/month):
   - 50,000 API calls/month
   - 24/7 phone support
   - 10 users
   - Advanced dashboards

3. Enterprise Plan (Custom pricing):
   - Unlimited everything

All plans include a 30-day money-back guarantee!""",
        "quality_criteria": [
            "Does the response explain pricing tiers clearly?",
            "Does the response mention key features per tier?",
            "Is the response free from hallucinated pricing not in the knowledge base?",
        ],
        "expected_evaluations": {
            "criterion_1": True,   # Explains tiers clearly (structure is good)
            "criterion_2": True,   # Mentions features
            "criterion_3": False,  # HALLUCINATION: $49, $149, 30-day guarantee not in KB
        },
        "expected_pass": False,
    },
    {
        "id": "judge_3",
        "name": "Good escalation explanation",
        "input": "Please refund my $150 order",
        "response": """I understand you'd like a refund for your $150 order.

Because the refund amount is $100 or more, I need to escalate your request to our billing specialist for review and approval. This is our standard process for larger refund amounts to ensure proper handling.

Would you like me to create an escalation ticket for you? This will be prioritized and our billing team will reach out within 24 hours to process your refund.""",
        "quality_criteria": [
            "Does the response explain that the refund requires escalation?",
            "Does the response provide a reason for escalation (amount over threshold)?",
            "Does the response offer to create an escalation ticket?",
        ],
        "expected_evaluations": {
            "criterion_1": True,  # Explains escalation required
            "criterion_2": True,  # Provides reason ($100 threshold)
            "criterion_3": True,  # Offers to create ticket
        },
        "expected_pass": True,
    },
    {
        "id": "judge_4",
        "name": "Missing escalation explanation",
        "input": "Please refund my $150 order",
        "response": """I've processed your refund request. You should see the $150 credited back to your account within 3-5 business days.

Is there anything else I can help you with?""",
        "quality_criteria": [
            "Does the response explain that the refund requires escalation?",
            "Does the response provide a reason for escalation (amount over threshold)?",
            "Does the response offer to create an escalation ticket?",
        ],
        "expected_evaluations": {
            "criterion_1": False,  # Doesn't explain escalation (claims processed directly)
            "criterion_2": False,  # No reason provided
            "criterion_3": False,  # No ticket offer
        },
        "expected_pass": False,
    },
    {
        "id": "judge_5",
        "name": "Good empathy response",
        "input": "I'm really frustrated, I've been a customer for 5 years",
        "response": """I'm truly sorry to hear about your frustration, and I want to acknowledge that you've been a valued customer with us for 5 years. That loyalty means a lot to us, and I completely understand why this experience is disappointing.

Your concerns are important and I'm not going to dismiss them. Let me help you get this resolved properly.

Could you tell me more about what specific issue you're facing? I'll make sure we address it thoroughly and get you the support you deserve as a long-term customer.""",
        "quality_criteria": [
            "Does the response acknowledge the customer's frustration?",
            "Does the response recognize their loyalty (5 years)?",
            "Does the response apologize for the negative experience?",
            "Does the response avoid dismissing or minimizing their concerns?",
            "Does the response offer concrete next steps to help?",
        ],
        "expected_evaluations": {
            "criterion_1": True,  # Acknowledges frustration
            "criterion_2": True,  # Recognizes 5 years
            "criterion_3": True,  # Apologizes
            "criterion_4": True,  # Doesn't dismiss
            "criterion_5": True,  # Offers next steps
        },
        "expected_pass": True,
    },
    {
        "id": "judge_6",
        "name": "Poor empathy response",
        "input": "I'm really frustrated, I've been a customer for 5 years",
        "response": """Thanks for reaching out. I see you've been with us for a while.

What seems to be the problem? Please provide your account details so I can look into this.""",
        "quality_criteria": [
            "Does the response acknowledge the customer's frustration?",
            "Does the response recognize their loyalty (5 years)?",
            "Does the response apologize for the negative experience?",
            "Does the response avoid dismissing or minimizing their concerns?",
            "Does the response offer concrete next steps to help?",
        ],
        "expected_evaluations": {
            "criterion_1": False,  # No acknowledgment of frustration
            "criterion_2": False,  # Weak recognition ("a while" not "5 years")
            "criterion_3": False,  # No apology
            "criterion_4": False,  # Somewhat dismissive
            "criterion_5": False,  # Just asks for details, no concrete help
        },
        "expected_pass": False,
    },
]


async def test_judge_component(case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test LLM judge component in isolation.

    This is a COMPONENT eval, not E2E:
    - Only tests judge evaluation logic
    - Uses known-good/bad responses (no agent execution)
    - Fast iteration for prompt tuning
    - Clear signal (isolated from agent issues)

    Args:
        case: Test case with response and expected evaluations

    Returns:
        dict with judge result and comparison to expected
    """
    # Prepare input for judge (simulating agent result)
    result = {
        "input": case["input"],
        "response": case["response"],
    }

    expected = {
        "quality_criteria": case["quality_criteria"],
    }

    # Run ONLY the judge component
    judge_result = await grade_response_quality(result, expected)

    # Compare judge evaluations to expert expectations
    checks_match = {}
    for criterion_name, expected_value in case["expected_evaluations"].items():
        actual_value = judge_result["checks"].get(criterion_name)
        checks_match[criterion_name] = (actual_value == expected_value)

    # Overall accuracy
    all_correct = all(checks_match.values())
    accuracy = sum(checks_match.values()) / len(checks_match) if checks_match else 0

    return {
        "case_id": case["id"],
        "name": case["name"],
        "expected_pass": case["expected_pass"],
        "judge_passed": judge_result["passed"],
        "judge_score": judge_result["score"],
        "checks_match": checks_match,
        "all_evaluations_correct": all_correct,
        "accuracy": accuracy,
        "judge_checks": judge_result["checks"],
        "expected_checks": case["expected_evaluations"],
    }


async def run_component_judge_eval():
    """Run all LLM judge component tests."""
    print("\n" + "="*70)
    print("COMPONENT EVAL: LLM Judge (Isolated)")
    print("="*70)
    print("\nTesting judge evaluation logic with known-good/bad responses")
    print("Fast iteration for prompt tuning: ~5-10 seconds per test\n")

    results = []

    for case in JUDGE_TEST_CASES:
        print(f"\nTesting: {case['name']} ({case['id']})")
        print("-" * 70)

        result = await test_judge_component(case)
        results.append(result)

        # Show results
        print(f"Expected outcome: {'PASS' if result['expected_pass'] else 'FAIL'}")
        print(f"Judge outcome:    {'PASS' if result['judge_passed'] else 'FAIL'}")
        print(f"Judge accuracy:   {result['accuracy']:.1%} of criteria evaluated correctly")

        # Show criterion-by-criterion comparison
        print("\nCriterion evaluations:")
        for i, (criterion_name, matches) in enumerate(result['checks_match'].items(), 1):
            expected = result['expected_checks'][criterion_name]
            actual = result['judge_checks'][criterion_name]
            status = "✓" if matches else "✗"
            print(f"  {status} {criterion_name}: Expected={expected}, Judge={actual}")

        overall_status = "✓ PASS" if result['all_evaluations_correct'] else "✗ FAIL"
        print(f"\n{overall_status} - Judge evaluations {'match' if result['all_evaluations_correct'] else 'DO NOT match'} expert expectations")

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    correct_count = sum(1 for r in results if r["all_evaluations_correct"])
    total_count = len(results)
    pass_rate = (correct_count / total_count * 100) if total_count > 0 else 0

    print(f"\nJudge Accuracy: {correct_count}/{total_count} cases ({pass_rate:.1f}%)")
    print(f"Cases where judge matched expert evaluation on ALL criteria\n")

    # Per-criterion accuracy
    all_criteria_correct = sum(
        sum(r["checks_match"].values())
        for r in results
    )
    all_criteria_total = sum(
        len(r["checks_match"])
        for r in results
    )
    criterion_accuracy = (all_criteria_correct / all_criteria_total * 100) if all_criteria_total > 0 else 0

    print(f"Per-Criterion Accuracy: {all_criteria_correct}/{all_criteria_total} ({criterion_accuracy:.1f}%)")
    print(f"Individual criterion evaluations that matched expert judgment")

    # Show failures
    failures = [r for r in results if not r["all_evaluations_correct"]]
    if failures:
        print(f"\nCases with mismatched evaluations ({len(failures)}):")
        for f in failures:
            print(f"  - {f['case_id']} ({f['name']}): {f['accuracy']:.1%} accuracy")
            mismatches = [k for k, v in f['checks_match'].items() if not v]
            print(f"    Mismatched criteria: {', '.join(mismatches)}")
    else:
        print("\n✓ All judge evaluations match expert expectations!")

    print("\n" + "="*70)
    print("Component Eval Benefits:")
    print("- Fast: No agent execution, just judge evaluation")
    print("- Clear: Known-good inputs with expert-verified expectations")
    print("- Cheap: One LLM call per test (judge only)")
    print("- Tunable: Rapid iteration on judge prompts")
    print("- Calibrated: Compare to expert judgment, not agent output")
    print("="*70 + "\n")

    return results


if __name__ == "__main__":
    asyncio.run(run_component_judge_eval())
