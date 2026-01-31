"""Input guardrails - PII detection and prompt injection prevention."""

import re
from agents import input_guardrail, GuardrailFunctionOutput, RunContextWrapper
from src.models.context import SupportContext

# PII patterns
CREDIT_CARD_PATTERN = re.compile(
    r"\b(?:\d{4}[-\s]?){3}\d{4}\b"  # 1234-5678-9012-3456 or spaces
)
SSN_PATTERN = re.compile(
    r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b"  # 123-45-6789
)
BANK_ACCOUNT_PATTERN = re.compile(
    r"\b\d{8,17}\b"  # 8-17 digit account numbers
)

# Prompt injection patterns
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"ignore\s+(all\s+)?prior\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+", re.IGNORECASE),
    re.compile(r"pretend\s+(you\s+are|to\s+be)", re.IGNORECASE),
    re.compile(r"act\s+as\s+(if\s+you\s+are|a)", re.IGNORECASE),
    re.compile(r"forget\s+(all\s+)?your\s+(instructions|rules)", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|prior)", re.IGNORECASE),
    re.compile(r"new\s+instructions?:", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),  # Trying to inject system prompt
]


def detect_pii(text: str) -> list[str]:
    """Detect PII patterns in text. Returns list of detected types."""
    detected = []

    if CREDIT_CARD_PATTERN.search(text):
        detected.append("credit card number")

    if SSN_PATTERN.search(text):
        detected.append("Social Security Number")

    # Only flag bank account if it looks like one (near banking keywords)
    banking_context = re.search(
        r"(account|routing|bank|iban|swift)", text, re.IGNORECASE
    )
    if banking_context and BANK_ACCOUNT_PATTERN.search(text):
        detected.append("bank account number")

    return detected


def detect_injection(text: str) -> bool:
    """Detect prompt injection attempts."""
    for pattern in INJECTION_PATTERNS:
        if pattern.search(text):
            return True
    return False


@input_guardrail
async def pii_guardrail(
    context: RunContextWrapper[SupportContext],
    agent,
    input_text: str,
) -> GuardrailFunctionOutput:
    """Block messages containing PII like credit cards, SSN, bank accounts."""
    detected = detect_pii(input_text)

    if detected:
        pii_types = ", ".join(detected)
        return GuardrailFunctionOutput(
            output_info=f"PII detected: {pii_types}",
            tripwire_triggered=True,
        )

    return GuardrailFunctionOutput(
        output_info="No PII detected",
        tripwire_triggered=False,
    )


@input_guardrail
async def injection_guardrail(
    context: RunContextWrapper[SupportContext],
    agent,
    input_text: str,
) -> GuardrailFunctionOutput:
    """Block prompt injection attempts."""
    if detect_injection(input_text):
        return GuardrailFunctionOutput(
            output_info="Prompt injection attempt detected",
            tripwire_triggered=True,
        )

    return GuardrailFunctionOutput(
        output_info="No injection detected",
        tripwire_triggered=False,
    )


# User-friendly error messages
PII_ERROR_MESSAGE = (
    "I noticed your message may contain sensitive information like credit card "
    "numbers or personal identification numbers. For your security, please don't "
    "share this information in chat. Our team will never ask for full card numbers "
    "or SSNs. How else can I help you today?"
)

INJECTION_ERROR_MESSAGE = (
    "I'm sorry, but I can't process that request. If you need help with our "
    "products or services, please let me know how I can assist you."
)
