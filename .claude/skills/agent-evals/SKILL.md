---
name: agent-evals
description: Design and implement evaluation frameworks for AI agents. Use when testing agent reasoning quality, building graders, performing error analysis, or establishing regression protection.
---

# Agent Evaluations Skill

## Core Thesis

"One of the biggest predictors for whether someone is able to build agentic workflows really well is whether or not they're able to drive a really disciplined evaluation process." - Andrew Ng

## When to Activate

Use this skill when:
- Building quality checks for any AI agent
- Designing evaluation datasets
- Creating graders to define "good" automatically
- Performing error analysis to find failure patterns
- Setting up regression protection for agent changes
- Debating whether a prompt or config change actually improved things
- Considering model switches and need to quantify quality tradeoffs
- Stakeholders disagree about whether the agent is "good enough"
- Receiving user complaints you can't systematically reproduce
- Deciding which agent component to improve next

## Key Concepts

### Evals vs TDD

| Aspect | TDD (Code Testing) | Evals (Agent Evaluation) |
|--------|-------------------|-------------------------|
| **Core Question** | "Does it work?" | "Did it decide correctly?" |
| **Tests** | Does function return correct output? | Did agent make the right decision? |
| **Outcome** | PASS or FAIL (deterministic) | Scores (probabilistic) |
| **Correct Answers** | Exactly one | Range of acceptable responses |
| **Analogy** | Testing if calculator works | Testing if student knows WHEN to use multiplication |

**Key Insight**: TDD validates code correctness with deterministic PASS/FAIL. Evals measure reasoning quality with probabilistic scores. The fundamental difference isn't complexity—it's whether judgment is involved.

#### Decision Framework: TDD or Evals?

Ask: **"Is there exactly one correct answer?"**

| Answer | Use | Examples |
|--------|-----|----------|
| **Yes** | TDD | API returns expected format, function calculates correctly, config parses without error |
| **No** (range of acceptable answers requiring judgment) | Evals | Agent chooses appropriate tool, response tone matches context, summary captures key points |

**Gray Areas**: Some behaviors seem deterministic but aren't. "Did the agent call the right API?" might have one correct answer in simple cases, but when multiple APIs could work, you need evals to judge which choice was *better*.

### The Two Evaluation Axes

Every eval criterion exists along two independent dimensions:

**Axis 1: Scoring Method**
| Type | Definition | Signal Quality |
|------|------------|----------------|
| **Objective** | A deterministic function can verify correctness | High (no noise) |
| **Subjective** | Requires reasoning about quality, not just matching | Variable (LLM introduces noise) |

**Axis 2: Reference Data**
| Type | Definition | Data Requirement |
|------|------------|------------------|
| **Ground Truth** | Known correct answers exist for each test case | Must curate expected outputs |
| **No Ground Truth** | Quality assessed against criteria/rubrics only | Define rubric, not answers |

### The Four Quadrants

```
                    │ Ground Truth Available │ No Ground Truth │
────────────────────┼────────────────────────┼─────────────────┤
Objective           │        Q1 ⭐            │       Q3        │
(Code-checkable)    │   Fastest, Cheapest    │   Fast, Cheap   │
────────────────────┼────────────────────────┼─────────────────┤
Subjective          │        Q2              │       Q4        │
(LLM-judged)        │      Moderate          │ Most Expensive  │
────────────────────┴────────────────────────┴─────────────────┘
```

**Q1: Objective + Ground Truth** (Preferred when possible)
- Code verifies outputs match expected answers
- Examples: invoice date extraction, tool call verification, JSON schema validation, math problems
- Implementation: String matching, regex, schema validators, exact comparison

**Q2: Subjective + Ground Truth**
- LLM judges assess semantic coverage against reference content
- Examples: summaries addressing key talking points, reports including required findings, code implementing specified functionality
- Implementation: LLM-as-Judge with reference comparison prompt

**Q3: Objective + No Ground Truth**
- Code checks constraints without needing correct answers
- Examples: "response under 500 tokens", "no PII detected", "valid JSON format", "no profanity"
- Implementation: Length checks, regex patterns, format validators, blocklist matching

**Q4: Subjective + No Ground Truth**
- LLM judges evaluate quality using rubrics when no single correct answer exists
- Examples: response helpfulness, explanation clarity, appropriate tone, engagement level
- Implementation: LLM-as-Judge with rubric-based scoring

#### Quadrant Decision Framework

When analyzing a new eval need, ask these questions in order:

```
1. Can you obtain ground truth for test cases?
   │
   ├── YES ──→ 2a. Can code verify success deterministically?
   │                │
   │                ├── YES ──→ Q1 (Use code grader with expected outputs)
   │                └── NO ───→ Q2 (Use LLM judge with reference comparison)
   │
   └── NO ───→ 2b. Can code check the constraint?
                    │
                    ├── YES ──→ Q3 (Use code grader with constraint check)
                    └── NO ───→ Q4 (Use LLM judge with rubric)
```

#### Quadrant Preference Hierarchy

**Key Insight**: The cheapest reliable eval is the best eval. Move toward Q1/Q3 whenever the criterion allows it.

| Priority | Quadrant | Why Prefer |
|----------|----------|------------|
| 1st | Q1 | Zero LLM cost, deterministic, fast, no noise |
| 2nd | Q3 | Zero LLM cost, deterministic, no curation overhead |
| 3rd | Q2 | LLM cost but bounded by reference quality |
| 4th | Q4 | Highest cost, most noise, but captures nuanced quality |

**Common Mistakes to Avoid:**
- ❌ Using LLM judges for code-checkable criteria → Wastes resources, introduces unnecessary noise
- ❌ Expecting code to assess criteria requiring semantic understanding → Produces unreliable signals
- ✅ Match evaluation approach to criterion type for optimal signal quality and cost efficiency

### Graders

Graders are the functions that score agent outputs. Choose grader type based on quadrant classification.

**Key Insight**: Binary criteria produce more reliable scores than numeric scales because they leverage LLM classification strengths while avoiding calibration weaknesses.

#### Code-Based Grader Structure (Q1, Q3)

Use when criterion is objective/code-checkable. Structure checks as a dictionary with sum-based scoring and standardized result format:

```python
def grade_response(output: str, expected: dict) -> dict:
    """Code-based grader with structured checks and standardized output."""
    checks = {
        "has_required_fields": all(
            field in output for field in expected.get("required_fields", [])
        ),
        "valid_json": is_valid_json(output),
        "within_length": len(output) <= expected.get("max_length", 1000),
        "no_pii_detected": not contains_pii(output),
        "matches_expected": output.strip() == expected.get("exact_match", "").strip()
    }

    score = sum(checks.values()) / len(checks)

    return {
        "passed": score >= expected.get("threshold", 0.8),
        "score": score,
        "checks": checks,
        "failed_checks": [k for k, v in checks.items() if not v]
    }
```

#### LLM Grader Prompt Template (Q2, Q4)

Use when criterion requires semantic judgment. Present criteria as numbered yes/no questions with explicit response constraints.

**Key Insight**: Decompose quality assessments into **5-7 specific yes/no questions** rather than relying on numeric scales. Each question should be clear enough that multiple humans would arrive at the same conclusion independently. The final score comes from counting affirmative answers.

```python
LLM_GRADER_PROMPT = """
Evaluate the following agent response against the criteria below.

## Input
{input}

## Agent Response
{response}

## Reference (if available)
{reference}

## Evaluation Criteria
Answer each question with YES or NO only:

1. Does the response directly address the user's request?
2. Is the information factually consistent with the reference?
3. Is the response free of hallucinated details not in the source?
4. Does the tone match the expected context (professional/casual)?
5. Is the response complete without unnecessary verbosity?

## Your Evaluation
Provide exactly 5 lines, one answer per criterion:
"""

def parse_llm_grader_response(llm_response: str) -> dict:
    """Parse binary YES/NO responses into structured result."""
    lines = [line.strip().upper() for line in llm_response.strip().split('\n') if line.strip()]
    criteria = [
        "addresses_request", "factually_consistent",
        "no_hallucinations", "appropriate_tone", "complete_response"
    ]

    checks = {
        criteria[i]: lines[i] == "YES"
        for i in range(min(len(lines), len(criteria)))
    }

    return {
        "passed": sum(checks.values()) >= 4,
        "score": sum(checks.values()) / len(criteria),
        "checks": checks
    }
```

