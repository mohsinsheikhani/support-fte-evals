"""Customer lookup tools."""

from agents import function_tool, RunContextWrapper
from src.models.context import SupportContext

# Mock customer database
MOCK_CUSTOMERS = {
    "alice@example.com": {
        "id": "C001",
        "name": "Alice Smith",
        "email": "alice@example.com",
        "plan": "premium",
    },
    "bob@example.com": {
        "id": "C002",
        "name": "Bob Johnson",
        "email": "bob@example.com",
        "plan": "free",
    },
    "carol@example.com": {
        "id": "C003",
        "name": "Carol Williams",
        "email": "carol@example.com",
        "plan": "enterprise",
    },
}


@function_tool
def lookup_customer(
    wrapper: RunContextWrapper[SupportContext],
    email: str
) -> str:
    """Find a customer by their email address.

    Args:
        email: The customer's email address to look up.

    Returns:
        Customer information if found, or a not found message.
    """
    customer_data = MOCK_CUSTOMERS.get(email.lower().strip())

    if customer_data:
        # Update context with customer info
        wrapper.context.customer.id = customer_data["id"]
        wrapper.context.customer.email = customer_data["email"]
        wrapper.context.customer.name = customer_data["name"]
        wrapper.context.customer.plan = customer_data["plan"]

        return (
            f"Customer found:\n"
            f"- ID: {customer_data['id']}\n"
            f"- Name: {customer_data['name']}\n"
            f"- Email: {customer_data['email']}\n"
            f"- Plan: {customer_data['plan']}"
        )
    else:
        return f"No customer found with email: {email}"
