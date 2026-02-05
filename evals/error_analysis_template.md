# Error Analysis Template - Systematic Methodology

**Purpose**: This template ensures we apply systematic error analysis for every grader implementation, following the eval-driven development methodology.

**When to Use**: After EVERY test run, even if all tests pass.

---

## Phase 1: Data Collection

### 1.1 Create AnalyzedCase Objects

**Use programmatic error analyzer instead of manual tables:**

```python
from evals.error_analyzer import AnalyzedCase, analyze_failures, prioritize_fixes

# Create analyzed cases for each test
cases = [
    AnalyzedCase(
        case_id="1",
        error_location="none",  # "none" for passed, "Component.span" for failed
        trace={},  # Full execution trace
        passed=True,
        input_text="...",
        expected_output="...",
        actual_output="..."
    ),
    AnalyzedCase(
        case_id="2",
        error_location="TriageAgent.routing",
        trace={"span_1": {...}, "span_2": {...}},
        passed=False,
        upstream_issue=False,  # Set True if failure due to upstream degradation
        root_cause="Agent asks for email before routing",
        input_text="...",
        expected_output="...",
        actual_output="..."
    ),
    # ... more cases
]

# Automatically generate error report
report = analyze_failures(cases)

print(f"Pass Rate: {report['pass_rate']:.1%}")
print(f"Top Priority: {report['top_priority']}")
```

### 1.2 Raw Test Results Table (Auto-Generated)

**Manual table (fallback if not using error_analyzer.py):**

| Case ID | Input (first 50 chars) | Expected Output | Actual Output | Status | Observed Behavior |
|---------|----------------------|-----------------|---------------|--------|-------------------|
| X | ... | ... | ... | PASS/FAIL | ... |
| X | ... | ... | ... | PASS/FAIL | ... |

**Summary Stats** (Auto-generated from `analyze_failures()`):
- Total Cases: `report['total_cases']`
- Passed: `report['passed']` (`report['pass_rate']`)
- Failed: `report['failures']` (`report['failure_rate']`)
- Top Priority: `report['top_priority']`

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

## Phase 2.5: Trace Review (Understanding Failure Chains)

**CRITICAL**: Examine complete traces for each failed case, not just final outputs.

> "A component might fail frequently because it receives degraded input upstream, not because it's broken. Attribution without investigation produces false improvements."

### 2.5.1 Capture Full Traces for Failed Cases

**For EACH failed case, document the complete execution trace:**

**Case ID**: __

**Input**: (Original user input)

**Complete Trace** (all intermediate outputs):

```
Span 1 - [Component A Name]:
  Input received: ...
  Processing performed: ...
  Output produced: ...
  Status: ✓ Success / ✗ Failed

Span 2 - [Component B Name]:
  Input received: ... (from Span 1)
  Processing performed: ...
  Output produced: ...
  Status: ✓ Success / ✗ Failed

Span 3 - [Component C Name]:
  Input received: ... (from Span 2)
  Processing performed: ...
  Output produced: ...
  Status: ✗ FAILURE OCCURRED HERE
  Error: ...

NEVER REACHED:
Span 4 - [Component D Name]: Not executed
Span 5 - [Component E Name]: Not executed
```

### 2.5.2 Analyze Failure Chain

**For the failing span, examine:**

1. **Input Quality**: Was the input to this span correct/valid?
   - [ ] Good - Input was valid
   - [ ] Degraded - Input was malformed/incorrect from upstream

2. **Processing Logic**: Did the component process correctly given its input?
   - [ ] Correct - Component handled input appropriately
   - [ ] Incorrect - Component logic is flawed

3. **Output Problem**: What specifically was wrong with the output?
   ```
   Expected: ...
   Actual: ...
   Gap: ...
   ```