#### Combined Grader Pattern

Execute code checks first to filter structural validity, then run LLM evaluation only for responses passing initial checks. This sequencing optimizes cost by avoiding expensive LLM calls on obviously flawed outputs:

```python
def combined_grader(output: str, expected: dict, llm_client) -> dict:
    """Two-stage grader: code checks first, LLM evaluation second."""

    # Stage 1: Fast code-based structural checks
    structural_checks = {
        "valid_format": is_valid_json(output),
        "within_limits": len(output) <= expected.get("max_length", 2000),
        "has_required_sections": all(
            section in output for section in expected.get("sections", [])
        )
    }

    structural_passed = all(structural_checks.values())

    if not structural_passed:
        return {
            "passed": False,
            "stage_failed": "structural",
            "structural_checks": structural_checks,
            "semantic_checks": None,
            "reason": f"Failed structural checks: {[k for k, v in structural_checks.items() if not v]}"
        }

    # Stage 2: Expensive LLM-based semantic evaluation
    llm_response = llm_client.evaluate(
        prompt=LLM_GRADER_PROMPT.format(
            input=expected.get("input", ""),
            response=output,
            reference=expected.get("reference", "N/A")
        )
    )

    semantic_result = parse_llm_grader_response(llm_response)

    return {
        "passed": semantic_result["passed"],
        "stage_failed": None if semantic_result["passed"] else "semantic",
        "structural_checks": structural_checks,
        "semantic_checks": semantic_result["checks"],
        "score": semantic_result["score"]
    }
```

#### Grader Design Principles

| Principle | Guidance |
|-----------|----------|
| **Prioritize code checks** | Use code-based graders for all deterministic criteria |
| **Reserve LLM for semantics** | Only invoke LLM judges when semantic understanding is required |
| **Avoid numeric scales** | Prefer binary YES/NO over 1-5 ratings due to calibration inconsistencies |
| **Use 5-7 binary criteria** | Decompose quality into specific yes/no questions clear enough for human consensus |
| **Evaluate independently** | Score each response separately against identical criteria; avoid pairwise "which is better?" comparisons |
| **Sequence for cost** | Run cheap checks before expensive ones to fail fast |
| **Standardize output** | Always return structured results with pass/fail, score, and failed checks |

#### Independent Evaluation Over Pairwise Comparison

When comparing agent outputs (e.g., A/B testing prompts or model changes), avoid asking an LLM to directly compare two responses.

**Why Pairwise Fails:**
- **Positional bias**: LLMs tend to favor the first or last option presented
- **Inconsistent criteria**: The judge may weight different factors across comparisons
- **Non-transitive rankings**: A > B and B > C doesn't guarantee A > C

**Independent Evaluation Pattern:**

```python
def compare_responses_independently(response_a: str, response_b: str,
                                     input_context: str, criteria: list) -> dict:
    """Evaluate each response separately, then compare scores mathematically."""

    # Evaluate A independently
    score_a = evaluate_against_criteria(response_a, input_context, criteria)

    # Evaluate B independently with IDENTICAL criteria
    score_b = evaluate_against_criteria(response_b, input_context, criteria)

    # Mathematical comparison, not LLM opinion
    return {
        "response_a_score": score_a,
        "response_b_score": score_b,
        "winner": "A" if score_a > score_b else "B" if score_b > score_a else "tie",
        "margin": abs(score_a - score_b)
    }
```

**Key Insight**: Calculate final scores mathematically from independent evaluations. Never ask "which response is better?"—this framing introduces bias that undermines reliability.

### Grader Validation

**Core Principle**: LLM judges are powerful but imperfect. Validate against human judgment before production deployment.

#### Human Calibration Process

Before deploying any LLM grader to production:

1. **Gather human ratings**: Have humans rate at least 20 sample responses using your criteria
2. **Run LLM grader**: Evaluate the same 20 samples with your automated grader
3. **Measure agreement**: Calculate alignment between human and LLM judgments
4. **Iterate if needed**: Poor alignment signals criteria need clarification

#### Agreement Thresholds

| Metric | Target | Action if Below |
|--------|--------|-----------------|
| **Exact match** | ≥70% | Revise criteria for clarity |
| **Within-one** | ≥90% | Review edge cases, add examples |

```python
def validate_grader_against_humans(
    samples: list[dict],
    human_ratings: list[dict],
    llm_grader: callable
) -> dict:
    """Validate LLM grader alignment with human judgment."""

    llm_ratings = [llm_grader(sample) for sample in samples]

    exact_matches = sum(
        1 for h, l in zip(human_ratings, llm_ratings)
        if h["passed"] == l["passed"]
    )

    within_one = sum(
        1 for h, l in zip(human_ratings, llm_ratings)
        if abs(h["score"] - l["score"]) <= 0.2  # Within one criterion
    )

    n = len(samples)

    return {
        "exact_match_rate": exact_matches / n,
        "within_one_rate": within_one / n,
        "ready_for_production": (exact_matches / n >= 0.7) and (within_one / n >= 0.9),
        "disagreements": [
            {"sample": s, "human": h, "llm": l}
            for s, h, l in zip(samples, human_ratings, llm_ratings)
            if h["passed"] != l["passed"]
        ]
    }
```

#### When Alignment Fails

If your grader doesn't meet thresholds:

| Issue | Likely Cause | Fix |
|-------|--------------|-----|
| Low exact match | Ambiguous criteria | Rewrite questions to be more specific |
| Inconsistent within-one | Edge case handling | Add examples of borderline cases to prompt |
| Systematic bias | Criteria mismatch | Humans and LLM interpret criteria differently—align definitions |

**Key Insight**: A grader that disagrees with humans 30%+ of the time will produce unreliable signals and erode trust in your evaluation system. Invest in calibration upfront.

### Error Analysis

Systematic error analysis transforms agent improvement from intuition-driven to data-driven. Rather than immediately fixing perceived problems, effective builders first analyze failure patterns to identify which components actually require attention.

#### The Build-Analyze Loop

The development cycle prioritizes investigation before intervention:

1. Build agent version
2. Run evaluations
3. **Analyze errors** (most developers skip this critical step)
4. Identify which component failed most frequently
5. Fix that specific component
6. Re-run evaluations
7. Repeat

**Key Insight**: "Less experienced teams spend a lot of time building and probably much less time analyzing" (Andrew Ng). Analysis time prevents wasted effort on wrong components. Thirty minutes counting errors outperforms thirty hours fixing the wrong system.

#### Traces and Spans Vocabulary

| Term | Definition |
|------|------------|
| **Trace** | Complete record capturing all intermediate outputs from a single agent execution—every LLM call, search operation, decision point, and final response |
| **Span** | Individual step's input, processing, and output within a trace. Each component produces one span |

This vocabulary enables precise error attribution. Rather than saying "the agent failed," you identify: "the source selection span picked low-quality sources despite high-quality options in search results."

**Critical Pattern**: Always trace errors to root cause by examining complete traces. A component might fail frequently because it receives degraded input upstream, not because it's broken. Attribution without investigation produces false improvements.

#### The Spreadsheet Method

Simple tabulation reveals error patterns:

| Case | Component A | Component B | Component C | Error Location |
|------|-------------|-------------|-------------|----------------|
| Q1   | OK          | ERROR       | ERROR       | Component B    |
| Q2   | OK          | OK          | OK          | None           |
| Q3   | ERROR       | -           | -           | Component A    |
| Q4   | OK          | OK          | ERROR       | Component C    |

Count occurrences by location. Percentages emerge from data rather than memory bias.

#### Why Counting Beats Intuition

Several cognitive biases distort error perception:

| Bias | Distortion | Fix |
|------|------------|-----|
| **Availability** | Recent or dramatic failures feel more common | Count all failures equally |
| **Confirmation** | You notice errors matching your existing theory | Categorize before theorizing |
| **Expertise** | You focus on components you understand best | Systematic span examination |
| **Anchoring** | First errors dominate thinking | Randomize analysis order |

