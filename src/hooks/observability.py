"""Observability hooks for logging agent lifecycle events."""

import json
import time
from datetime import datetime
from typing import Any
from dataclasses import dataclass, field, asdict

from agents import RunHooks, Agent, Tool, RunContextWrapper
from agents.lifecycle import AgentHookContext

from src.models.context import SupportContext


@dataclass
class AgentEvent:
    """Structured log event for agent lifecycle."""
    event_type: str
    timestamp: str
    agent_name: str
    duration_ms: float | None = None
    details: dict = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


@dataclass
class ToolEvent:
    """Structured log event for tool calls."""
    event_type: str
    timestamp: str
    agent_name: str
    tool_name: str
    duration_ms: float | None = None
    input_args: dict = field(default_factory=dict)
    output: str | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


@dataclass
class HandoffEvent:
    """Structured log event for agent handoffs."""
    event_type: str
    timestamp: str
    from_agent: str
    to_agent: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


class SupportHooks(RunHooks[SupportContext]):
    """
    Observability hooks for Customer Support FTE.

    Logs agent starts/ends, tool calls, and handoffs with timing.
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self._agent_start_times: dict[str, float] = {}
        self._tool_start_times: dict[str, float] = {}
        self.events: list[dict] = []

    def _log(self, event: AgentEvent | ToolEvent | HandoffEvent) -> None:
        """Log an event."""
        event_dict = asdict(event)
        self.events.append(event_dict)
        if self.verbose:
            print(f"[LOG] {event.to_json()}")

    async def on_agent_start(
        self,
        context: RunContextWrapper[SupportContext],
        agent: Agent,
    ) -> None:
        """Called when an agent starts processing."""
        self._agent_start_times[agent.name] = time.time()

        event = AgentEvent(
            event_type="agent_start",
            timestamp=datetime.now().isoformat(),
            agent_name=agent.name,
            details={
                "session_id": context.context.session.session_id,
                "turn": context.context.session.turn_count,
            },
        )
        self._log(event)

        # Track in routing history
        if agent.name not in context.context.routing.agents_involved:
            context.context.routing.agents_involved.append(agent.name)
        context.context.routing.current_agent = agent.name

    async def on_agent_end(
        self,
        context: RunContextWrapper[SupportContext],
        agent: Agent,
        output: Any,
    ) -> None:
        """Called when an agent finishes processing."""
        start_time = self._agent_start_times.pop(agent.name, None)
        duration_ms = (time.time() - start_time) * 1000 if start_time else None

        event = AgentEvent(
            event_type="agent_end",
            timestamp=datetime.now().isoformat(),
            agent_name=agent.name,
            duration_ms=round(duration_ms, 2) if duration_ms else None,
            details={
                "output_length": len(str(output)) if output else 0,
            },
        )
        self._log(event)

    async def on_tool_start(
        self,
        context: RunContextWrapper[SupportContext],
        agent: Agent,
        tool: Tool,
    ) -> None:
        """Called when a tool starts executing."""
        tool_key = f"{agent.name}:{tool.name}"
        self._tool_start_times[tool_key] = time.time()

        event = ToolEvent(
            event_type="tool_start",
            timestamp=datetime.now().isoformat(),
            agent_name=agent.name,
            tool_name=tool.name,
        )
        self._log(event)

    async def on_tool_end(
        self,
        context: RunContextWrapper[SupportContext],
        agent: Agent,
        tool: Tool,
        result: str,
    ) -> None:
        """Called when a tool finishes executing."""
        tool_key = f"{agent.name}:{tool.name}"
        start_time = self._tool_start_times.pop(tool_key, None)
        duration_ms = (time.time() - start_time) * 1000 if start_time else None

        event = ToolEvent(
            event_type="tool_end",
            timestamp=datetime.now().isoformat(),
            agent_name=agent.name,
            tool_name=tool.name,
            duration_ms=round(duration_ms, 2) if duration_ms else None,
            output=result[:200] if result else None,  # Truncate long outputs
        )
        self._log(event)

    async def on_handoff(
        self,
        context: RunContextWrapper[SupportContext],
        from_agent: Agent,
        to_agent: Agent,
    ) -> None:
        """Called when a handoff occurs between agents."""
        event = HandoffEvent(
            event_type="handoff",
            timestamp=datetime.now().isoformat(),
            from_agent=from_agent.name,
            to_agent=to_agent.name,
        )
        self._log(event)

        # Record in context
        context.context.record_handoff(
            from_agent=from_agent.name,
            to_agent=to_agent.name,
            reason="Agent handoff",
        )

    def get_summary(self) -> dict:
        """Get summary of all logged events."""
        agent_events = [e for e in self.events if e["event_type"].startswith("agent_")]
        tool_events = [e for e in self.events if e["event_type"].startswith("tool_")]
        handoff_events = [e for e in self.events if e["event_type"] == "handoff"]

        # Calculate total duration
        total_duration = sum(
            e.get("duration_ms", 0) or 0
            for e in agent_events
            if e["event_type"] == "agent_end"
        )

        return {
            "total_events": len(self.events),
            "agent_events": len(agent_events),
            "tool_events": len(tool_events),
            "handoff_events": len(handoff_events),
            "total_duration_ms": round(total_duration, 2),
            "agents_involved": list(set(
                e["agent_name"] for e in agent_events
            )),
            "tools_used": list(set(
                e["tool_name"] for e in tool_events
            )),
        }
