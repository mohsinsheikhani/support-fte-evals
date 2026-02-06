"""Q2 Graders: Response quality assessment (LLM-as-Judge with structured output)."""

import asyncio
from typing import Dict, Any, List
from pydantic import BaseModel, Field, create_model
from agents import Agent, Runner

# Import FAQ knowledge base for accuracy verification
from src.agents.faq import FAQ_KNOWLEDGE


def create_evaluation_model(criteria: List[str]) -> type[BaseModel]:
    """
    Dynamically create a Pydantic model for quality criteria evaluation.

    Args:
        criteria: List of YES/NO questions from dataset

    Returns:
        Pydantic model class with bool fields for each criterion
    """
    # Create field definitions for each criterion
    field_definitions = {}

    for i, criterion in enumerate(criteria, start=1):
        field_name = f"criterion_{i}"
        field_definitions[field_name] = (
            bool,
            Field(description=criterion)
        )

    # Dynamically create the model
    EvaluationModel = create_model(
        "QualityEvaluation",
        **field_definitions
    )

    return EvaluationModel


async def grade_response_quality(result: Dict[str, Any], expected: Dict[str, Any]) -> Dict[str, Any]:
    """
    Grade response quality using LLM-as-judge with structured output.

    Uses dynamic Pydantic models based on quality_criteria from dataset.
    Each criterion is evaluated as YES/NO (True/False).

    Args:
        result: Output from handle_message() with agent response
        expected: Expected dict containing quality_criteria list

    Returns:
        dict with passed, score, checks, failed_checks
    """
    # Get quality criteria from dataset
    quality_criteria = expected.get("quality_criteria", [])

    if not quality_criteria:
        return {
            "passed": False,
            "score": 0.0,
            "checks": {},
            "failed_checks": ["no_quality_criteria"],
            "error": "No quality_criteria specified in expected",
        }

    # Get input and response
    input_text = result.get("input", "")
    response_text = result.get("response", "")

    if not response_text:
        return {
            "passed": False,
            "score": 0.0,
            "checks": {},
            "failed_checks": ["no_response"],
            "error": "No response in result",
        }

    # Create dynamic Pydantic model for these criteria
    EvaluationModel = create_evaluation_model(quality_criteria)

    # Build evaluation prompt
    criteria_list = "\n".join([f"{i}. {q}" for i, q in enumerate(quality_criteria, start=1)])

    # Check if we need to provide knowledge base for accuracy verification
    needs_kb = any(
        keyword in criterion.lower()
        for criterion in quality_criteria
        for keyword in ["hallucinate", "knowledge base", "accurate", "correct pricing", "not in"]
    )

    # Build prompt with optional knowledge base
    kb_section = ""
    if needs_kb:
        kb_section = f"""
## Knowledge Base (Ground Truth)
{FAQ_KNOWLEDGE}

When evaluating accuracy criteria, compare the agent's response against this knowledge base.
Verify that all facts, prices, and features mentioned are present in the knowledge base above.
"""

    instructions = f"""You are an expert evaluator for customer support responses.

Evaluate the agent's response against each criterion below. Answer TRUE or FALSE for each.

## Customer Input
{input_text}

## Agent Response
{response_text}
{kb_section}
## Evaluation Criteria
{criteria_list}

For each criterion, determine if the response meets it (TRUE) or not (FALSE).
Be objective and precise. Base your evaluation on what is present in the response.
For accuracy criteria, verify facts against the knowledge base provided above."""

    # Create LLM judge agent with structured output
    judge_agent = Agent(
        name="QualityJudge",
        instructions=instructions,
        output_type=EvaluationModel,
    )

    # Run evaluation
    try:
        judge_result = await Runner.run(
            starting_agent=judge_agent,
            input="Evaluate the response against the criteria.",
        )

        # Get structured output
        evaluation: EvaluationModel = judge_result.final_output

        # Convert to checks dict
        checks = {}
        failed_checks = []

        for i, criterion in enumerate(quality_criteria, start=1):
            field_name = f"criterion_{i}"
            criterion_passed = getattr(evaluation, field_name)

            # Use simplified check name
            check_name = f"criterion_{i}"
            checks[check_name] = criterion_passed

            if not criterion_passed:
                failed_checks.append(check_name)

        # Calculate score
        total_criteria = len(quality_criteria)
        passed_criteria = sum(checks.values())
        score = passed_criteria / total_criteria if total_criteria > 0 else 0.0

        # Overall pass: all criteria must pass
        passed = len(failed_checks) == 0

        return {
            "passed": passed,
            "score": score,
            "checks": checks,
            "failed_checks": failed_checks,
            "criteria": quality_criteria,  # Include for reference
        }

    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": {},
            "failed_checks": ["llm_judge_error"],
            "error": f"LLM judge failed: {str(e)}",
        }