Systematic counting corrects these distortions by treating all failures equally.

#### Prioritization Formula

**Priority = Frequency × Feasibility**

- **Frequency**: What percentage of failures originate here?
- **Feasibility**: How easily can you fix it? (Scale: 0=impossible to 1=trivial)

| Feasibility | Description | Examples |
|-------------|-------------|----------|
| 0.9–1.0 | Trivial | Configuration or regex changes |
| 0.7–0.8 | Easy | Prompt adjustments or filters |
| 0.5–0.6 | Moderate | Retraining or new components |
| 0.3–0.4 | Hard | New architecture or external dependencies |
| 0.0–0.2 | Unknown | Requires investigation first |

**Example**: A component failing 45% of the time but requiring infrastructure changes (feasibility 0.3) scores 13.5. Another failing 15% but fixable in minutes (feasibility 0.9) scores 13.5. Prioritize equally, but the second requires less effort.

#### Error Analysis Implementation

```python
from dataclasses import dataclass
from collections import Counter

@dataclass
class AnalyzedCase:
    case_id: str
    error_location: str  # Which span failed
    trace: dict          # Full execution trace

def analyze_failures(cases: list[AnalyzedCase]) -> dict:
    """Generate error report from analyzed cases."""

    failed_cases = [c for c in cases if c.error_location != "none"]
    error_counts = Counter(case.error_location for case in failed_cases)
    total_failures = len(failed_cases)

    if total_failures == 0:
        return {"total_cases": len(cases), "failures": 0, "breakdown": {}}

    error_percentages = {
        location: {
            "count": count,
            "percentage": (count / total_failures) * 100
        }
        for location, count in error_counts.most_common()
    }

    return {
        "total_cases": len(cases),
        "failures": total_failures,
        "failure_rate": total_failures / len(cases),
        "breakdown": error_percentages,
        "top_priority": error_counts.most_common(1)[0][0]
    }

def prioritize_fixes(error_report: dict, feasibility: dict[str, float]) -> list:
    """Rank components by priority = frequency × feasibility."""

    priorities = []
    for location, data in error_report["breakdown"].items():
        freq = data["percentage"] / 100
        feas = feasibility.get(location, 0.5)
        priorities.append({
            "component": location,
            "frequency": freq,
            "feasibility": feas,
            "priority_score": freq * feas
        })

    return sorted(priorities, key=lambda x: x["priority_score"], reverse=True)
```

### Dataset Design

**Core Principle**: Quality over quantity. Start with 10-20 examples. The bottleneck in agent improvement is understanding *why* failures occur, not accumulating raw test volume.

#### The Three-Category Framework

| Category | Count | Purpose | Pass Rate Target |
|----------|-------|---------|------------------|
| **Typical** | 10 | Common use cases representing 80% of real usage | 90%+ |
| **Edge** | 5 | Unusual but valid scenarios requiring judgment calls | 70-80% |
| **Error** | 5 | Requests outside agent scope or impossible requests | Should fail gracefully |

**Typical Cases (10)**: Bread-and-butter scenarios the agent was designed for—straightforward task creation, basic queries, standard workflows.

**Edge Cases (5)**: Uncommon but legitimate requests—emoji in titles, ambiguous time references, multiple simultaneous actions, special characters. Tests graceful degradation.

**Error Cases (5)**: Test recognition of limitations—out-of-domain queries, malformed inputs, impossible requests, inappropriate commands the agent should decline.

#### Real Data Over Synthetic

| Data Type | Characteristics | Value |
|-----------|-----------------|-------|
| **Synthetic** | Clean, well-formed, imagined | Low—misses real usage patterns |
| **Production** | Messy, abbreviated, context-dependent | High—reveals genuine failure modes |

**Mining Real Data Process:**
1. Export 30 days of user queries
2. Filter for negative signals: poor ratings, retry patterns, support tickets, abandoned sessions
3. Sample 50-100 candidates
4. Classify into Typical/Edge/Error categories
5. Select 20 diverse, representative cases

#### Eval Case Structure

Each case requires three components:

```
{
  "input": "User message + relevant context (prior conversation, user state)",
  "expected": "Success criteria, output patterns, should_succeed boolean",
  "rationale": "Why this case exists and what it tests"
}
```

#### Dataset Growth Strategy

Grow organically through production feedback, not arbitrary coverage targets:

✅ **Add cases when:**
- Production failures reveal uncovered patterns
- New case initially fails (confirms bug exists)
- After fix, case passes (confirms fix works)

❌ **Don't add cases because:**
- "We should have better coverage" (vague)
- "Competitors have larger datasets" (irrelevant)
- "Time has passed since last update" (age ≠ gaps)

**Key Insight**: Twenty thoughtful cases revealing failure patterns outperform thousands producing only pass-rate percentages. Evaluation systems exist to drive improvement, not generate confidence scores

### Regression Protection

**Core Principle**: Regression protection isn't about preventing all changes—it's about knowing what your changes do. Evaluation suites transform from one-time validation into continuous quality assurance through systematic baseline comparison and per-criterion tracking.

**Key Insight**: Aggregate performance improvements can mask critical regressions in specific criteria. A system that improves from 80% to 85% overall while dropping from 95% to 75% on factual accuracy has regressed where it matters most.

#### The Baseline-First Development Pattern

Every agent modification requires baseline establishment before changes begin. This discipline prevents post-hoc rationalization of unexpected performance shifts.

**Workflow:**

```python
# 1. BEFORE any code changes
baseline_results = run_full_eval_suite(agent, dataset)
save_baseline(
    results=baseline_results,
    version="v1.2.3",
    timestamp=datetime.now(),
    metadata={"model": "claude-sonnet-4-5", "config": current_config}
)

# 2. Make your changes
modify_agent_code()

# 3. AFTER changes, run identical eval suite
current_results = run_full_eval_suite(agent, dataset)

# 4. Compare per-criterion, not just aggregate
regression_report = detect_regressions(
    baseline=baseline_results,
    current=current_results,
    threshold_config=DOMAIN_THRESHOLDS
)

# 5. Review before proceeding
if regression_report["has_regressions"]:
    print(regression_report["detailed_analysis"])
    # Decide: accept tradeoff, revert change, or iterate further
```

**Critical Pattern**: Never compare current performance to memory or intuition. Always compare to captured baseline data.

#### Per-Criterion Regression Detection

Aggregate metrics hide critical signal. Track every criterion independently to catch hidden regressions.

**Why Aggregates Fail:**

| Scenario | Overall Score | Hidden Reality |
|----------|--------------|----------------|
| Baseline | 82% | All criteria balanced |
| After change | 87% (+5%) | "factual_consistency" dropped 92% → 72% (-20%) |
| Interpretation | ✅ Improvement! | ❌ Critical regression masked by other gains |

**Implementation:**

