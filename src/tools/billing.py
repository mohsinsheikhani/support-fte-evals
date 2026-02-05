"""Billing and refund tools."""

from datetime import datetime, timedelta
from agents import function_tool, RunContextWrapper
from src.models.context import SupportContext

# Mock order database
MOCK_ORDERS = {
    "C001": [  # Alice
        {
            "order_id": "ORD-1001",
            "date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
            "amount": 50.00,  # Under $100 threshold for auto-refund
            "description": "Add-on Feature",
            "status": "completed",
        },
        {
            "order_id": "ORD-1002",
            "date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
            "amount": 150.00,  # Over $100 threshold - requires escalation
            "description": "Premium Upgrade",
            "status": "completed",
        },
        {
            "order_id": "ORD-1003",
            "date": (datetime.now() - timedelta(days=35)).strftime("%Y-%m-%d"),
            "amount": 99.00,
            "description": "Premium Monthly Subscription",
            "status": "completed",
        },
    ],
    "C002": [  # Bob
        {
            "order_id": "ORD-2001",
            "date": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
            "amount": 29.00,
            "description": "Add-on Feature Pack",
            "status": "completed",
        },
    ],
    "C003": [  # Carol
        {
            "order_id": "ORD-3001",
            "date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
            "amount": 499.00,
            "description": "Enterprise Annual Subscription",
            "status": "completed",
        },
    ],
}

# Track processed refunds
PROCESSED_REFUNDS: set[str] = set()


@function_tool
def check_billing_history(
    wrapper: RunContextWrapper[SupportContext],
) -> str:
    """Get the billing history for the current customer.

    Returns a list of recent orders for the identified customer.
    Customer must be identified first using lookup_customer.

    Returns:
        List of orders or an error if customer not identified.
    """
    customer_id = wrapper.context.customer.id

    if not customer_id:
        return "Error: Customer not identified. Please look up the customer first."

    orders = MOCK_ORDERS.get(customer_id, [])

    if not orders:
        return f"No billing history found for customer {customer_id}."

    lines = [f"Billing history for {wrapper.context.customer.name}:\n"]
    for order in orders:
        lines.append(
            f"- {order['order_id']}: ${order['amount']:.2f} on {order['date']}\n"
            f"  {order['description']} ({order['status']})"
        )

    return "\n".join(lines)


@function_tool
def process_refund(
    wrapper: RunContextWrapper[SupportContext],
    order_id: str,
    reason: str,
) -> str:
    """Process a refund for an order.

    Refunds under $100 are processed automatically.
    Refunds $100 or more require escalation to a human agent.

    Args:
        order_id: The order ID to refund (e.g., "ORD-1001").
        reason: The reason for the refund request.

    Returns:
        Confirmation of refund or escalation requirement.
    """
    customer_id = wrapper.context.customer.id

    if not customer_id:
        return "Error: Customer not identified. Please look up the customer first."

    # Check if already refunded
    if order_id in PROCESSED_REFUNDS:
        return f"Order {order_id} has already been refunded."

    # Find the order
    orders = MOCK_ORDERS.get(customer_id, [])
    order = next((o for o in orders if o["order_id"] == order_id), None)

    if not order:
        return f"Order {order_id} not found for this customer."

    amount = order["amount"]

    # Auto-approve refunds under $100
    if amount < 100:
        PROCESSED_REFUNDS.add(order_id)
        return (
            f"Refund approved and processed!\n"
            f"- Order: {order_id}\n"
            f"- Amount: ${amount:.2f}\n"
            f"- Reason: {reason}\n"
            f"- Status: Refund will appear in 3-5 business days."
        )
    else:
        return (
            f"Refund requires escalation.\n"
            f"- Order: {order_id}\n"
            f"- Amount: ${amount:.2f}\n"
            f"- Reason: {reason}\n"
            f"- Note: Refunds of $100 or more require human approval. "
            f"Please escalate this case."
        )
