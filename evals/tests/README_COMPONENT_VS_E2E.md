# Component vs End-to-End Evaluations

This directory demonstrates both **component-level** and **end-to-end (E2E)** evaluation patterns for AI agents.

## Quick Comparison

| Aspect | E2E Eval | Component Eval |
|--------|----------|----------------|
| **What it tests** | Full agent pipeline | Single isolated component |
| **Speed** | Slow (5-60 seconds) | Fast (1-10 seconds) |
| **Purpose** | "Should we ship?" | "What needs fixing?" |
| **Signal clarity** | Noisy (multiple sources) | Clear (isolated) |
| **Best for** | Regression, monitoring | Debugging, tuning |
| **Example** | `test_routing_integration.py` | `component_routing_test.py` |

---

## End-to-End Evaluations

### Files
- `test_routing_integration.py` - Full agent execution with routing check
- `test_tool_usage_integration.py` - Full agent execution with tool verification
- `test_response_quality_integration.py` - Full agent with LLM judge
- `test_citation_integration.py` - Full agent with knowledge citation check
- All other `test_*_integration.py` files

### What They Do
```
User Input → [Full Agent Pipeline] → Final Output → [Grader]
             ↑                                       ↑
             Triage → Specialist → Tools → Response  Check specific behavior
```

**Example (Routing E2E)**:
```python
# Run FULL system
result = await handle_message("Guide me on pricing structure?")

# Check which agent responded
assert result["agent_used"] == "FAQAgent"
```

### Characteristics
✅ **Realistic** - Tests how users interact with the system
✅ **Integration** - Catches issues between components
✅ **Regression protection** - Verifies full system behavior
⚠️ **Slow** - Full agent execution takes time
⚠️ **Noisy** - Failures could come from any component
⚠️ **Expensive** - Multiple LLM calls per test

### When to Use
- ✅ Establishing baselines
- ✅ Regression testing before deployment
- ✅ Monitoring production quality
- ✅ Final verification after component fixes
- ❌ Fast iteration during debugging
- ❌ Tuning prompts or logic

---

## Component Evaluations

### Files
- `component_routing_test.py` - Isolated routing decision logic
- `component_llm_judge_test.py` - Isolated LLM judge evaluation

### What They Do
```
Known-Good Input → [Single Component] → Output → Compare to Expected
                   ↑                              ↑
                   ONLY routing logic             Clear pass/fail
                   or ONLY judge logic
```

**Example (Routing Component)**:
```python
# Test ONLY routing decision (no full execution)
routed_agent = await test_routing_decision("Guide me on pricing structure?")

# Direct comparison
assert routed_agent == "FAQAgent"
```

### Characteristics
✅ **Fast** - No full pipeline, just one component
✅ **Clear signal** - Failures isolate to tested component
✅ **Cheap** - Minimal LLM calls
✅ **Debuggable** - Direct visibility into component behavior
⚠️ **Isolation** - Doesn't test component interactions
⚠️ **Gold standard needed** - Requires expert-verified test cases

### When to Use
- ✅ Fast iteration during development
- ✅ Prompt tuning for specific components
- ✅ Debugging after E2E failures
- ✅ Comparing different implementations
- ❌ Verifying full system integration
- ❌ Catching multi-component issues

---

## The Recommended Workflow (from agent-evals skill)

### 1. Start with E2E Baseline
```bash
# Establish overall quality
uv run evals/tests/test_routing_integration.py
# Result: 67% pass rate
```

### 2. Analyze Failures Systematically
```
Component-Level Spreadsheet:
| Case | Triage: Route | Specialist: Tool | Output: Text |
|------|---------------|------------------|--------------|
| 4    | ✗ Wrong agent | Never reached    | Never reached|
```

Identifies: Routing component is the problem.

### 3. Create Component Eval for Problem Area
```bash
# Fast iteration on routing logic
uv run evals/tests/component_routing_test.py
# Result: Isolated routing test with clear signal
```

### 4. Iterate Quickly on Component
```bash
# Try fix v1
uv run evals/tests/component_routing_test.py  # 1 second
# Try fix v2
uv run evals/tests/component_routing_test.py  # 1 second
# Try fix v3
uv run evals/tests/component_routing_test.py  # 1 second

# vs E2E iteration
uv run evals/tests/test_routing_integration.py  # 60 seconds each
```

### 5. Verify with E2E
```bash
# Confirm system-level improvement
uv run evals/tests/test_routing_integration.py
# Result: 100% pass rate ✓
```

---

## Examples in This Codebase

### Example 1: Routing Logic