```python
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class CriterionResult:
    name: str
    baseline_score: float
    current_score: float

    @property
    def delta(self) -> float:
        return self.current_score - self.baseline_score

    @property
    def pct_change(self) -> float:
        if self.baseline_score == 0:
            return 0
        return (self.delta / self.baseline_score) * 100

def detect_regressions(
    baseline: Dict[str, float],
    current: Dict[str, float],
    threshold_config: dict
) -> dict:
    """
    Detect regressions by comparing each criterion independently.

    Returns detailed report including:
    - Per-criterion deltas
    - Flagged regressions based on thresholds
    - Overall assessment
    """

    criterion_results = []
    regressions = []

    for criterion_name in baseline.keys():
        result = CriterionResult(
            name=criterion_name,
            baseline_score=baseline[criterion_name],
            current_score=current.get(criterion_name, 0)
        )
        criterion_results.append(result)

        # Check against threshold
        threshold = threshold_config.get("drop_threshold", 0.05)
        any_drop_fails = threshold_config.get("any_drop", False)

        if any_drop_fails and result.delta < 0:
            regressions.append(result)
        elif abs(result.delta) >= threshold and result.delta < 0:
            regressions.append(result)

    # Calculate aggregate metrics
    baseline_avg = sum(baseline.values()) / len(baseline)
    current_avg = sum(current.values()) / len(current)

    return {
        "has_regressions": len(regressions) > 0,
        "regression_count": len(regressions),
        "regressed_criteria": [r.name for r in regressions],
        "criterion_details": [
            {
                "name": r.name,
                "baseline": r.baseline_score,
                "current": r.current_score,
                "delta": r.delta,
                "pct_change": r.pct_change
            }
            for r in criterion_results
        ],
        "aggregate_baseline": baseline_avg,
        "aggregate_current": current_avg,
        "aggregate_delta": current_avg - baseline_avg,
        "detailed_analysis": format_regression_report(criterion_results, regressions)
    }

def format_regression_report(all_results: List[CriterionResult],
                             regressions: List[CriterionResult]) -> str:
    """Generate human-readable regression report."""

    lines = ["=" * 60, "REGRESSION DETECTION REPORT", "=" * 60, ""]

    if not regressions:
        lines.append("✅ No regressions detected")
    else:
        lines.append(f"⚠️  {len(regressions)} regression(s) detected:")
        lines.append("")
        for reg in regressions:
            lines.append(f"  • {reg.name}")
            lines.append(f"    Baseline: {reg.baseline_score:.1%}")
            lines.append(f"    Current:  {reg.current_score:.1%}")
            lines.append(f"    Delta:    {reg.delta:+.1%} ({reg.pct_change:+.1f}%)")
            lines.append("")

    lines.append("All Criteria Changes:")
    lines.append("")
    for result in sorted(all_results, key=lambda r: r.delta):
        indicator = "📉" if result.delta < 0 else "📈" if result.delta > 0 else "➡️"
        lines.append(
            f"  {indicator} {result.name}: "
            f"{result.baseline_score:.1%} → {result.current_score:.1%} "
            f"({result.delta:+.1%})"
        )

    return "\n".join(lines)
```

**Key Insight**: Always review the full criterion-level report, even when aggregate scores improve. Regressions in high-importance criteria (factual accuracy, safety, tone) matter more than improvements in low-importance ones (formatting, verbosity).

#### Context-Dependent Thresholds

Sensitivity configuration depends on domain stakes and iteration velocity requirements.

| Domain | Threshold Config | Rationale |
|--------|-----------------|-----------|
| **High-Stakes** (medical, financial, safety-critical) | `any_drop=True` | Any performance decrease requires investigation. User harm from regression outweighs iteration speed. |
| **Standard** (customer support, productivity tools) | `drop_threshold=0.05` | 5% drops trigger review. Balances quality protection with development velocity. |
| **Experimental** (prototypes, research) | `drop_threshold=0.10` | 10% threshold allows rapid experimentation. Speed of learning prioritized over stability. |

**Configuration Pattern:**

```python
# Define thresholds by project stage or domain
THRESHOLDS = {
    "production_medical": {
        "any_drop": True,
        "require_signoff": True,
        "criteria_weights": {
            "factual_accuracy": 2.0,  # Extra sensitivity
            "safety_compliance": 2.0,
            "formatting": 0.5
        }
    },

    "production_standard": {
        "drop_threshold": 0.05,
        "require_signoff": False,
        "critical_criteria": ["factual_accuracy", "appropriate_tone"]
    },

    "development": {
        "drop_threshold": 0.10,
        "require_signoff": False,
        "alert_only": True
    }
}

def apply_weighted_thresholds(regression_report: dict,
                              config: dict) -> dict:
    """Apply domain-specific weights and thresholds."""

    weights = config.get("criteria_weights", {})
    critical = config.get("critical_criteria", [])

    # Reclassify regressions with weights
    weighted_regressions = []
    for detail in regression_report["criterion_details"]:
        weight = weights.get(detail["name"], 1.0)
        is_critical = detail["name"] in critical

        # Weighted delta
        weighted_delta = detail["delta"] * weight

        # Critical criteria have stricter thresholds
        threshold = config.get("drop_threshold", 0.05)
        if is_critical:
            threshold = threshold / 2

        if weighted_delta < -threshold:
            weighted_regressions.append({
                **detail,
                "weighted_delta": weighted_delta,
                "is_critical": is_critical,
                "severity": "HIGH" if is_critical else "MEDIUM"
            })

    return {
        **regression_report,
        "weighted_regressions": weighted_regressions,
        "requires_signoff": (
            config.get("require_signoff", False) and
            len(weighted_regressions) > 0
        )
    }
```

**Decision Framework**: Choose threshold based on question: "What's worse—blocking a beneficial change or shipping a harmful regression?"

#### CI/CD Integration

Automated regression protection prevents accidental deployment of degraded agents.

**Pipeline Pattern:**

```yaml
# .github/workflows/agent-eval.yml
name: Agent Evaluation

on:
  pull_request:
    paths:
      - 'agent/**'
      - 'prompts/**'
      - 'config/**'

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup environment
        run: |
          pip install -r requirements.txt

      - name: Load baseline
        run: |
          # Fetch baseline from main branch or storage
          python scripts/load_baseline.py --branch main --output baseline.json

      - name: Run evaluation suite
        run: |
          python scripts/run_evals.py --dataset eval_datasets.json --output current.json

      - name: Detect regressions
        id: regression_check
        run: |
          python scripts/compare_results.py \
            --baseline baseline.json \
            --current current.json \
            --threshold-config production_standard \
            --output regression_report.json

      - name: Post results to PR
        uses: actions/github-script@v6
        with:
          script: |
            const report = require('./regression_report.json');
            const body = formatReportForGitHub(report);

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });

      - name: Block merge on regression
        if: steps.regression_check.outputs.has_regressions == 'true'
        run: |
          echo "::error::Regressions detected. Review required before merge."
          exit 1
```

**Key Components:**

| Component | Purpose |
|-----------|---------|
| **Baseline loading** | Fetch comparison target from main branch or artifact storage |
| **Identical eval suite** | Run same dataset/graders on PR branch |
| **Automated comparison** | Detect regressions without human calculation |
| **PR comment** | Surface results where decisions happen |
| **Merge blocking** | Prevent accidental regression deployment |

**Storage Pattern for Baselines:**

```python
# Save baseline with version control
def save_baseline(results: dict, version: str, metadata: dict):
    """Store baseline for future comparison."""

    baseline_entry = {
        "version": version,
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "metadata": metadata
    }

    # Option 1: Version control (simple, auditable)
    baseline_file = f"baselines/{version}.json"
    with open(baseline_file, "w") as f:
        json.dump(baseline_entry, f, indent=2)

    # Option 2: Database (queryable, scalable)
    db.baselines.insert_one(baseline_entry)

    # Option 3: Cloud storage (distributed teams)
    s3.upload_json(baseline_entry, f"baselines/{version}.json")

def load_baseline(version: str = "latest") -> dict:
    """Load baseline for comparison."""

    if version == "latest":
        # Get most recent from main branch
        version = get_latest_baseline_version()

    return json.load(open(f"baselines/{version}.json"))
```

#### The Eval-Driven Development Loop

Systematic iteration workflow that uses evaluation data to guide improvement decisions.

**Complete Workflow:**

```
1. Establish Baseline
   ↓
2. Identify Lowest-Performing Criterion
   ↓
3. Hypothesize Root Cause
   ↓
4. Make Targeted Change
   ↓
5. Run Full Eval Suite
   ↓
6. Compare to Baseline
   ├─→ Regression detected? → Investigate/revert → Back to step 3
   └─→ Improvement confirmed? → Update baseline → Back to step 2
```

**Implementation:**

