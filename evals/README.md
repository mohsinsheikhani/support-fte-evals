# Customer Support FTE - Evaluation Framework

Comprehensive evaluation system for Customer Support Digital FTE agent using eval-driven development methodology.

## Quick Start

```bash
# Run complete Q1 baseline (all 6 code-based graders)
uv run evals/run_q1_baseline.py

# Expected: 100% pass rate (14/14 cases), ~56 seconds
# Results saved to: evals/results/q1_baseline_results.json
```

## Directory Structure

```
evals/
├── README.md                       # This file
├── dataset.json                    # Test dataset (13 cases across Q1-Q4)
├── run_q1_baseline.py             # Q1 baseline evaluation script
│
├── graders/                        # Grader implementations
│   ├── routing.py                 # Agent routing validation
│   ├── routing_flexible.py        # Ambiguous routing handling
│   ├── guardrails.py              # Input guardrail validation
│   ├── tools.py                   # Tool usage validation
│   ├── citation.py                # Knowledge citation validation
│   ├── output_guardrail.py        # Output safety validation
│   └── quality.py                 # Response quality (LLM judge)
│
├── utils/                          # Utility functions
│   ├── runner.py                  # Generic evaluation runner
│   ├── error_analyzer.py          # Programmatic error analysis
│   └── analysis.py                # Analysis utilities
│
├── tests/                          # Integration tests
│   ├── test_routing_integration.py
│   ├── test_tool_usage_integration.py
│   └── ... (one per grader)
│
├── results/                        # Evaluation results
│   ├── q1_baseline_results.json   # Current Q1 baseline (100%)
│   └── archive/                   # Historical results
│
└── docs/                           # Documentation
    ├── roadmap.md                 # Implementation roadmap
    ├── approach.md                # Eval methodology
    ├── error_analysis_template.md # Error analysis template
    ├── q1_baseline_complete.md    # Q1 completion summary
    └── graders/                   # Per-grader documentation
        ├── routing_baseline.md
        ├── tool_usage_baseline.md
        └── archive/               # Old docs
```

## Evaluation Quadrants

### Q1: Code-Based Graders (Objective) ✓ Complete
**6 graders, 14 test cases, 100% pass rate**

1. **routing_grader** (7 cases) - Validates agent selection
2. **input_guardrail_grader** (2 cases) - PII and injection detection
3. **tool_usage_grader** (2 cases) - Tool calls and business logic
4. **citation_grader** (1 case) - Knowledge base accuracy
5. **output_guardrail_grader** (1 case) - Secret leakage prevention
6. **routing_flexible_grader** (1 case) - Ambiguous routing handling

**Characteristics**:
- Deterministic, objective checks
- Ground truth available
- Fast execution (~4 sec/case)
- No human calibration needed
- Perfect for regression protection

### Q2: LLM Judges (Quality) - Coming Soon
**1-2 graders, 3+ cases**

- **response_quality_grader** - Helpfulness, tone, empathy
- Requires human calibration (≥70% agreement)
- Uses LLM-as-judge pattern

### Q3: Flexible Routing (Handled in Q1)
- Already covered by `routing_flexible_grader`

### Q4: Complex Scenarios - Coming Soon
**4 graders, 1 case**

- Multi-issue handling
- Priority assessment
- Tone calibration
- Escalation judgment

## Running Evaluations

### Full Q1 Baseline
```bash
uv run evals/run_q1_baseline.py
# Runs all 6 graders across 14 test cases
# Exit code 0 if 100%, non-zero otherwise
```

### Individual Grader Tests
```bash
# Test routing grader
uv run evals/tests/test_routing_integration.py

# Test tool usage grader
uv run evals/tests/test_tool_usage_integration.py
```

### Results
- JSON results: `evals/results/q1_baseline_results.json`
- Console output: Detailed pass/fail with scores
- Per-grader summaries and overall statistics

## Grader Standard Output

All graders return a standardized format:

```python
{
    "passed": bool,           # Overall pass/fail
    "score": float,           # 0.0-1.0 (percentage of checks passed)
    "checks": {               # Individual check results
        "check_name": bool
    },
    "failed_checks": list,    # Names of failed checks
}
```

## Development Workflow

### 1. Eval-Driven Development
- Write grader FIRST, before fixing agent
- Let failures reveal infrastructure needs
- Real agent testing, not mocks

### 2. Systematic Error Analysis
When failures occur:
1. **Component-level spreadsheet** - Break execution into spans
2. **Frequency counting** - Calculate failure_count / total_cases
3. **Prioritization formula** - Frequency × Feasibility
4. **Trace review** - Examine complete execution traces
5. **Upstream degradation** - Distinguish bad component vs bad input

See: `docs/error_analysis_template.md`

### 3. Iteration Pattern
1. Implement grader
2. Run against real agent
3. Analyze failures systematically
4. Fix infrastructure/agent
5. Re-run until 100%
6. Document baseline

## Key Principles

### State Management
- **Unique session IDs** - Prevent conversation history contamination
- **Clear global state** - Reset before each test case
- **Isolation** - Each test case independent

### Defense in Depth
Multiple protection layers:
- **Input guardrails** → Block PII/injection before processing
- **Agent routing** → Security questions escalate immediately
- **Agent behavior** → Refuse sensitive requests
- **Output guardrails** → Block secrets if agent leaks
- **Graders** → Validate all layers working

### Regression Protection
- Run baseline before/after changes
- 100% pass rate required
- Catch breakages immediately
- Document all test cases

## Implementation Status

### Week 1: Q1 Code Graders ✓ Complete
- [x] All 6 graders implemented
- [x] 100% pass rate (14/14 cases)
- [x] Baseline documented
- [x] Regression protection established

### Week 2: Q2 LLM Graders - Next
- [ ] Implement `response_quality_grader`
- [ ] Validate against human ratings (≥70% agreement)
- [ ] Run full baseline

### Week 3: Q4 Complex Graders
- [ ] Implement 4 complex scenario graders
- [ ] Validate against human ratings
- [ ] Complete final baseline

## Documentation

### Core Docs
- `docs/roadmap.md` - Implementation timeline
- `docs/approach.md` - Evaluation methodology
- `docs/q1_baseline_complete.md` - Q1 completion summary
- `docs/error_analysis_template.md` - Systematic analysis guide

### Per-Grader Docs
Each grader has detailed documentation in `docs/graders/`:
- Baseline report (what was tested, results)
- Error analysis (iterations, fixes)
- Implementation notes

### Archive
Historical documents in `docs/graders/archive/`

## Key Learnings

1. **Systematic error analysis is critical**
   - Spreadsheet method reveals exact failure locations
   - Frequency counting quantifies impact
   - Prioritization formula guides fix selection

2. **State management matters**
   - Global state contamination causes non-deterministic failures
   - Clear state before each test case
   - Unique session IDs prevent history contamination

3. **Real testing beats mocks**
   - Mocks hide infrastructure gaps
   - Real agent execution exposes unexpected interactions
   - Integration testing discovers hidden dependencies

4. **Code graders are reliable**
   - Objective, deterministic
   - Fast execution
   - No calibration needed
   - Perfect for regression

## Contact

For questions or issues with the evaluation framework, see:
- Main project: `/home/mohsin/Public/agents_factory/customer-support-fte/`
- Agent implementation: `src/agents/`
- Tools: `src/tools/`
- Guardrails: `src/guardrails/`

---

**Current Status**: Q1 Complete ✓ | Q2 Next → | Q4 Pending ⏳
