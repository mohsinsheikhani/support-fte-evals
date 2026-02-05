# Q1 Baseline - Complete ✓

**Status**: All 6 Q1 code-based graders implemented and passing
**Overall Pass Rate**: 100% (14/14 test cases)
**Duration**: 55.96 seconds
**Date**: 2026-02-05

---

## Summary

All Q1 code-based graders successfully implemented with 100% pass rate across all test cases. This establishes the baseline for regression protection.

### Grader Results

| Grader | Test Cases | Pass Rate | Notes |
|--------|-----------|-----------|-------|
| routing_grader | 7/7 | 100% | Agent selection working correctly |
| input_guardrail_grader | 2/2 | 100% | PII and injection detection working |
| tool_usage_grader | 2/2 | 100% | Tool calls and business logic correct |
| citation_grader | 1/1 | 100% | Knowledge base citations accurate |
| output_guardrail_grader | 1/1 | 100% | Secret leakage prevention working |
| routing_flexible_grader | 1/1 | 100% | Ambiguous routing handled correctly |
| **TOTAL** | **14/14** | **100%** | **All Q1 requirements met** |

---

## Test Cases Covered

### Routing (7 cases)
- **Case 1**: FAQ routing (refund policy → FAQAgent)
- **Case 2**: Security escalation (data security → EscalationAgent)
- **Case 4**: Pricing questions (pricing guide → FAQAgent)
- **Case 5**: Billing complaints (double charge → BillingAgent)
- **Case 6**: Technical errors (500 error → TechnicalAgent)
- **Case 8**: Refund requests under $100 (→ BillingAgent)
- **Case 9**: Refund requests over $100 (→ BillingAgent)

### Input Guardrails (2 cases)
- **Case 3**: PII detection (credit card → blocked)
- **Case 7**: Prompt injection (instruction override → blocked)

### Tool Usage (2 cases)
- **Case 8**: Auto-approve refund ($50 → success)
- **Case 9**: Escalation required ($150 → escalation_needed)

### Citation (1 case)
- **Case 4**: Pricing knowledge (correct content, no hallucination)

### Output Guardrail (1 case)
- **Case 10**: API key leakage prevention (secrets blocked)

### Routing Flexible (1 case)
- **Case 12**: Ambiguous intent (payment + access → BillingAgent accepted)

---

## Implementation Journey

### Week 1: Q1 Code Graders

1. **routing_grader** (7 cases) - 100% pass rate (3 iterations)
   - Baseline: 29% (2/7)
   - Fixed: Agent identity, routing logic, handoff wrappers
   - Final: 100%

2. **input_guardrail_grader** (2 cases) - 100% pass rate (0 iterations)
   - Validated existing guardrail infrastructure
   - PII and injection detection working correctly

3. **tool_usage_grader** (2 cases) - 100% pass rate (3 iterations)
   - Iteration 0: Added SupportHooks infrastructure (0% → 0%)
   - Iteration 1: Fixed session contamination (0% → 50%)
   - Iteration 2: Fixed agent instructions (50% → 100%)

4. **citation_grader** (1 case) - 100% pass rate (0 iterations)
   - Validated static FAQ_KNOWLEDGE
   - No hallucination detected

5. **output_guardrail_grader** (1 case) - 100% pass rate (0 iterations)
   - Validated secrets protection
   - Defense in depth working correctly

6. **routing_flexible_grader** (1 case) - 100% pass rate (0 iterations)
   - Validated ambiguous routing handling
   - Multiple valid routes accepted

---

## Key Issues Resolved

### Issue 1: State Contamination in Baseline Script
**Problem**: Case 8 failing in baseline run (92.9% pass rate) but passing in isolation

**Root Cause**: `PROCESSED_REFUNDS` global state not cleared between test cases
- Case 8 ran twice (routing + tool_usage)
- First run added ORD-1001 to PROCESSED_REFUNDS
- Second run detected "already refunded" and returned different message
- Classification failed: expected "approved and processed", got "already refunded"

**Fix**: Clear `PROCESSED_REFUNDS` before each test case in `run_single_case()`