```python
class EvalDrivenDevelopment:
    """Encapsulates eval-driven iteration workflow."""

    def __init__(self, agent, dataset, threshold_config):
        self.agent = agent
        self.dataset = dataset
        self.threshold_config = threshold_config
        self.baseline = None
        self.iteration_history = []

    def establish_baseline(self):
        """Step 1: Capture current performance before changes."""
        print("🔍 Establishing baseline...")
        self.baseline = run_full_eval_suite(self.agent, self.dataset)

        print(f"✅ Baseline established:")
        print(f"   Overall: {self.baseline['aggregate']:.1%}")
        print(f"   Per criterion: {self.baseline['by_criterion']}")

        return self.baseline

    def identify_improvement_target(self) -> str:
        """Step 2: Find lowest-performing criterion."""
        if not self.baseline:
            raise ValueError("Must establish baseline first")

        by_criterion = self.baseline["by_criterion"]
        sorted_criteria = sorted(by_criterion.items(), key=lambda x: x[1])

        target = sorted_criteria[0]
        print(f"\n🎯 Improvement target: {target[0]} ({target[1]:.1%})")

        return target[0]

    def test_change(self, change_description: str):
        """Steps 4-6: Test change and compare to baseline."""
        print(f"\n🔬 Testing change: {change_description}")

        # Run evals on modified agent
        current_results = run_full_eval_suite(self.agent, self.dataset)

        # Detect regressions
        regression_report = detect_regressions(
            baseline=self.baseline["by_criterion"],
            current=current_results["by_criterion"],
            threshold_config=self.threshold_config
        )

        # Record iteration
        iteration = {
            "change": change_description,
            "timestamp": datetime.now().isoformat(),
            "results": current_results,
            "regression_report": regression_report
        }
        self.iteration_history.append(iteration)

        # Present results
        print(regression_report["detailed_analysis"])

        return regression_report

    def accept_change(self):
        """Update baseline after accepting change."""
        if not self.iteration_history:
            raise ValueError("No changes to accept")

        latest = self.iteration_history[-1]
        self.baseline = latest["results"]

        print(f"✅ Change accepted. Baseline updated.")
        print(f"   New overall: {self.baseline['aggregate']:.1%}")

    def reject_change(self):
        """Discard change, keep baseline unchanged."""
        print("❌ Change rejected. Baseline unchanged.")
        # Agent should be reverted to baseline state externally

# Usage
edd = EvalDrivenDevelopment(
    agent=my_agent,
    dataset=eval_dataset,
    threshold_config=THRESHOLDS["production_standard"]
)

# Iteration 1
edd.establish_baseline()
target = edd.identify_improvement_target()  # "factual_consistency" (72%)

# Improve factual_consistency
modify_agent_prompt("Add fact-checking step...")
report = edd.test_change("Added explicit fact-checking in prompt")

if not report["has_regressions"]:
    edd.accept_change()
else:
    print("Regression detected in:", report["regressed_criteria"])
    # Decide: accept tradeoff, revert, or iterate further

# Iteration 2
target = edd.identify_improvement_target()  # Next lowest criterion
# Continue iterating...
```

**Key Disciplines:**

| Discipline | Why It Matters |
|------------|----------------|
| **Baseline before changes** | Prevents confirmation bias—you can't unconsciously shift comparison target |
| **Change one thing at a time** | Enables attribution—you know what caused improvements or regressions |
| **Full eval suite every time** | Catches hidden regressions in non-target criteria |
| **Decide explicitly** | Accept, reject, or iterate—never leave changes in limbo |
| **Update baseline on accept** | New baseline becomes comparison target for next iteration |

**Anti-Pattern Warning:**

```python
# ❌ BAD: Making multiple changes without intermediate evals
improve_prompt()
change_temperature()
add_validation_step()
run_evals()  # Which change caused which effect?

# ✅ GOOD: Eval-driven iteration
baseline = run_evals()

improve_prompt()
results_1 = run_evals()
compare(baseline, results_1)  # Prompt change isolated

change_temperature()
results_2 = run_evals()
compare(results_1, results_2)  # Temperature change isolated
```

**Time Investment vs Return:**

Running evals after every change feels slow initially but accelerates overall development:

| Approach | Initial Speed | Debug Time | Total Time | Confidence |
|----------|--------------|------------|------------|------------|
| **No evals** | Fast | Very long (unknown root cause) | Longest | Low |
| **Eval at end** | Fast | Long (multiple changes to untangle) | Long | Medium |
| **Eval per change** | Moderate | Minimal (attribution clear) | Shortest | High |

**Key Insight**: The eval-driven loop trades small upfront costs (running evals) for massive downstream savings (knowing exactly what each change does). Teams that resist this discipline spend weeks debugging mystery regressions that proper baselines would have caught in minutes.

## The Complete Quality Loop

**Core Pattern**: Agent development = Building + Analysis. High-performing teams allocate disproportionate time to understanding failures rather than coding fixes, achieving faster deployment through systematic learning rather than intuitive problem-solving.

**Key Insight**: The quality loop isn't linear—it's a continuous cycle where production failures feed back into dataset improvement, creating a compounding advantage over time.

### The Ten-Step Workflow

The complete quality loop transforms agent development from ad-hoc iteration into a systematic methodology:

```
1. Build Initial Agent → 2. Create Eval Dataset → 3. Execute Evals
         ↑                                              ↓
    10. Monitor                                  4. Analyze Errors
    Production                                          ↓
         ↑                                     5. Fix Lowest Component
    9. Deploy with                                      ↓
    Safeguards                                   6. Re-run Evals
         ↑                                              ↓
    8. Ship Decision ← 7. Verify No Regression ←────────┘
```

#### Step 1: Build Initial Agent (Quick Prototype)

Goal: Create minimally viable agent to generate baseline data, not production-ready system.

**Anti-Pattern**: Spending weeks on initial architecture before measuring quality.

```python
# Week 1: Quick prototype
def initial_agent(user_input: str) -> str:
    """Bare minimum agent to test core hypothesis."""
    prompt = f"You are a helpful assistant. User: {user_input}"
    return llm.generate(prompt)

# NOT Week 1: Over-engineered system
class AgentFramework:
    def __init__(self, router, planner, executor, validator):
        # Complex architecture before knowing what matters
        ...
```

**Time Investment**: 1-3 days maximum. The goal is generating outputs to evaluate, not perfection.

#### Step 2: Create Evaluation Dataset (10-20 Cases)

Design dataset using the three-category framework (Typical/Edge/Error). See Dataset Design section for full details.

**Minimum Viable Dataset:**

```python
INITIAL_DATASET = [
    # Typical cases (10)
    {"input": "Schedule meeting tomorrow 2pm", "category": "typical"},
    {"input": "What's on my calendar Friday?", "category": "typical"},
    # ... 8 more typical cases

    # Edge cases (5)
    {"input": "Schedule meeting 🎉 party time", "category": "edge"},
    {"input": "Meeting at 2 (which timezone?)", "category": "edge"},
    # ... 3 more edge cases

    # Error cases (5)
    {"input": "Schedule meeting yesterday", "category": "error"},
    {"input": "Delete all my data", "category": "error"},
    # ... 3 more error cases
]
```

**Key Principle**: Real production data outweighs synthetic data by 10x. Mine actual user queries when possible.

#### Step 3: Execute Evals (Establish Baseline)

Run full evaluation suite to establish baseline before any optimization. Record both aggregate and per-criterion scores.

```python
baseline_results = {
    "version": "v0.1",
    "timestamp": "2026-01-30T10:00:00Z",
    "aggregate_score": 0.73,  # 73% overall
    "by_criterion": {
        "correct_tool_selection": 0.85,
        "factual_accuracy": 0.68,  # Lowest
        "appropriate_tone": 0.90,
        "complete_response": 0.72,
        "handles_errors_gracefully": 0.60  # Second lowest
    },
    "by_category": {
        "typical": 0.82,
        "edge": 0.65,
        "error": 0.58
    }
}
```

**Critical Step**: Save complete traces for error analysis, not just scores.

#### Step 4: Analyze Errors Systematically

Apply error analysis methodology (see Error Analysis section) to identify component-level failure patterns.

**Failure Mode Categorization:**

| Failure Mode | Definition | Severity | Example |
|--------------|------------|----------|---------|
| **Graceful** | Agent recognizes limitation and declines appropriately | Low | "I cannot schedule meetings in the past" |
| **Confident-Wrong** | Agent proceeds confidently with incorrect information | High | Creates meeting at wrong time without warning |
| **Partial** | Agent completes task but misses requirements | Medium | Schedules meeting but ignores timezone |
| **Tool-Selection** | Agent chooses wrong tool or API | Medium | Uses search instead of calendar API |

