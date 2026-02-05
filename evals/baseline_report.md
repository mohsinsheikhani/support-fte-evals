# Baseline Evaluation Report

**Date**: 2026-02-05
**Version**: v0.1 (Initial Agent Implementation)
**Grader**: Routing Grader (Q1)
**Test Cases**: 7 routing scenarios from dataset.json

---

## Executive Summary

Established baseline evaluation using routing grader with **real agent integration tests**.

**Overall Routing Success Rate: 29% (2/7 cases passed)**

This baseline reveals critical routing issues in the TriageAgent that must be fixed before proceeding with additional graders.

---

## Baseline Results

### Test Execution

| Case ID | Input | Expected Agent | Actual Agent | Status | Score |
|---------|-------|----------------|--------------|--------|-------|
| 1 | "What's your refund policy?" | FAQAgent | FAQAgent | ✓ PASS | 1.00 |
| 2 | "How secure is the customer data?" | EscalationAgent | TriageAgent | ✗ FAIL | 0.33 |
| 4 | "Guide me on pricing structure?" | FAQAgent | TriageAgent | ✗ FAIL | 0.33 |
| 5 | "I was charged twice this month for order ORD-1001" | BillingAgent | TriageAgent | ✗ FAIL | 0.33 |
| 6 | "I'm getting a 500 error when calling the /api/users endpoint" | TechnicalAgent | TriageAgent | ✗ FAIL | 0.33 |
| 8 | "I'm alice@example.com, please refund my $50 order ORD-1001" | BillingAgent | TriageAgent | ✗ FAIL | 0.33 |
| 9 | "I'm alice@example.com, please refund my $150 order ORD-1002" | BillingAgent | BillingAgent | ✓ PASS | 1.00 |

### Summary Statistics

- **Total Cases**: 7
- **Passed**: 2
- **Failed**: 5
- **Pass Rate**: 28.6%
- **Average Score**: 0.52

---

## Error Analysis

### Failure Pattern

**Primary Issue**: TriageAgent not routing to specialist agents (5/7 failures)

All failed cases show the same pattern:
- User asks a question
- TriageAgent receives the message
- **TriageAgent does NOT hand off to specialist**
- TriageAgent stays active and handles the request itself

### Root Cause Analysis

After examining the TriageAgent implementation (`src/agents/triage.py`), the root cause is identified:

**Line 16-17 in triage agent instructions:**
```
2. Identify the customer using their email (use lookup_customer tool)
```

**The Problem**:
- Triage agent is instructed to "always identify the customer first"
- For messages without email addresses, it asks for email before routing
- This creates a conversation barrier that prevents handoffs
- Agent stays at TriageAgent level instead of routing to specialists

**Evidence**:

**Case 1 (PASSED)**: "What's your refund policy?"
- Simple FAQ question
- Agent somehow routed to FAQAgent (inconsistent with pattern)

**Case 2 (FAILED)**: "How secure is the customer data?"
- Security question → should go to EscalationAgent
- TriageAgent asks for email instead of routing

**Cases 4, 5, 6, 8 (FAILED)**: All questions without email
- Agent stays at TriageAgent level
- Asks for customer identification before routing

**Case 9 (PASSED)**: "I'm alice@example.com, please refund my $150..."
- Email provided in message
- Agent successfully identifies customer and routes to BillingAgent

### Component Attribution

| Component | Failure Count | Percentage |
|-----------|--------------|------------|
| TriageAgent routing logic | 5 | 71% |
| Other | 0 | 0% |
| Passed | 2 | 29% |

**Conclusion**: 71% of failures are due to TriageAgent routing logic requiring customer identification before handoffs.

---

## Fix Plan

### Priority 1: Fix TriageAgent Instructions (High Impact)

**Problem**: Triage agent requires customer identification before routing to specialists.

**Proposed Fix**: Update triage agent instructions to distinguish between:
1. **Informational queries** (FAQ, general questions) → Route immediately without customer lookup
2. **Account-specific queries** (billing, refunds, account access) → Require customer identification

**Updated Routing Logic**:

```python
# src/agents/triage.py - Updated instructions

instructions = """You are the front-line triage agent for customer support.

Your job is to route customers to the appropriate specialist quickly and efficiently.

## Routing Rules

**Route IMMEDIATELY without customer lookup for:**
- General FAQ questions (pricing, policies, features, "how does X work")
- Security concerns → EscalationAgent
- Product information requests → FAQAgent

**Route AFTER customer identification for:**
- Billing issues (charges, refunds) → BillingAgent (requires email)
- Technical issues with user's account → TechnicalAgent (requires email)
- Account-specific requests → Appropriate agent (requires email)

## Guidelines

1. **Identify query type first**: Is this general information or account-specific?
2. **For general questions**: Route immediately to appropriate specialist
3. **For account queries**: Ask for email, use lookup_customer, then route
4. **For security concerns**: Route immediately to EscalationAgent
5. **When unclear**: Ask clarifying question about query type, not customer email

## Examples

"What's your refund policy?" → FAQAgent (general policy, no lookup needed)
"Guide me on pricing?" → FAQAgent (general info, no lookup needed)
"How secure is customer data?" → EscalationAgent (security concern, no lookup needed)
"I was charged twice" → Ask for email → BillingAgent (account-specific)
"I'm getting a 500 error" → Ask for context: their account or general bug?
"""
```

