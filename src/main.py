"""Main handler for Customer Support FTE."""

import asyncio
from datetime import datetime
from uuid import uuid4
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from agents import Runner, RunConfig, InputGuardrailTripwireTriggered, SQLiteSession

from src.models.context import SupportContext, SessionMetadata
from src.agents.triage import triage_agent
from src.guardrails import (
    pii_guardrail,
    injection_guardrail,
    secrets_guardrail,
    PII_ERROR_MESSAGE,
    INJECTION_ERROR_MESSAGE,
    OUTPUT_BLOCKED_MESSAGE,
)


# Create triage agent with guardrails
def create_guarded_triage_agent():
    """Create triage agent with input/output guardrails attached."""
    # Clone triage agent with guardrails
    from agents import Agent
    from src.tools.customer import lookup_customer
    from src.agents import faq_agent, billing_agent, technical_agent, escalation_agent

    return Agent(
        name=triage_agent.name,
        instructions=triage_agent.instructions,
        tools=[lookup_customer],
        handoffs=[faq_agent, billing_agent, technical_agent, escalation_agent],
        input_guardrails=[pii_guardrail, injection_guardrail],
        output_guardrails=[secrets_guardrail],
    )


# Session storage
SESSION_DB_PATH = "sessions.db"


async def handle_message(
    message: str,
    session_id: Optional[str] = None,
    context: Optional[SupportContext] = None,
) -> dict:
    """
    Handle a customer support message.

    Args:
        message: The customer's message
        session_id: Optional session ID for conversation continuity
        context: Optional existing context

    Returns:
        Dict with response, session_id, context, and metadata
    """
    # Generate session ID if not provided
    if session_id is None:
        session_id = f"session-{uuid4().hex[:8]}"

    # Create or use existing context
    if context is None:
        context = SupportContext(
            session=SessionMetadata(session_id=session_id)
        )

    # Increment turn count
    context.increment_turn()

    # Create guarded agent
    guarded_agent = create_guarded_triage_agent()

    # Create session for persistence
    session = SQLiteSession(
        db_path=SESSION_DB_PATH,
        session_id=session_id,
    )

    # Run configuration
    run_config = RunConfig(
        workflow_name="customer-support",
        trace_id=f"trace_{uuid4().hex[:8]}",  # Must start with "trace_"
    )

    try:
        # Run the agent
        result = await Runner.run(
            starting_agent=guarded_agent,
            input=message,
            context=context,
            session=session,
            run_config=run_config,
        )

        # Update metrics from result
        if hasattr(result, 'raw_responses'):
            for response in result.raw_responses:
                if hasattr(response, 'usage'):
                    context.update_metrics(
                        input_tokens=response.usage.input_tokens or 0,
                        output_tokens=response.usage.output_tokens or 0,
                    )

        return {
            "response": result.final_output,
            "session_id": session_id,
            "context": context.model_dump(),
            "agent_used": result.last_agent.name if result.last_agent else "unknown",
            "success": True,
        }

    except InputGuardrailTripwireTriggered as e:
        # Handle guardrail violations
        # Structure: e.guardrail_result.output.output_info
        output_info = e.guardrail_result.output.output_info

        # Determine which guardrail was triggered based on output_info
        if "PII detected" in output_info:
            error_message = PII_ERROR_MESSAGE
            guardrail_type = "pii_guardrail"
        elif "injection" in output_info.lower():
            error_message = INJECTION_ERROR_MESSAGE
            guardrail_type = "injection_guardrail"
        else:
            error_message = "I'm sorry, I couldn't process that request."
            guardrail_type = "unknown_guardrail"

        return {
            "response": error_message,
            "session_id": session_id,
            "context": context.model_dump(),
            "agent_used": "guardrail",
            "success": False,
            "guardrail_triggered": guardrail_type,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()  # Print full traceback for debugging
        return {
            "response": f"I apologize, but I encountered an error. Please try again. Error: {str(e)}",
            "session_id": session_id,
            "context": context.model_dump(),
            "agent_used": "error",
            "success": False,
            "error": str(e),
        }


async def chat_loop():
    """Interactive chat loop for testing."""
    print("Customer Support FTE")
    print("=" * 40)
    print("Type 'quit' to exit, 'new' for new session")
    print()

    session_id = None
    context = None

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("Goodbye!")
            break

        if user_input.lower() == "new":
            session_id = None
            context = None
            print("Started new session.\n")
            continue

        result = await handle_message(
            message=user_input,
            session_id=session_id,
            context=context,
        )

        # Preserve session for continuity
        session_id = result["session_id"]

        # Reconstruct context from result
        if result["success"]:
            context = SupportContext(**result["context"])

        print(f"\nAgent ({result['agent_used']}): {result['response']}\n")


def main():
    """Entry point."""
    asyncio.run(chat_loop())


if __name__ == "__main__":
    main()