**Analysis Template:**

```python
@dataclass
class ErrorAnalysis:
    case_id: str
    failure_mode: str  # graceful | confident-wrong | partial | tool-selection
    component_failed: str  # routing | tool-use | response-generation | validation
    root_cause: str
    trace: dict

def analyze_failure_distribution(errors: list[ErrorAnalysis]) -> dict:
    """Categorize failures by mode and component."""

    by_mode = Counter(e.failure_mode for e in errors)
    by_component = Counter(e.component_failed for e in errors)

    # Prioritize confident-wrong failures regardless of frequency
    critical_failures = [e for e in errors if e.failure_mode == "confident-wrong"]

    return {
        "by_mode": dict(by_mode),
        "by_component": dict(by_component),
        "critical_count": len(critical_failures),
        "critical_cases": [e.case_id for e in critical_failures],
        "fix_priority": prioritize_components(by_component, critical_failures)
    }

def prioritize_components(by_component: dict,
                         critical_failures: list[ErrorAnalysis]) -> list:
    """
    Prioritization hierarchy:
    1. Components with confident-wrong failures (highest risk)
    2. Most frequent failure component (highest impact)
    3. Feasibility-weighted score (fastest wins)
    """

    # Check for critical failures first
    critical_components = set(e.component_failed for e in critical_failures)
    if critical_components:
        return list(critical_components)

    # Fall back to frequency × feasibility
    return sorted(
        by_component.items(),
        key=lambda x: x[1],  # Frequency
        reverse=True
    )
```

**Key Insight**: Confident-wrong failures outweigh all other considerations. A system that fails gracefully 50% of the time is safer than one that succeeds 90% but hallucinates confidently 10%.

#### Steps 5-7: Fix, Re-test, Verify (Iteration Cycle)

**Step 5: Fix Lowest Component**

Target the single lowest-performing component identified in analysis. Resist fixing multiple things simultaneously.

```python
# Analysis identified: factual_accuracy = 0.68 (lowest)
# Root cause: Agent doesn't verify facts against retrieved data

# ✅ GOOD: Single targeted fix
def improved_agent(user_input: str) -> str:
    context = retrieve_relevant_context(user_input)
    prompt = f"""You are a helpful assistant.

IMPORTANT: Only state facts that are explicitly present in the context below.
If the context doesn't contain information needed to answer, say so.

Context: {context}

User: {user_input}"""
    return llm.generate(prompt)

# ❌ BAD: Multiple simultaneous changes
def over_improved_agent(user_input: str) -> str:
    # Changed prompt + temperature + added validation + new retrieval
    # Which change helped? Which hurt? Unknown.
    ...
```

**Step 6: Re-run Evals**

Execute identical evaluation suite on modified agent.

```python
iteration_1_results = {
    "version": "v0.2-factual-fix",
    "aggregate_score": 0.78,  # +5% overall
    "by_criterion": {
        "correct_tool_selection": 0.85,  # Unchanged
        "factual_accuracy": 0.80,  # +12% (targeted improvement)
        "appropriate_tone": 0.88,  # -2% (possible regression)
        "complete_response": 0.73,  # +1%
        "handles_errors_gracefully": 0.62  # +2%
    }
}
```

**Step 7: Verify No Regression**

Apply regression detection (see Regression Protection section) to catch hidden degradation.

```python
regression_report = detect_regressions(
    baseline=baseline_results["by_criterion"],
    current=iteration_1_results["by_criterion"],
    threshold_config={"drop_threshold": 0.05}
)

# Example output:
# ⚠️ 1 regression detected:
#   • appropriate_tone: 0.90 → 0.88 (-2%)
#
# Investigation needed: Why did tone degrade when fixing factual accuracy?
# Hypothesis: Added "say so explicitly" instruction made responses more clinical
```

**Decision Point**: Accept tradeoff (2% tone for 12% accuracy), iterate further, or revert.

**Iteration Tracking**: Monitor diminishing returns across cycles.

```python
@dataclass
class IterationMetrics:
    iteration: int
    improvement: float  # Delta from previous iteration
    effort_hours: float
    regressions_introduced: int

def detect_diminishing_returns(iterations: list[IterationMetrics]) -> dict:
    """Flag when additional iteration yields minimal gains."""

    if len(iterations) < 3:
        return {"continue": True, "reason": "Insufficient data"}

    # Check last 3 iterations
    recent = iterations[-3:]

    avg_improvement = sum(i.improvement for i in recent) / len(recent)
    avg_effort = sum(i.effort_hours for i in recent) / len(recent)

    # Thresholds
    MIN_IMPROVEMENT = 0.02  # 2% per iteration
    MAX_EFFORT = 8  # 8 hours per iteration

    if avg_improvement < MIN_IMPROVEMENT and avg_effort > MAX_EFFORT:
        return {
            "continue": False,
            "reason": f"Diminishing returns: {avg_improvement:.1%} gain for {avg_effort:.1f}h effort",
            "recommendation": "Ship current version or redesign approach"
        }

    return {"continue": True}
```

**Anti-Pattern**: Iterating indefinitely without measuring improvement velocity. After 3-5 iterations with <2% gains each, you've likely hit architectural limits.

#### Step 8: Ship Decision

Evaluate readiness using context-dependent thresholds.

**Shipping Heuristics:**

```python
def evaluate_ship_readiness(results: dict, context: str) -> dict:
    """Determine if agent is ready for deployment."""

    score = results["aggregate_score"]

    # Base threshold by score
    if score >= 0.95:
        base_decision = "ship_confidently"
        suitable_for = ["high-stakes", "standard", "experimental"]
    elif score >= 0.90:
        base_decision = "ship_with_monitoring"
        suitable_for = ["standard", "experimental"]
    elif score >= 0.80:
        base_decision = "ship_if_low_stakes"
        suitable_for = ["experimental"]
    elif score >= 0.70:
        base_decision = "prototype_only"
        suitable_for = []
    else:
        base_decision = "continue_iteration"
        suitable_for = []

    # Additional criteria beyond score
    checks = {
        "no_critical_failures": all(
            results["by_criterion"].get(c, 0) >= 0.80
            for c in ["factual_accuracy", "safety_compliance"]
        ),
        "improvement_trajectory": is_improving(results["iteration_history"]),
        "graceful_error_handling": results["by_criterion"].get("handles_errors_gracefully", 0) >= 0.70,
        "better_than_alternative": score > get_baseline_alternative_score()
    }

    ready = base_decision in ["ship_confidently", "ship_with_monitoring"]
    ready = ready and all(checks.values())

    return {
        "decision": base_decision,
        "score": score,
        "suitable_for": suitable_for,
        "ready_to_ship": ready,
        "checks": checks,
        "rationale": generate_rationale(base_decision, checks, score)
    }

def generate_rationale(decision: str, checks: dict, score: float) -> str:
    """Generate human-readable shipping decision rationale."""

    if decision == "ship_confidently":
        return f"Score {score:.1%} meets high-stakes threshold. All safety checks passed."

    if decision == "ship_with_monitoring":
        return f"Score {score:.1%} acceptable for standard use. Deploy with active monitoring."

    if not checks["no_critical_failures"]:
        return "BLOCK: Critical failures in factual_accuracy or safety_compliance."

    if not checks["improvement_trajectory"]:
        return "BLOCK: Performance plateaued. Consider architectural changes."

    return f"Score {score:.1%} insufficient. Continue iteration."
```

**Ship Decision Table:**

| Score Range | Decision | High-Stakes | Standard | Experimental |
|-------------|----------|-------------|----------|--------------|
| **≥95%** | Ship confidently | ✅ | ✅ | ✅ |
| **90-95%** | Ship with monitoring | ⚠️ Review | ✅ | ✅ |
| **80-90%** | Ship if low-stakes | ❌ | ⚠️ Review | ✅ |
| **70-80%** | Prototype only | ❌ | ❌ | ⚠️ Limited |
| **<70%** | Continue iteration | ❌ | ❌ | ❌ |

