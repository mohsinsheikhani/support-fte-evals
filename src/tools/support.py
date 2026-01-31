"""Support ticket tools."""

from datetime import datetime, timedelta
from uuid import uuid4
from agents import function_tool, RunContextWrapper
from src.models.context import SupportContext

# Mock support tickets database
MOCK_TICKETS = {
    "C001": [  # Alice
        {
            "ticket_id": "TKT-101",
            "subject": "API rate limiting issue",
            "status": "open",
            "priority": "high",
            "created": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
        },
    ],
    "C002": [  # Bob
        {
            "ticket_id": "TKT-201",
            "subject": "Cannot export data",
            "status": "open",
            "priority": "medium",
            "created": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
        },
        {
            "ticket_id": "TKT-202",
            "subject": "Login issues on mobile",
            "status": "resolved",
            "priority": "low",
            "created": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
        },
    ],
    "C003": [],  # Carol - no tickets
}

# Track created escalation tickets
ESCALATION_TICKETS: list[dict] = []


@function_tool
def check_support_tickets(
    wrapper: RunContextWrapper[SupportContext],
) -> str:
    """Get open support tickets for the current customer.

    Returns a list of support tickets for the identified customer.
    Customer must be identified first using lookup_customer.

    Returns:
        List of tickets or an error if customer not identified.
    """
    customer_id = wrapper.context.customer.id

    if not customer_id:
        return "Error: Customer not identified. Please look up the customer first."

    tickets = MOCK_TICKETS.get(customer_id, [])
    open_tickets = [t for t in tickets if t["status"] == "open"]

    if not open_tickets:
        return f"No open support tickets for {wrapper.context.customer.name}."

    lines = [f"Open support tickets for {wrapper.context.customer.name}:\n"]
    for ticket in open_tickets:
        lines.append(
            f"- {ticket['ticket_id']}: {ticket['subject']}\n"
            f"  Priority: {ticket['priority']} | Created: {ticket['created']}"
        )

    return "\n".join(lines)


@function_tool
def create_escalation_ticket(
    wrapper: RunContextWrapper[SupportContext],
    subject: str,
    description: str,
    priority: str = "medium",
) -> str:
    """Create an escalation ticket for human agent review.

    Use this when an issue cannot be resolved automatically and requires
    human intervention.

    Args:
        subject: Brief summary of the issue.
        description: Detailed description of the issue and context.
        priority: Ticket priority - "low", "medium", or "high".

    Returns:
        Confirmation with ticket ID and expected SLA.
    """
    customer_id = wrapper.context.customer.id

    if not customer_id:
        return "Error: Customer not identified. Please look up the customer first."

    # Validate priority
    if priority not in ("low", "medium", "high"):
        priority = "medium"

    # Generate ticket
    ticket_id = f"ESC-{uuid4().hex[:6].upper()}"

    # SLA based on priority
    sla_hours = {"low": 48, "medium": 24, "high": 4}[priority]

    ticket = {
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "customer_name": wrapper.context.customer.name,
        "customer_email": wrapper.context.customer.email,
        "subject": subject,
        "description": description,
        "priority": priority,
        "status": "pending_human_review",
        "created": datetime.now().isoformat(),
        "sla_hours": sla_hours,
    }

    ESCALATION_TICKETS.append(ticket)

    # Update context
    wrapper.context.mark_escalated(ticket_id, subject)

    return (
        f"Escalation ticket created successfully!\n"
        f"- Ticket ID: {ticket_id}\n"
        f"- Priority: {priority.upper()}\n"
        f"- SLA: Response within {sla_hours} hours\n"
        f"- Status: Pending human review\n\n"
        f"A support specialist will review your case and contact you at "
        f"{wrapper.context.customer.email}."
    )
