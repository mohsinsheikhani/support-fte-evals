"""Agents for Customer Support FTE."""

from src.agents.faq import faq_agent
from src.agents.escalation import escalation_agent
from src.agents.billing import billing_agent
from src.agents.technical import technical_agent
from src.agents.triage import triage_agent

__all__ = [
    "faq_agent",
    "billing_agent",
    "technical_agent",
    "escalation_agent",
    "triage_agent",
]