**Additional Considerations Beyond Score:**
- Failure modes: Graceful degradation preferred over confident-wrong
- Improvement trajectory: Shipping 85% with upward trend beats 88% plateaued
- User expectations: Better than current alternative matters more than absolute score
- Monitoring capability: Ship earlier if you can detect and rollback failures quickly

#### Step 9: Deploy with Safeguards

Activate regression protection and monitoring before production deployment.

**Deployment Checklist:**

```python
DEPLOYMENT_SAFEGUARDS = {
    "regression_protection": {
        "enabled": True,
        "baseline_version": "v0.5",
        "alert_threshold": 0.05,  # 5% drop triggers alert
        "auto_rollback_threshold": 0.10  # 10% drop auto-reverts
    },

    "monitoring": {
        "sample_rate": 0.10,  # Eval 10% of production traffic
        "alert_on_criteria": ["factual_accuracy", "safety_compliance"],
        "human_review_threshold": 0.70  # Scores below 70% flagged for review
    },

    "gradual_rollout": {
        "enabled": True,
        "stages": [
            {"percentage": 0.05, "duration_hours": 24},  # 5% for 24h
            {"percentage": 0.25, "duration_hours": 48},  # 25% for 48h
            {"percentage": 1.0, "duration_hours": None}  # 100%
        ]
    },

    "rollback_plan": {
        "previous_version": "v0.4",
        "automated": True,
        "manual_override": True
    }
}

def deploy_with_safeguards(agent_version: str, safeguards: dict):
    """Deploy new agent version with protection mechanisms."""

    # Establish production baseline
    prod_baseline = run_production_sample_evals(
        sample_size=100,
        version=safeguards["regression_protection"]["baseline_version"]
    )

    # Gradual rollout
    for stage in safeguards["gradual_rollout"]["stages"]:
        print(f"Deploying to {stage['percentage']:.0%} of traffic...")
        route_traffic(agent_version, percentage=stage["percentage"])

        # Monitor during stage
        sleep(hours=stage["duration_hours"])
        current_performance = run_production_sample_evals(
            sample_size=100,
            version=agent_version
        )

        # Check for regression
        regression = detect_regressions(
            baseline=prod_baseline["by_criterion"],
            current=current_performance["by_criterion"],
            threshold_config={
                "drop_threshold": safeguards["regression_protection"]["alert_threshold"]
            }
        )

        # Auto-rollback on severe regression
        if current_performance["aggregate_score"] < (
            prod_baseline["aggregate_score"] -
            safeguards["regression_protection"]["auto_rollback_threshold"]
        ):
            print("🚨 SEVERE REGRESSION DETECTED - AUTO-ROLLBACK")
            rollback_to(safeguards["rollback_plan"]["previous_version"])
            return {"deployed": False, "reason": "auto_rollback", "regression": regression}

        # Alert but continue on minor regression
        if regression["has_regressions"]:
            alert_team(f"Minor regression detected: {regression['regressed_criteria']}")

    return {"deployed": True, "final_performance": current_performance}
```

**Key Safeguards:**

| Safeguard | Purpose | Configuration |
|-----------|---------|---------------|
| **Regression detection** | Catch performance drops early | 5% alert, 10% auto-rollback |
| **Sample evaluation** | Continuous quality monitoring | 10% of production traffic |
| **Gradual rollout** | Limit blast radius | 5% → 25% → 100% over days |
| **Rollback plan** | Quick recovery | Automated with manual override |

#### Step 10: Monitor Production & Grow Dataset

Production deployment isn't the end—it's the beginning of continuous improvement.

**Production Monitoring Loop:**

```python
class ProductionMonitor:
    """Continuous quality monitoring and dataset growth."""

    def __init__(self, eval_suite, alert_config):
        self.eval_suite = eval_suite
        self.alert_config = alert_config
        self.dataset = load_eval_dataset()

    def monitor_production_traffic(self, sample_rate: float = 0.10):
        """Evaluate random sample of production interactions."""

        for interaction in sample_production_stream(rate=sample_rate):
            # Run evaluation on production output
            result = self.eval_suite.grade(
                input=interaction["input"],
                output=interaction["output"]
            )

            # Flag failures for review
            if result["score"] < self.alert_config["human_review_threshold"]:
                self.flag_for_review(interaction, result)

            # Detect novel failure patterns
            if self.is_novel_failure(interaction, result):
                self.add_to_dataset_candidates(interaction, result)

    def flag_for_review(self, interaction: dict, result: dict):
        """Queue low-scoring interactions for human review."""
        review_queue.add({
            "interaction": interaction,
            "score": result["score"],
            "failed_criteria": result["failed_checks"],
            "priority": "high" if result["score"] < 0.50 else "medium"
        })

    def is_novel_failure(self, interaction: dict, result: dict) -> bool:
        """Detect failure patterns not in current eval dataset."""

        # Check if similar case exists in dataset
        similarity_scores = [
            compute_similarity(interaction["input"], case["input"])
            for case in self.dataset
        ]

        max_similarity = max(similarity_scores)

        # Novel if: low score + dissimilar to existing cases
        return (
            result["score"] < 0.70 and
            max_similarity < 0.75  # Not similar to any existing case
        )

    def add_to_dataset_candidates(self, interaction: dict, result: dict):
        """Queue novel failures for dataset addition."""

        candidate = {
            "input": interaction["input"],
            "output": interaction["output"],
            "score": result["score"],
            "failed_criteria": result["failed_checks"],
            "timestamp": interaction["timestamp"],
            "frequency": 1  # Track how often this pattern appears
        }

        dataset_candidates.add(candidate)

    def weekly_dataset_review(self):
        """Review candidates and grow dataset with real failures."""

        # Sort by frequency and severity
        sorted_candidates = sorted(
            dataset_candidates,
            key=lambda c: c["frequency"] * (1 - c["score"]),
            reverse=True
        )

        print(f"📊 {len(sorted_candidates)} dataset candidates this week")

        for candidate in sorted_candidates[:10]:  # Top 10
            print(f"\nCandidate (score: {candidate['score']:.1%}, freq: {candidate['frequency']})")
            print(f"Input: {candidate['input']}")
            print(f"Failed: {candidate['failed_criteria']}")

            # Human decision: Add to dataset?
            if should_add_to_dataset(candidate):
                self.dataset.append({
                    "input": candidate["input"],
                    "expected": create_expected_criteria(candidate),
                    "rationale": f"Production failure pattern: {candidate['failed_criteria']}"
                })

                print("✅ Added to dataset")

        save_eval_dataset(self.dataset)
        print(f"📈 Dataset grown to {len(self.dataset)} cases")

        # Reset candidates after review
        dataset_candidates.clear()
```

**Dataset Growth Strategy:**

| Signal | Action | Rationale |
|--------|--------|-----------|
| **Novel failure pattern** | Add to dataset immediately | Prevents regression in newly discovered edge case |
| **Repeated failure (3+ times)** | High priority addition | Frequency indicates gap in coverage |
| **Critical failure (score <50%)** | Add and investigate urgently | Severe quality issue |
| **Graceful handling** | Lower priority | System working as intended |

**Feedback Loop Closes:**

```
Production Failures → Dataset Growth → Next Iteration Catches Issue → Ship Improved Version
         ↑                                                                        ↓
         └────────────────────────────────────────────────────────────────────────┘
```

**Key Insight**: The best eval datasets are grown organically from production failures, not designed upfront. Initial 20 cases bootstrap the process; production monitoring compounds dataset quality over time.

### Cost Optimization Sequencing

**Critical Principle**: Optimize in strict order: Quality → Latency → Cost. Never reverse.

**Why This Order:**

| Sequence | Result |
|----------|--------|
| Quality → Latency → Cost ✅ | Ship working, fast, cheap agent |
| Quality → Cost → Latency ❌ | Ship working, cheap, slow agent (users complain) |
| Latency → Quality → Cost ❌ | Ship fast, expensive, broken agent |
| Cost → Quality → Latency ❌ | Ship cheap, broken, slow agent (worst) |

**Implementation:**

