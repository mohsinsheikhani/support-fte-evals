# Error Analysis Template - Systematic Methodology

**Purpose**: This template ensures we apply systematic error analysis for every grader implementation, following the eval-driven development methodology.

**When to Use**: After EVERY test run, even if all tests pass.

---

## Phase 1: Data Collection

### 1.1 Raw Test Results Table

**Copy this template and fill in:**

| Case ID | Input (first 50 chars) | Expected Output | Actual Output | Status | Observed Behavior |
|---------|----------------------|-----------------|---------------|--------|-------------------|
| X | ... | ... | ... | PASS/FAIL | ... |
| X | ... | ... | ... | PASS/FAIL | ... |

**Summary Stats:**
- Total Cases: __
- Passed: __ (___%)
- Failed: __ (___%)
- Average Score: ___

---

## Phase 2: Component-Level Attribution (Spreadsheet Method)

### 2.1 Identify Execution Chain Components

For this grader, break down the execution into distinct components:

**Example for routing:**
- Component A: Triage receives message
- Component B: Triage classifies query type
- Component C: Triage executes handoff
- Component D: Specialist receives handoff
- Component E: Specialist responds

**For YOUR grader, list components:**
1. Component A: ____________________
2. Component B: ____________________
3. Component C: ____________________
4. Component D: ____________________
5. Component E: ____________________

### 2.2 Component Failure Spreadsheet

**For each failed case, identify WHERE in the chain it failed:**

| Case | Comp A | Comp B | Comp C | Comp D | Comp E | Error Location | Root Cause |
|------|--------|--------|--------|--------|--------|----------------|------------|
| 1 | ✓ | ✓ | ✗ | - | - | Comp C | ... |
| 2 | ✓ | ✗ | - | - | - | Comp B | ... |

**Legend:**
- ✓ = Component succeeded
- ✗ = Component failed (this is where error occurred)
- - = Not reached (upstream failure prevented execution)

---

## Phase 3: Frequency Counting

### 3.1 Count Failures by Component

| Component | Failure Count | Total Cases | Frequency | Description |
|-----------|--------------|-------------|-----------|-------------|
| Comp A | __ | __ | __% | ... |
| Comp B | __ | __ | __% | ... |
| Comp C | __ | __ | __% | ... |
| **TOTALS** | __ | __ | __% | |

### 3.2 Identify Top 3 Failure Sources

1. **Primary**: _____________ (__% of failures)
2. **Secondary**: _____________ (__% of failures)
3. **Tertiary**: _____________ (__% of failures)

**Single Root Cause?**
- [ ] YES - Single component accounts for ≥60% of failures
- [ ] NO - Failures distributed across multiple components

---

## Phase 4: Root Cause Analysis

### 4.1 For Each Top Failure Source

**Component**: ______________