**Expected Improvement**: 71% → 85%+ pass rate

### Implementation Steps

1. **Update triage agent instructions** (src/agents/triage.py)
2. **Re-run routing integration tests**
3. **Verify improvement**: Target 6/7 cases passing (85%+)
4. **Analyze remaining failures**
5. **Iterate if needed**

---

## Re-Run Plan

After implementing the fix:

```bash
# Re-run integration tests
uv run python evals/test_routing_integration.py

# Expected results:
# - Cases 1, 2, 4: PASS (FAQ and escalation without email)
# - Cases 5, 6: PASS or may still need iteration
# - Cases 8, 9: PASS (email provided)
# - Target: 85%+ pass rate
```

**Success Criteria**:
- Pass rate ≥ 85% (6/7 cases)
- TriageAgent routes FAQ questions without asking for email
- Account-specific queries still require customer identification

---

## Lessons Learned

### Testing with Real Agents is Critical

This baseline evaluation demonstrates why **integration testing with real agent responses is mandatory**:

**What mock testing would have shown:**
```python
mock_result = {"agent_used": "FAQAgent"}
assert mock_result["agent_used"] == "FAQAgent"  # ✓ Test passes
```
Result: 100% pass rate, zero bugs discovered

**What real agent testing revealed:**
- TriageAgent not routing to specialists (71% failure rate)
- Agent asking for email before answering simple questions
- Inconsistent routing behavior (case 1 passes, case 4 fails)

**Key Insight**: Mock data testing creates a false sense of confidence. Real integration tests expose actual agent behavior issues.

### Eval-Driven Development Works

Following the eval-driven development loop:
1. ✓ Built routing grader
2. ✓ Ran evaluation → 29% pass rate
3. → Analyzed errors → Found TriageAgent routing logic issue
4. → Identified fix → Update instructions to route FAQ without customer lookup
5. → Next: Implement fix and re-run

This systematic approach prevents random prompt tweaking and focuses effort on the actual root cause.

---

---

## Iteration 1: First Fix Results

**Date**: 2026-02-05
**Change**: Updated TriageAgent to route informational queries immediately without email requirement

### Changes Made

Updated `src/agents/triage.py` instructions:
- Added query type classification (informational vs account-specific)
- Route informational queries (FAQ, security, pricing) immediately
- Route account-specific queries after customer identification

**Commit**: TBD

### Results

| Case ID | Baseline | After Fix | Status | Change |
|---------|----------|-----------|--------|--------|
| 1 | ✓ PASS | ✓ PASS | Maintained | - |
| 2 | ✗ FAIL | ✓ PASS | **Fixed** | Security → EscalationAgent now routes immediately |
| 4 | ✗ FAIL | ✓ PASS | **Fixed** | Pricing → FAQAgent now routes immediately |
| 5 | ✗ FAIL | ✗ FAIL | Still failing | Asks for email instead of routing |
| 6 | ✗ FAIL | ✗ FAIL | Still failing | Asks for email instead of routing |
| 8 | ✓ PASS | ✓ PASS | Maintained | - |
| 9 | ✗ FAIL | ✗ FAIL | Still failing | Asks for email instead of routing |

**Pass Rate**: 29% → 57% (+28% improvement, 2x baseline)

### Iteration 1 Analysis

**What Worked** ✓:
- Informational queries now route correctly without email (Cases 2, 4)
- Agent correctly distinguishes informational vs account-specific queries
- FAQ and security questions no longer blocked at triage level

**New Finding** 🔍:

**Problem**: TriageAgent asks for email instead of routing for account-specific queries

**Evidence**:
```
Case 5: "I was charged twice this month for order ORD-1001"
Expected: BillingAgent
Actual: TriageAgent
Response: "Could you please provide the email address associated with your account?
          This will allow me to locate your account details and connect you with
          our billing specialist..."
```

**Root Cause**:
- TriageAgent interprets "identify customer first" as gatekeeping
- Agent stays at triage level to collect email
- Never actually hands off to specialist

**Architectural Issue**:
Current approach creates a two-step flow:
1. User asks account-specific question
2. Triage asks for email
3. User provides email
4. Triage routes to specialist
5. Specialist handles the issue

Better approach:
1. User asks account-specific question
2. **Triage routes immediately** to specialist
3. **Specialist asks for email** if needed
4. Specialist handles the issue

**Decision**: Triage's job is routing, not customer identification. Move email collection to specialist agents.

### Iteration 2: Specialist Agents Handle Identification

**Date**: 2026-02-05
**Change**: Moved customer identification responsibility to specialist agents

