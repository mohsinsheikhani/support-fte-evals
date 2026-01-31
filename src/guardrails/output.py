"""Output guardrails - Prevent leaking sensitive data."""

import re
from agents import output_guardrail, GuardrailFunctionOutput, RunContextWrapper
from src.models.context import SupportContext

# Sensitive data patterns in output
API_KEY_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]{32,}", re.IGNORECASE),  # OpenAI-style
    re.compile(r"api[_-]?key[\"'\s:=]+[a-zA-Z0-9]{16,}", re.IGNORECASE),
    re.compile(r"bearer\s+[a-zA-Z0-9\-_.]{20,}", re.IGNORECASE),
    re.compile(r"token[\"'\s:=]+[a-zA-Z0-9\-_.]{20,}", re.IGNORECASE),
]

INTERNAL_ID_PATTERNS = [
    re.compile(r"internal[_-]?id[\"'\s:=]+\w+", re.IGNORECASE),
    re.compile(r"db[_-]?id[\"'\s:=]+\w+", re.IGNORECASE),
    re.compile(r"user[_-]?id[\"'\s:=]+[a-f0-9\-]{32,}", re.IGNORECASE),  # UUID-like
]

DATABASE_QUERY_PATTERNS = [
    re.compile(r"\bSELECT\s+.+\s+FROM\s+", re.IGNORECASE),
    re.compile(r"\bINSERT\s+INTO\s+", re.IGNORECASE),
    re.compile(r"\bUPDATE\s+\w+\s+SET\s+", re.IGNORECASE),
    re.compile(r"\bDELETE\s+FROM\s+", re.IGNORECASE),
]

PASSWORD_PATTERNS = [
    re.compile(r"password[\"'\s:=]+\S{8,}", re.IGNORECASE),
    re.compile(r"passwd[\"'\s:=]+\S{8,}", re.IGNORECASE),
    re.compile(r"secret[\"'\s:=]+\S{8,}", re.IGNORECASE),
]


def detect_sensitive_output(text: str) -> list[str]:
    """Detect sensitive data patterns in output. Returns list of detected types."""
    detected = []

    for pattern in API_KEY_PATTERNS:
        if pattern.search(text):
            detected.append("API key")
            break

    for pattern in INTERNAL_ID_PATTERNS:
        if pattern.search(text):
            detected.append("internal ID")
            break

    for pattern in DATABASE_QUERY_PATTERNS:
        if pattern.search(text):
            detected.append("database query")
            break

    for pattern in PASSWORD_PATTERNS:
        if pattern.search(text):
            detected.append("password")
            break

    return detected


@output_guardrail
async def secrets_guardrail(
    context: RunContextWrapper[SupportContext],
    agent,
    output: str,
) -> GuardrailFunctionOutput:
    """Block responses that would leak sensitive data."""
    detected = detect_sensitive_output(output)

    if detected:
        leak_types = ", ".join(detected)
        return GuardrailFunctionOutput(
            output_info=f"Sensitive data detected in output: {leak_types}",
            tripwire_triggered=True,
        )

    return GuardrailFunctionOutput(
        output_info="No sensitive data in output",
        tripwire_triggered=False,
    )


# Fallback message when output is blocked
OUTPUT_BLOCKED_MESSAGE = (
    "I apologize, but I encountered an issue generating a response. "
    "Please contact our support team directly for assistance with your request."
)
