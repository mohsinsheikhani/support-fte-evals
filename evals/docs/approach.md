# Eval Implementation Roadmap

## Phase 1: Understand What You're Evaluating

Before writing any code, map your agent's behaviors to evaluation quadrants:

| Behavior to Evaluate | Question to Ask | Quadrant |
|----------------------|-----------------|----------|
| Does triage route to correct agent? | "Is there one correct answer?" → YES | Q1 (Code grader) |
| Does PII guardrail trigger? | "Can code verify?" → YES | Q1 (Code grader) |
| Is the response helpful? | "Requires judgment?" → YES | Q4 (LLM judge) |
| Does agent use correct tool? | "One correct answer?" → YES | Q1 (Code grader) |

**Your first task**: List all behaviors your agent should exhibit and classify each into a quadrant.

---

## Phase 2: Design Your Dataset (Start with 20 cases)

Use the **Three-Category Framework**:

```
Typical (10 cases)  → Common scenarios your agent was built for
Edge (5 cases)      → Unusual but valid requests
Error (5 cases)     → Requests that should fail gracefully
```

For your Customer Support FTE, consider:

### Typical Cases (10)
- FAQ question about pricing
- FAQ question about refund policy
- Billing inquiry (check charges)
- Refund request under $100
- Technical issue (API error)
- Customer identification flow
- Multi-turn conversation
- etc.

### Edge Cases (5)
- Ambiguous intent (could be billing OR technical)
- Customer not found in system
- Mixed request (billing + technical in one message)
- etc.

### Error Cases (5)
- Credit card number in message (PII guardrail)
- SSN in message (PII guardrail)
- Prompt injection attempt
- Request to speak to human immediately
- etc.

**Your second task**: Create a JSON file with 20 test cases, each having:

```json
{
    "input": "User message here",
    "expected_agent": "FAQAgent",
    "expected_guardrail": null,
    "category": "typical",
    "rationale": "Why this case exists"
}
```

---

## Phase 3: Build Your Graders

**Start with Q1 graders (code-based)** - they're cheapest and fastest:

1. **Routing Grader**: Check if `result["agent_used"]` matches `expected_agent`
2. **Guardrail Grader**: Check if `result["guardrail_triggered"]` matches expectation
3. **Tool Call Grader**: Check if expected tools were called (requires trace inspection)

**Then add Q4 graders (LLM-as-judge)** for subjective criteria:

4. **Helpfulness Grader**: Use 5-7 binary YES/NO questions
5. **Tone Grader**: Professional? Empathetic? Not robotic?

**Your third task**: Implement graders one at a time. Start with the routing grader since your `handle_message()` already returns `agent_used`.

---

## Phase 4: Run Evals & Establish Baseline

```python
# Pseudocode structure
async def run_eval_suite(dataset):
    results = []
    for case in dataset:
        output = await handle_message(case["input"])

        # Run graders
        routing_score = grade_routing(output, case)
        guardrail_score = grade_guardrail(output, case)
        # ... more graders

        results.append({
            "case_id": case["id"],
            "scores": {...},
            "passed": all_checks_passed
        })

    return aggregate_results(results)
```

**Your fourth task**: Create a simple eval runner that:
1. Loads your dataset
2. Runs each case through `handle_message()`
3. Applies graders
4. Outputs pass/fail per criterion

---

## Phase 5: Error Analysis

After running evals, you'll have failures. **Don't immediately fix them.** Instead:

1. **Count failures by component**: Which agent/guardrail/tool failed most?
2. **Categorize failure modes**: Graceful vs Confident-Wrong vs Partial
3. **Prioritize**: Frequency × Feasibility = Priority Score

**Your fifth task**: Create a simple spreadsheet or dict to track:

| Case | Routing | Guardrail | Helpfulness | Error Location |
|------|---------|-----------|-------------|----------------|
| 1    | PASS    | PASS      | FAIL        | helpfulness    |
| 2    | FAIL    | -         | -           | routing        |

---

## Suggested File Structure

```
evals/
├── dataset.json        # Your 20 test cases
├── graders/
│   ├── routing.py      # Q1: Check agent routing
│   ├── guardrails.py   # Q1: Check guardrail triggers
│   ├── tools.py        # Q1: Check tool usage
│   └── quality.py      # Q4: LLM-as-judge for helpfulness/tone
├── runner.py           # Runs dataset through agent + graders
├── analysis.py         # Error analysis utilities
└── baseline.json       # Saved baseline results
```

---

## Where to Start (Today)

1. Create `evals/dataset.json` with your 20 cases
2. Create `evals/graders/routing.py` - simplest grader, just check `agent_used`
3. Create `evals/runner.py` - loop through dataset, run agent, apply grader
4. Run it and see your first baseline score