**E2E Test** (`test_routing_integration.py`):
- Runs full agent with user input
- Checks which agent responded
- Slow but realistic
- Used for: Baseline, regression testing

**Component Test** (`component_routing_test.py`):
- Tests ONLY routing decision
- Provides known-good inputs
- Fast iteration (< 1 second)
- Used for: Debugging routing logic, tuning routing prompts

### Example 2: LLM Judge

**E2E Test** (`test_response_quality_integration.py`):
- Runs full agent → gets response → judge evaluates
- Tests complete evaluation pipeline
- Slow (agent + judge)
- Used for: Baseline, final verification

**Component Test** (`component_llm_judge_test.py`):
- Provides known-good/bad responses directly to judge
- Tests ONLY judge evaluation logic
- Fast (just judge, no agent)
- Used for: Tuning judge prompts, calibrating against expert judgment

---

## Real-World Impact: Response Quality Grader

### Without Component Eval (What We Did)
```
Iteration 0: Run E2E (60s) → 67% pass → Analysis (45min)
Iteration 1: Run E2E (60s) → 100% pass ✓

Total: 120 seconds testing + 45 minutes analysis
Iterations: 2 (lucky - found fix quickly)
```

### With Component Eval (Ideal)
```
Iteration 0: Run E2E (60s) → 67% pass → Analysis (45min)
Create component eval (15min)

Fast iteration on component:
- Try fix v1 → Component test (5s) → 80% pass
- Try fix v2 → Component test (5s) → 90% pass
- Try fix v3 → Component test (5s) → 100% pass ✓

Iteration 1: Run E2E (60s) → 100% pass ✓

Total: 95 seconds testing + 45 minutes analysis + 15 min component setup
Iterations: 4 component + 1 E2E (more thorough exploration)
```

Savings increase with iteration count:
- 5 iterations: E2E = 300s, Component = 40s (7.5x faster)
- 10 iterations: E2E = 600s, Component = 65s (9.2x faster)

---

## Key Insights

### E2E Finds Problems
- Establishes baseline quality
- Catches integration issues
- Validates full system behavior
- **But**: Slow, noisy, expensive

### Component Evals Fix Problems
- Fast iteration cycles
- Clear signal (isolated component)
- Cheap (minimal LLM calls)
- **But**: Requires gold standard test cases

### Use Both Together
1. **E2E baseline** - Find problems
2. **Error analysis** - Isolate root cause
3. **Component eval** - Fast iteration on fix
4. **E2E verification** - Confirm system improvement

This gives:
- ✅ Realism (E2E testing)
- ✅ Speed (component iteration)
- ✅ Confidence (E2E verification)

---

## Running the Tests

### E2E Tests
```bash
# Individual E2E tests
uv run evals/tests/test_routing_integration.py
uv run evals/tests/test_response_quality_integration.py

# All E2E tests via baseline
uv run evals/run_q1_baseline.py
```

### Component Tests
```bash
# Routing component eval
uv run evals/tests/component_routing_test.py

# LLM judge component eval
uv run evals/tests/component_llm_judge_test.py
```

---

## What This Framework Demonstrates

This evaluation framework showcases:

1. **E2E Testing**
   - Full system integration tests
   - Realistic user scenarios
   - Regression protection

2. **Component Testing**
   - Isolated unit-like tests for AI components
   - Fast iteration capability
   - Clear signal for debugging

3. **Systematic Error Analysis**
   - Component-level spreadsheet method (from agent-evals skill)
   - Frequency counting
   - Prioritization formulas

4. **Hybrid Workflow**
   - E2E for baselines and verification
   - Component for debugging and tuning
   - Best of both approaches

5. **Production-Ready Practices**
   - Comprehensive test coverage (14 E2E + 14 component cases)
   - Automated regression protection
   - Clear documentation and rationale

---

## Methodology Source

All evaluation patterns and workflows in this framework come from the **agent-evals skill**, developed iteratively through hands-on practice. The skill provides:
- Evaluation quadrant classification (Q1-Q4)
- Systematic error analysis methodology
- Component vs E2E evaluation strategies
- LLM judge calibration approaches
- Baseline establishment for regression protection

To use the skill: `/agent-evals` in Claude Code

---

## References

- **E2E Tests**: All `test_*_integration.py` files
- **Component Tests**: `component_*.py` files
- **Error Analysis Examples**: `evals/docs/graders/*_error_analysis.md`
- **Framework Documentation**: `evals/README.md`
- **Methodology**: agent-evals skill (invoke with `/agent-evals`)