**Impact**: 92.9% → 100% pass rate

### Implementation Timeline
- **Discovery**: Debug script showed case 8 passing in isolation
- **Analysis**: Identified duplicate execution in baseline run
- **Root cause**: Global state persisting across test cases
- **Fix**: Added `PROCESSED_REFUNDS.clear()` at line 64 of run_q1_baseline.py
- **Validation**: Re-run confirmed 100% pass rate

---

## Architecture Patterns Validated

### 1. Eval-Driven Development
- Write grader first, let failures reveal infrastructure needs
- Systematic error analysis: spreadsheet, frequency, prioritization
- Real agent testing, not mocks

### 2. Code Graders (Q1)
- Objective, deterministic checks
- Ground truth available
- Fast execution (~4 seconds per test case)
- No human calibration needed

### 3. Grader Implementation Patterns
**Testing NEW infrastructure** → Need iterations:
- routing_grader: 3 iterations (agent identity, handoffs)
- tool_usage_grader: 3 iterations (hooks, sessions, instructions)

**Testing EXISTING features** → Often succeed immediately:
- input_guardrail_grader: 0 iterations
- citation_grader: 0 iterations
- output_guardrail_grader: 0 iterations
- routing_flexible_grader: 0 iterations

### 4. State Management
- Unique session IDs prevent conversation history contamination
- Clear global state before each test case
- Isolation critical for reliable evaluation

### 5. Defense in Depth
Multiple protection layers working:
- **Input guardrails**: Block PII and injection before processing
- **Agent routing**: Security questions → EscalationAgent
- **Agent behavior**: Refuse sensitive requests
- **Output guardrails**: Block secrets if agent leaks
- **Graders**: Validate all layers working

---

## Regression Protection Established

This baseline provides regression protection for:
- **Routing logic**: 7 test cases covering all agent types
- **Input safety**: 2 test cases for PII and injection
- **Tool execution**: 2 test cases for business logic
- **Knowledge accuracy**: 1 test case for citations
- **Output safety**: 1 test case for secret leakage
- **Flexible handling**: 1 test case for ambiguous queries

Any future changes that break these behaviors will be caught by baseline evaluation.

---

## Running the Baseline

```bash
# Run complete Q1 baseline
uv run evals/run_q1_baseline.py

# Exit code 0 if 100%, non-zero otherwise
# Results saved to: evals/q1_baseline_results.json
```

**Expected output**:
- Total test cases: 14
- Total passed: 14
- Overall pass rate: 100.0%
- Duration: ~56 seconds

---

## Next Steps

### Week 2: Q2 LLM Graders
- [ ] Implement `response_quality_grader` (3 cases)
- [ ] Validate against 20 human ratings (target: ≥70% exact match)
- [ ] Iterate on prompts if validation fails
- [ ] Run full baseline on 11 cases

### Week 3: Q4 Complex Graders
- [ ] Implement 4 complex scenario graders (case 13)
- [ ] Validate against human ratings
- [ ] Run complete baseline on all 13 cases
- [ ] Document final baseline

---

## Key Learnings

1. **Systematic error analysis is critical**
   - Component-level spreadsheet reveals exact failure locations
   - Frequency counting quantifies impact
   - Prioritization formula guides fix selection

2. **State management matters**
   - Global state contamination causes non-deterministic failures
   - Clear state before each test case for isolation
   - Unique session IDs prevent history contamination

3. **Real testing beats mocks**
   - Mocks hide real failures
   - Real agent execution exposes infrastructure gaps
   - Integration testing discovers unexpected interactions

4. **Defense in depth works**
   - Multiple protection layers (input, routing, agent, output)
   - Each layer independently validated
   - System remains secure even if one layer fails

5. **Code graders are reliable**
   - Objective, deterministic checks
   - Fast execution
   - No human calibration needed
   - Perfect for regression protection

---

## Validation

✓ All 6 Q1 graders implemented
✓ 100% pass rate across 14 test cases
✓ Systematic error analysis applied
✓ State contamination issues resolved
✓ Baseline documented for regression protection
✓ Ready to proceed to Q2 LLM graders