**Example:**
```
Case 5: "I was charged twice for order ORD-1001"

Span 2 - Triage Decision Making:
  Input received: User message "I was charged twice..."
  Processing performed: Checked instructions "Identify customer using email"
  Output produced: Decision = "Ask for email before routing"
  Status: ✗ WRONG DECISION

  Analysis:
  - Input Quality: ✓ Good (valid user message)
  - Processing Logic: ✗ Incorrect (instructions caused bad decision)
  - Output Problem: Should output "Route to BillingAgent",
                    instead output "Ask for email"

  → Component is following instructions, but INSTRUCTIONS ARE WRONG
  → Fix instructions, not the component logic
```

---

## Phase 2.6: Upstream Degradation Analysis

**CRITICAL**: Distinguish between "component is broken" vs "component received bad input"

### 2.6.1 Upstream Dependency Table

**For each failing component, check if upstream caused the failure:**

| Failed Component | Upstream Component | Input Quality | Upstream Caused Failure? | Evidence |
|-----------------|-------------------|---------------|-------------------------|----------|
| Comp B | Comp A | Good/Bad | YES/NO | ... |
| Comp C | Comp B | Good/Bad | YES/NO | ... |

### 2.6.2 Root Cause Attribution Decision

**For each failed component:**

**Component**: ______________

**Received input from**: ______________

**Input quality check:**
- [ ] **GOOD** - Upstream provided correct/valid input
  - → Component itself is broken, fix this component
- [ ] **BAD** - Upstream provided incorrect/invalid input
  - → Component is working correctly, fix upstream instead

**Example:**
```
Failed Component: BillingAgent handoff execution
Upstream: TriageAgent decision making
Input Quality: BAD
  - TriageAgent decided "ask for email"
  - Should have decided "execute handoff to BillingAgent"
Upstream Caused Failure: YES

Decision: Don't fix handoff execution (it's fine)
          Fix TriageAgent decision logic instead

This prevents FALSE FIX:
  ✗ Spending hours "fixing" handoff execution that works perfectly
  ✓ Correctly identify decision logic as root cause
```

---

## Phase 3: Frequency Counting (Automated)

### 3.1 Generate Failure Report

**Use `analyze_failures()` to auto-generate frequency counts:**

```python
report = analyze_failures(cases)

# Automatically generated breakdown
for component, data in report['breakdown'].items():
    print(f"{component}: {data['count']} failures ({data['percentage']:.1f}%)")

# Output example:
# TriageAgent.identity_check: 5 failures (100.0%)
```

### 3.2 Frequency Table (Auto-Generated)

| Component | Failure Count | Frequency (of failures) | Frequency (of total) |
|-----------|--------------|------------------------|---------------------|
| _Auto-populated from `report['breakdown']`_ | | | |

**From error_analyzer output:**
```python
{
  "breakdown": {
    "TriageAgent.identity_check": {
      "count": 5,
      "percentage": 100.0,  # Of failures
      "percentage_of_total": 71.4  # Of all cases
    }
  }
}
```

### 3.3 Identify Top Failure Sources (Auto-Generated)

**Top Priority**: `report['top_priority']`

**Single Root Cause?**
```python
top_component_pct = list(report['breakdown'].values())[0]['percentage']
single_root_cause = top_component_pct >= 60.0
```

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
- [ ] YES - Examined complete trace with all spans (Phase 2.5)
- [ ] NO - Hypothesis based on output only ⚠️ RISKY

