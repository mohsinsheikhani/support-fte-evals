"""Q4 Graders: Subjective quality assessment (LLM-as-Judge)."""


# LLM Grader prompt template - uses binary YES/NO questions
HELPFULNESS_PROMPT = """
Evaluate the following customer support response.

## Customer Message
{input}

## Agent Response
{response}

## Evaluation Criteria
Answer each question with YES or NO only:

1. Does the response directly address the customer's request?
2. Does the response provide actionable information or next steps?
3. Is the response free of hallucinated or made-up information?
4. Is the response complete without being unnecessarily verbose?
5. Would a reasonable customer find this response helpful?

## Your Evaluation
Provide exactly 5 lines, one answer per criterion:
"""

TONE_PROMPT = """
Evaluate the tone of the following customer support response.

## Customer Message
{input}

## Agent Response
{response}

## Evaluation Criteria
Answer each question with YES or NO only:

1. Is the tone professional and appropriate for customer support?
2. Does the response show empathy for the customer's situation?
3. Is the language clear and easy to understand?
4. Does the response avoid being robotic or overly formal?
5. Would the tone make a customer feel valued?

## Your Evaluation
Provide exactly 5 lines, one answer per criterion:
"""


def parse_llm_response(llm_response: str, criteria: list[str]) -> dict:
    """Parse YES/NO responses into structured result."""
    # TODO: Implement parser
    # Hint: Split by lines, check for YES/NO, map to criteria names
    pass


async def grade_helpfulness(result: dict, case: dict, llm_client) -> dict:
    """
    Use LLM to judge response helpfulness.

    Args:
        result: Output from handle_message()
        case: Test case with input
        llm_client: LLM client for judging

    Returns:
        dict with passed, score, and criteria details
    """
    # TODO: Implement helpfulness grader
    # Hint: Format prompt, call LLM, parse response
    pass


async def grade_tone(result: dict, case: dict, llm_client) -> dict:
    """
    Use LLM to judge response tone.

    Args:
        result: Output from handle_message()
        case: Test case with input
        llm_client: LLM client for judging

    Returns:
        dict with passed, score, and criteria details
    """
    # TODO: Implement tone grader
    pass