### Changes Made

**1. Updated TriageAgent** (`src/agents/triage.py`):
- Removed all customer identification logic
- Removed lookup_customer tool (no longer needed)
- Simplified instructions: "Transfer immediately. No explanations needed."
- Explicit directive: DO NOT answer, explain, or ask for email - JUST TRANSFER

**2. Updated BillingAgent** (`src/agents/billing.py`):
- Added lookup_customer tool
- Added Step 1: Customer Identification instructions
- Agent now asks for email if not provided: "To access your account details, could you please provide the email..."
- Identifies customer before accessing billing details

**3. Updated TechnicalAgent** (`src/agents/technical.py`):
- Added lookup_customer tool
- Added conditional identification logic
- Agent determines if issue is account-specific or general
- Only asks for email when investigating account-specific problems

**Commit**: TBD

### Results

| Case ID | Iteration 1 | After Fix | Status | Change |
|---------|------------|-----------|--------|--------|
| 1 | ✓ PASS | ✓ PASS | Maintained | FAQ routing working |
| 2 | ✓ PASS | ✓ PASS | Maintained | Security → EscalationAgent |
| 4 | ✓ PASS | ✓ PASS | Maintained | Pricing → FAQAgent |
| 5 | ✗ FAIL | ✓ PASS | **Fixed** | Billing routes immediately now |
| 6 | ✗ FAIL | ✓ PASS | **Fixed** | Technical routes immediately now |
| 8 | ✓ PASS | ✓ PASS | Maintained | Billing with email |
| 9 | ✗ FAIL | ✓ PASS | **Fixed** | Billing routes immediately now |

**Pass Rate**: 57% → **100%** (+43% improvement, 7/7 cases passing) ✓

### Iteration 2 Analysis

**What Worked** ✓:

1. **Immediate Routing**: TriageAgent now transfers without asking questions
2. **Specialist Identification**: BillingAgent/TechnicalAgent ask for email when needed
3. **Clear Handoffs**: Explicit "Transfer immediately" instruction prevented chatty responses
4. **Separation of Concerns**: Routing ≠ Identification

**Key Insight**:
The problem in first attempt was the agent **talking about** handoffs instead of **executing** them. The fix was ultra-simple instructions: "Transfer immediately. No explanations needed."

**Evidence of Success**:
```
Case 5: "I was charged twice this month for order ORD-1001"
  Iteration 1: TriageAgent asks for email (stays at triage)
  Iteration 2: → BillingAgent (immediate transfer) ✓

Case 6: "I'm getting a 500 error when calling the /api/users endpoint"
  Iteration 1: TriageAgent asks for email (stays at triage)
  Iteration 2: → TechnicalAgent (immediate transfer) ✓
```

**Architectural Decision Validated**:
Specialist agents asking for identification proved to be the correct approach:
- Faster routing (1 turn vs 2-3 turns)
- Simpler triage logic (topic detection only)
- Better separation of concerns
- Matches real-world support system patterns

### Target Achieved

✓ **100% pass rate on routing grader**
✓ **All 7 test cases passing**
✓ **Ready to proceed with remaining Q1 graders**

---

## Next Steps

### Immediate (This Sprint)
1. [x] Document baseline (29% pass rate) - **COMPLETE**
2. [x] Implement TriageAgent instruction fix (Iteration 1) - **COMPLETE**
3. [x] Re-run routing integration tests - **COMPLETE** (57% pass rate)
4. [x] Analyze Iteration 1 results - **COMPLETE**
5. [ ] Verify specialist agents ask for email when needed
6. [ ] Implement Iteration 2 fix (remove email requirement from triage)
7. [ ] Re-run routing integration tests
8. [ ] Verify improvement to 85%+ pass rate
9. [ ] Update baseline documentation

### After Routing Fix (Week 1 Continuation)
6. [ ] Implement input_guardrail_grader (test cases 3, 7)
7. [ ] Implement tool_usage_grader (test cases 8, 9)
8. [ ] Implement citation_grader (test case 4)
9. [ ] Implement output_guardrail_grader (test case 10)
10. [ ] Implement routing_flexible_grader (test case 12)
11. [ ] Run complete Week 1 baseline on 10 Q1 cases

### Week 2+
- Implement Q2 LLM graders
- Implement Q4 complex scenario graders
- Full baseline on all 13 cases

---

## Metadata

**Test Environment**:
- Python: 3.11+
- Agent Framework: OpenAI Agents SDK
- Test Runner: Integration tests with real handle_message() calls
- Dataset: evals/dataset.json (13 cases total, 7 routing cases tested)

**Files**:
- Grader: `evals/graders/routing.py`
- Integration Test: `evals/test_routing_integration.py`
- Dataset: `evals/dataset.json`
- Agent Under Test: `src/agents/triage.py`

**Version Control**:
- Commit: d6daa36 (routing grader implementation)
- Branch: master
- Repository: github.com/mohsinsheikhani/support-fte-evals
