# Customer Support Digital FTE - Implementation Guide

## Project Overview

Building a Customer Support Digital FTE using OpenAI Agents SDK. The FTE handles Tier 1 support: FAQs, billing questions, basic troubleshooting.

Reference: `Capstone Building a Customer Support Digital FTE.md`

## Project Structure

```
customer-support-fte/
├── src/
│   ├── __init__.py
│   ├── models/
│   │   └── context.py          # Pydantic context model
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── customer.py         # lookup_customer
│   │   ├── billing.py          # check_billing_history, process_refund
│   │   ├── support.py          # check_support_tickets, create_escalation_ticket
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── triage.py           # Entry point, routing
│   │   ├── faq.py              # FAQ specialist
│   │   ├── billing.py          # Billing specialist
│   │   ├── technical.py        # Technical specialist
│   │   └── escalation.py       # Human handoff
│   ├── guardrails/
│   │   ├── __init__.py
│   │   ├── input.py            # PII, injection detection
│   │   └── output.py           # Secrets leakage detection
│   ├── hooks/
│   │   └── observability.py    # RunHooks implementation
│   ├── knowledge/
│   │   ├── docs/               # Policy documents for RAG
│   │   └── vectorstore.py      # FileSearchTool setup
│   └── main.py                 # Handler, session management
├── tests/                      # Manual verification scripts
├── pyproject.toml
└── .env
```

## Build Order (Bottom-Up)

| Step | Build | Verify Before Moving On |
|------|-------|------------------------|
| 1 | Context model | Can instantiate, serialize to JSON |
| 2 | Tools (mock data) | Each tool returns expected shape |
| 3 | Single specialist (FAQAgent) | Responds to FAQ questions |
| 4 | All specialists | Each handles its domain |
| 5 | Triage + Handoffs | Routes correctly to specialists |
| 6 | Guardrails | Blocks PII, injection, leakage |
| 7 | Sessions | Conversation persists across turns |
| 8 | Hooks | Logs appear with timing |
| 9 | RAG | FAQAgent cites policy documents |

## Implementation Principles

### 1. Mock Everything First
```python
# Don't connect to real databases - use hardcoded dictionaries
MOCK_CUSTOMERS = {
    "alice@example.com": {"id": "C001", "plan": "premium", "name": "Alice"}
}
```

### 2. One Agent at a Time
- Get FAQAgent working standalone before adding routing
- Test each specialist in isolation

### 3. Handoffs Last in Agent Layer
- Build all specialists first
- Then wire Triage to route between them
- Handoffs are the integration layer

### 4. Guardrails Wrap, Don't Embed
- Build agents without guardrails
- Add guardrails as decorators/wrappers after agents work

### 5. Session/Hooks are Infrastructure
- Add after core agent logic works
- They observe, don't change behavior

## Technology Stack

- **Runtime**: Python 3.11+
- **Package Manager**: uv
- **Agent Framework**: OpenAI Agents SDK
- **Models**: Pydantic for data validation
- **Session Storage**: SQLite
- **RAG**: FileSearchTool with vector stores

## Validation Checklist

### Routing
- [ ] FAQ questions route to FAQAgent
- [ ] Billing questions route to BillingAgent
- [ ] Technical questions route to TechnicalAgent
- [ ] Complex issues escalate properly

### Guardrails
- [ ] Credit card numbers are blocked
- [ ] SSN patterns are blocked
- [ ] Prompt injection attempts are blocked
- [ ] API keys don't appear in output

### Tools
- [ ] Customer lookup updates context
- [ ] Billing history returns order list
- [ ] Refunds under $100 process successfully
- [ ] Refunds over $100 trigger escalation
- [ ] Escalation tickets include priority and SLA

### Sessions
- [ ] Conversations persist across turns
- [ ] Different users have isolated sessions
- [ ] Context survives session reconnection

### Knowledge Base (RAG)
- [ ] Vector store created with policy documents
- [ ] FAQAgent retrieves relevant policies
- [ ] Responses cite sources from knowledge base
- [ ] Policy questions answered accurately

### Observability
- [ ] Agent lifecycle events are logged
- [ ] Tool calls are logged
- [ ] Handoffs are logged
- [ ] Session summary shows metrics