```python
class OptimizationPhases:
    """Enforce correct optimization sequence."""

    def phase_1_quality(self):
        """Phase 1: Achieve quality threshold (≥90%) regardless of cost/latency."""

        print("🎯 Phase 1: Optimizing for QUALITY")
        print("   Using: claude-opus-4 (most capable, expensive, slow)")

        while self.eval_score < 0.90:
            self.iterate_on_quality()

        print(f"✅ Quality threshold achieved: {self.eval_score:.1%}")
        self.proceed_to_phase_2()

    def phase_2_latency(self):
        """Phase 2: Reduce latency while maintaining quality threshold."""

        print("🎯 Phase 2: Optimizing for LATENCY (quality locked at ≥90%)")

        baseline_latency = measure_p95_latency()
        print(f"   Baseline latency: {baseline_latency}ms")

        optimizations = [
            ("Reduce prompt length", self.try_shorter_prompt),
            ("Parallel tool calls", self.enable_parallel_tools),
            ("Cache common contexts", self.add_prompt_caching),
            ("Streaming responses", self.enable_streaming)
        ]

        for name, optimization in optimizations:
            print(f"\n   Trying: {name}")
            optimization()

            # Verify no quality regression
            new_score = self.run_evals()
            if new_score < 0.90:
                print(f"   ❌ Quality regression: {new_score:.1%} - reverting")
                self.revert()
                continue

            # Measure latency improvement
            new_latency = measure_p95_latency()
            improvement = ((baseline_latency - new_latency) / baseline_latency) * 100
            print(f"   ✅ Latency improved {improvement:.1f}% - keeping change")

        self.proceed_to_phase_3()

    def phase_3_cost(self):
        """Phase 3: Reduce cost while maintaining quality + latency thresholds."""

        print("🎯 Phase 3: Optimizing for COST (quality ≥90%, latency locked)")

        baseline_cost = measure_cost_per_request()
        print(f"   Baseline cost: ${baseline_cost:.4f}/request")

        optimizations = [
            ("Switch to Sonnet (from Opus)", self.try_smaller_model),
            ("Switch to Haiku (from Sonnet)", self.try_smallest_model),
            ("Reduce context window", self.optimize_context),
            ("Cache embeddings", self.add_embedding_cache)
        ]

        for name, optimization in optimizations:
            print(f"\n   Trying: {name}")
            optimization()

            # Verify no quality regression
            new_score = self.run_evals()
            if new_score < 0.90:
                print(f"   ❌ Quality regression: {new_score:.1%} - reverting")
                self.revert()
                continue

            # Verify no latency regression
            new_latency = measure_p95_latency()
            if new_latency > self.latency_threshold:
                print(f"   ❌ Latency regression: {new_latency}ms - reverting")
                self.revert()
                continue

            # Measure cost improvement
            new_cost = measure_cost_per_request()
            savings = ((baseline_cost - new_cost) / baseline_cost) * 100
            print(f"   ✅ Cost reduced {savings:.1f}% - keeping change")

        print(f"\n🎉 Optimization complete:")
        print(f"   Quality: {self.eval_score:.1%}")
        print(f"   Latency: {measure_p95_latency()}ms")
        print(f"   Cost: ${measure_cost_per_request():.4f}/request")
```

**Anti-Pattern Warning:**

```python
# ❌ WRONG: Optimizing cost before quality
agent = Agent(model="haiku")  # Cheap model first
# Now struggling to reach quality threshold with limited model
# Wasted time trying to engineer around capability limitations

# ✅ CORRECT: Achieve quality first
agent = Agent(model="opus")  # Most capable model
# Iterate until quality threshold met
# Then swap to cheaper model, verify quality maintained
# If quality drops, stay with opus
```

**Key Insight**: Quality gates can't be satisfied with capability-limited models. Starting with the most capable model (expensive, slow) establishes the quality ceiling. Then systematically trade capability for speed/cost while maintaining quality threshold. Reversing this order wastes effort trying to engineer around fundamental capability gaps.

### Development Mindset: Analysis Over Coding

**Core Principle**: "Less experienced teams spend a lot of time building and probably much less time analyzing" (Andrew Ng)

**Time Allocation Comparison:**

| Team Experience | Building Time | Analysis Time | Result |
|-----------------|---------------|---------------|--------|
| **Novice** | 80% | 20% | Ship slowly, unclear why failures occur |
| **Intermediate** | 60% | 40% | Ship faster, understand some patterns |
| **Expert** | 40% | 60% | Ship fastest, systematic improvement |

**Why Analysis Dominates:**

```python
# Scenario: Agent has 75% pass rate, goal is 90%

# NOVICE APPROACH (80% building, 20% analysis)
# - Spend 8 hours tweaking prompt based on intuition
# - Run evals: 76% (+1%)
# - Spend 8 more hours adding validation layer
# - Run evals: 74% (-2%, regression!)
# - Spend 8 hours debugging why validation hurt
# - Total: 24 hours for -1% change

# EXPERT APPROACH (40% building, 60% analysis)
# - Spend 6 hours analyzing all failures systematically
# - Discover: 80% of errors from single component (routing)
# - Spend 4 hours fixing routing specifically
# - Run evals: 87% (+12%)
# - Spend 2 hours analyzing remaining gaps
# - Spend 2 hours targeted fix
# - Run evals: 91% (+16%)
# - Total: 14 hours for +16% improvement
```

**Analysis Time Investment Framework:**

```python
@dataclass
class TimeInvestment:
    activity: str
    hours: float
    value_multiplier: float  # How much this accelerates overall progress

RECOMMENDED_TIME_ALLOCATION = [
    TimeInvestment("Error analysis (systematic categorization)", 8.0, 5.0),
    TimeInvestment("Trace review (understanding failure chains)", 6.0, 4.0),
    TimeInvestment("Component attribution (which part failed)", 4.0, 3.0),
    TimeInvestment("Targeted fixing (informed by analysis)", 4.0, 2.0),
    TimeInvestment("Eval execution and comparison", 2.0, 3.0),
    TimeInvestment("Intuition-based tweaking", 1.0, 0.5),  # Avoid
]

def calculate_effective_progress(time_allocation: list[TimeInvestment]) -> float:
    """Calculate progress accounting for value multipliers."""

    return sum(
        investment.hours * investment.value_multiplier
        for investment in time_allocation
    )

# Example comparison
novice_allocation = [
    TimeInvestment("Intuition-based tweaking", 20.0, 0.5),
    TimeInvestment("Error analysis", 2.0, 5.0),
    TimeInvestment("Eval execution", 2.0, 3.0)
]
# Effective progress: 20×0.5 + 2×5 + 2×3 = 26 units in 24 hours

expert_allocation = [
    TimeInvestment("Error analysis", 8.0, 5.0),
    TimeInvestment("Trace review", 6.0, 4.0),
    TimeInvestment("Component attribution", 4.0, 3.0),
    TimeInvestment("Targeted fixing", 4.0, 2.0),
    TimeInvestment("Eval execution", 2.0, 3.0)
]
# Effective progress: 8×5 + 6×4 + 4×3 + 4×2 + 2×3 = 82 units in 24 hours
# 3.15x more effective progress in same time
```

**Mindset Shift Exercises:**

| Old Habit | New Habit |
|-----------|-----------|
| "Let me try changing the prompt" | "Let me analyze which 10 cases failed and why" |
| "This component feels wrong" | "This component failed in 8/20 cases (40% failure rate)" |
| "I'll add more validation" | "Validation won't fix the root cause (tool selection)" |
| "Run evals at the end" | "Run evals after every change to isolate impact" |
| "We need more test cases" | "We need to understand why existing cases fail" |

**Key Insight**: Thirty minutes counting errors outperforms thirty hours fixing the wrong component. Analysis provides certainty about what to fix; intuition provides guesses. Expert teams achieve faster shipping velocity precisely because they invest more time in analysis upfront, preventing wasted effort on wrong fixes.

## Integration

This skill connects to:
- SDK-specific evaluation modules (OpenAI, Claude, Google ADK)
- Observability skills for trace analysis
- CI/CD skills for automated eval runs

---

*Status: Production-ready - Complete framework with end-to-end quality loop (Evals vs TDD, Two Evaluation Axes, Four Quadrants, Graders, Grader Validation, Error Analysis, Dataset Design, Regression Protection, Complete Quality Loop)*