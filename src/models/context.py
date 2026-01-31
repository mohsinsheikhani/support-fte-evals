"""Context model for Customer Support FTE.

Tracks customer, session, routing, metrics, and resolution state
across the entire conversation lifecycle.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ResolutionStatus(str, Enum):
    """Status of the support interaction."""
    PENDING = "pending"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class CustomerInfo(BaseModel):
    """Customer identification data."""
    id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    plan: Optional[str] = None  # e.g., "free", "premium", "enterprise"


class SessionMetadata(BaseModel):
    """Session tracking data."""
    session_id: str
    start_time: datetime = Field(default_factory=datetime.now)
    turn_count: int = 0


class HandoffRecord(BaseModel):
    """Record of a single agent handoff."""
    from_agent: str
    to_agent: str
    reason: str
    timestamp: datetime = Field(default_factory=datetime.now)


class RoutingHistory(BaseModel):
    """Tracks agent routing through the conversation."""
    agents_involved: list[str] = Field(default_factory=list)
    handoffs: list[HandoffRecord] = Field(default_factory=list)
    current_agent: Optional[str] = None


class UsageMetrics(BaseModel):
    """Token and cost tracking."""
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def estimated_cost(self) -> float:
        """Estimate cost based on GPT-4o pricing (rough)."""
        # $2.50/1M input, $10.00/1M output
        input_cost = (self.input_tokens / 1_000_000) * 2.50
        output_cost = (self.output_tokens / 1_000_000) * 10.00
        return input_cost + output_cost


class Resolution(BaseModel):
    """Resolution state of the support interaction."""
    status: ResolutionStatus = ResolutionStatus.PENDING
    reason: Optional[str] = None
    resolved_by: Optional[str] = None  # agent name
    escalation_ticket_id: Optional[str] = None


class SupportContext(BaseModel):
    """
    Main context object passed through the agent system.

    This is the RunContextWrapper[T] type parameter for all tools.
    """
    customer: CustomerInfo = Field(default_factory=CustomerInfo)
    session: SessionMetadata
    routing: RoutingHistory = Field(default_factory=RoutingHistory)
    metrics: UsageMetrics = Field(default_factory=UsageMetrics)
    resolution: Resolution = Field(default_factory=Resolution)

    def record_handoff(self, from_agent: str, to_agent: str, reason: str) -> None:
        """Record an agent handoff."""
        self.routing.handoffs.append(
            HandoffRecord(from_agent=from_agent, to_agent=to_agent, reason=reason)
        )
        if to_agent not in self.routing.agents_involved:
            self.routing.agents_involved.append(to_agent)
        self.routing.current_agent = to_agent

    def mark_resolved(self, agent: str, reason: str) -> None:
        """Mark the interaction as resolved."""
        self.resolution.status = ResolutionStatus.RESOLVED
        self.resolution.resolved_by = agent
        self.resolution.reason = reason

    def mark_escalated(self, ticket_id: str, reason: str) -> None:
        """Mark the interaction as escalated to human."""
        self.resolution.status = ResolutionStatus.ESCALATED
        self.resolution.escalation_ticket_id = ticket_id
        self.resolution.reason = reason

    def increment_turn(self) -> None:
        """Increment the conversation turn count."""
        self.session.turn_count += 1

    def update_metrics(self, input_tokens: int, output_tokens: int) -> None:
        """Update token usage metrics."""
        self.metrics.input_tokens += input_tokens
        self.metrics.output_tokens += output_tokens