**Upstream Check**: (Did you verify this isn't an upstream issue?)
- [ ] YES - Checked upstream components, issue is in THIS component (Phase 2.6)
- [ ] NO - Haven't verified upstream ⚠️ MIGHT BE FALSE ATTRIBUTION

---

## Phase 4.2: Structured Trace Data (Optional but Recommended)

**For programmatic analysis, structure traces as:**

```python
from dataclasses import dataclass

@dataclass
class AnalyzedCase:
    case_id: str
    error_location: str  # Which span failed
    trace: dict          # Full execution trace with all spans
    upstream_issue: bool # True if failure due to upstream degradation
    root_cause: str      # Human-readable root cause description

# Example:
case_5 = AnalyzedCase(
    case_id="5",
    error_location="TriageAgent.decision_making",
    trace={
        "span_1": {"input": "...", "output": "..."},
        "span_2": {"input": "...", "output": "...", "failed": True},
    },
    upstream_issue=False,  # Instructions are wrong, not upstream data
    root_cause="Triage instructions require email before routing"
)
```

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

### 5.2 Calculate Priority Scores (Automated)

**Priority = Frequency × Feasibility**

**Use `prioritize_fixes()` to auto-calculate priorities:**

```python
# Define feasibility for each component
feasibility = {
    "TriageAgent.identity_check": 0.9,  # Easy - prompt change
    "BillingAgent.refund_logic": 0.5,   # Hard - business logic change
}

# Automatically calculate and rank priorities
priorities = prioritize_fixes(report, feasibility)

# Output is sorted by priority score (highest first)
for i, p in enumerate(priorities, 1):
    print(f"#{i} {p['component']}: {p['priority_score']:.3f}")

# Output example:
# #1 TriageAgent.identity_check: 0.900
```

**Priority Table (Auto-Generated)**:

| Rank | Component | Frequency | Feasibility | Priority Score |
|------|-----------|-----------|-------------|----------------|
| _Auto-populated from `prioritize_fixes()` output_ | | | | |

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
- [ ] **Captured complete traces with all spans (not just outputs)**
- [ ] **Performed upstream degradation analysis (not assumed component is broken)**
- [ ] Calculated priorities with formula (not gut feel)
- [ ] Examined actual traces (not assumed root cause)
- [ ] Documented BEFORE implementing (not after)
- [ ] Re-ran full suite (not just failed cases)

**Most Common Mistakes to Avoid:**
- ❌ Skipping trace review → Risk false attribution
- ❌ Not checking upstream → Fix working component instead of broken upstream
- ❌ Looking only at final output → Miss where error actually originated
- ❌ Assuming component is broken → Might be following bad instructions/receiving bad input

**Validation Questions:**
1. Did you examine the **complete trace** for each failed case? (Not just "it failed")
2. Did you verify **input quality** to failing component? (Upstream degradation check)
3. Can you point to **exact span** where error occurred? (Specific component, not vague guess)
4. Do you have **evidence** from traces? (Not just intuition)

**Time Investment:**
- Analysis time: __ minutes
- Implementation time: __ minutes
- Total: __ minutes
- **Wasted effort on wrong components**: __ minutes (target: 0)
- **False attribution prevented**: __ cases (due to upstream analysis)

---

## Quick Reference Checklist

**Use this for every test run:**

### Phase 1-2: Attribution
1. [ ] Fill in raw results table
2. [ ] Create component spreadsheet
3. [ ] Count failures by component
4. [ ] Identify top 3 failure sources

### Phase 2.5-2.6: **CRITICAL - Trace Analysis**
5. [ ] **Capture complete traces for ALL failed cases**
6. [ ] **Document each span: input → processing → output**
7. [ ] **Analyze failure chains: which span actually failed?**
8. [ ] **Upstream degradation check: bad input or bad component?**

### Phase 3-5: Prioritization & Fixing
9. [ ] Analyze root causes (WITH trace evidence)
10. [ ] List fix options with feasibility
11. [ ] Calculate priority scores
12. [ ] Select fix with rationale (root cause vs symptoms)
13. [ ] Document implementation plan

### Phase 6-8: Implementation & Validation
14. [ ] Implement fix
15. [ ] Re-run full test suite
16. [ ] Compare before/after with new traces
17. [ ] Document insights
18. [ ] Decide: iterate or move on

**CRITICAL STEPS (Cannot Skip):**
- ✅ Step 5-8: Trace analysis and upstream check
- ✅ Without traces: Risk fixing wrong component (false attribution)

**Payoff**: Prevents hours/days of fixing wrong components

---

## Example: Filled Template

See `routing_error_analysis.md` for complete example of this template applied to routing grader iterations.