**Failure Pattern**: (Describe what's happening)
```
Example:
Agent is asking for email instead of routing.
Pattern appears in cases: 2, 4, 5, 6
All cases lack email in initial message.
```

**Evidence**: (Paste actual agent responses showing the pattern)
```
Case 2 response:
"Could you please provide your email..."

Case 4 response:
"To assist you, I'll need your email..."
```

**Root Cause Hypothesis**: (Why is this happening?)
```
Example:
Agent instruction line 16: "Identify the customer using their email"
Agent interprets this as a blocking requirement, not optional step.
```

**Trace Verification**: (Did you examine the actual execution trace?)
- [ ] YES - Examined trace, root cause confirmed
- [ ] NO - Hypothesis based on output only

---

## Phase 5: Fix Option Brainstorming

### 5.1 List ALL Potential Fixes

| Fix Option | Description | Addresses Root Cause? | Est. Time | Feasibility (0-1) |
|------------|-------------|----------------------|-----------|-------------------|
| 1. | ... | YES/NO | Xh | 0.X |
| 2. | ... | YES/NO | Xh | 0.X |
| 3. | ... | YES/NO | Xh | 0.X |

**Feasibility Scale:**
- 1.0 = Trivial (config, 5 min)
- 0.9 = Easy (prompt, 15-30 min)
- 0.7 = Moderate (small code change, 1-2h)
- 0.5 = Hard (architecture change, 4-8h)
- 0.3 = Very hard (research needed, days)
- 0.1 = Extremely hard (fundamental redesign, weeks)

### 5.2 Calculate Priority Scores

**Priority = Frequency × Feasibility**

| Fix Option | Frequency | Feasibility | Priority | Rank |
|------------|-----------|-------------|----------|------|
| 1. | __% | 0.X | 0.XX | #X |
| 2. | __% | 0.X | 0.XX | #X |
| 3. | __% | 0.X | 0.XX | #X |

### 5.3 Decision Matrix

**Highest Priority**: _____________ (Score: ____)

**But should we choose it?**

Consider:
- [ ] Does it address root cause (not just symptoms)?
- [ ] Is it sustainable long-term?
- [ ] Does it improve architecture vs. adding technical debt?
- [ ] Are there cascading benefits beyond this grader?

**Selected Fix**: _____________

**Rationale**: (Why this fix over others?)
```
Example:
Chose option #2 (priority 0.34) over option #1 (priority 0.43)
because option #1 treats symptoms (add email to tests) while
option #2 fixes root cause (architectural separation of routing vs identity).
Long-term benefit outweighs short-term ease.
```

---

## Phase 6: Implementation Plan

### 6.1 Detailed Steps

**Fix**: _____________

**Steps**:
1. [ ] Update file X: Change Y to Z
2. [ ] Add file A: Implement B
3. [ ] Test locally: Run command C
4. [ ] Expected result: D

**Estimated Time**: __ hours

**Expected Improvement**:
- Current pass rate: __%
- Expected pass rate: __%
- Expected improvement: +__%

### 6.2 Validation Criteria

**Success Criteria** (Before marking iteration complete):
- [ ] Pass rate improved by ≥__%
- [ ] Top failure component reduced by ≥__%
- [ ] No new failure patterns introduced
- [ ] Re-ran full test suite (not just failed cases)

---

## Phase 7: Post-Implementation Analysis

### 7.1 Results Comparison

| Metric | Before Fix | After Fix | Change |
|--------|------------|-----------|--------|
| Pass Rate | __% | __% | +__% |
| Primary Failure | __% | __% | -__% |
| Secondary Failure | __% | __% | -__% |
| Avg Score | 0.XX | 0.XX | +0.XX |

### 7.2 New Spreadsheet Analysis

**Did failures move to different components?**
- [ ] NO - Same components, lower frequency
- [ ] YES - New failure pattern emerged at: _________

**Re-run frequency counting for new failures:**

| Component | New Failure Count | Frequency |
|-----------|------------------|-----------|
| ... | ... | ... |

### 7.3 Iteration Decision

**Current Status**:
- Pass Rate: __%
- Target: __%
- Gap: __%

**Next Action**:
- [ ] **Target achieved** → Document final results, move to next grader
- [ ] **Continue iterating** → Return to Phase 2 with new data
- [ ] **Reassess approach** → If 3+ iterations with <5% improvement each, consider architectural change

---

## Phase 8: Documentation & Lessons

### 8.1 Key Insights

**What did systematic analysis reveal that intuition missed?**
```
Example:
Frequency counting showed 71% of failures in single component.
Without counting, would have guessed "around half" and might
have split effort across multiple components.
```

**How did prioritization formula affect decision?**
```
Example:
Formula suggested fix A (0.43) but we chose fix B (0.34)
because root cause analysis showed A was symptomatic.
This prevented technical debt.
```

### 8.2 Process Adherence Checklist

**Did we follow the systematic method?**
- [ ] Created component spreadsheet (not just eyeballed)
- [ ] Counted failures systematically (not guessed)
- [ ] Calculated priorities with formula (not gut feel)
- [ ] Examined actual traces (not assumed root cause)
- [ ] Documented BEFORE implementing (not after)
- [ ] Re-ran full suite (not just failed cases)

**Time Investment:**
- Analysis time: __ minutes
- Implementation time: __ minutes
- Total: __ minutes
- **Wasted effort on wrong components**: __ minutes (target: 0)

---

## Quick Reference Checklist

**Use this for every test run:**

1. [ ] Fill in raw results table
2. [ ] Create component spreadsheet
3. [ ] Count failures by component
4. [ ] Identify top 3 failure sources
5. [ ] Analyze root causes with traces
6. [ ] List fix options with feasibility
7. [ ] Calculate priority scores
8. [ ] Select fix with rationale
9. [ ] Document implementation plan
10. [ ] Implement fix
11. [ ] Re-run full test suite
12. [ ] Compare before/after
13. [ ] Document insights
14. [ ] Decide: iterate or move on

**Time Required**: 25-30 minutes of analysis per iteration

**Payoff**: Prevents hours/days of fixing wrong components

---

## Example: Filled Template

See `routing_error_analysis.md` for complete example of this template applied to routing grader iterations.
