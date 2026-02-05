# Grader Implementation Roadmap

## Implementation Roadmap

### Week 1: Q1 Code Graders (Priority)

- [x] Implement `routing_grader` (covers 7 cases) ✓ - 100% pass rate
- [x] Implement `input_guardrail_grader` (2 cases) ✓ - 100% pass rate
- [ ] Implement `tool_usage_grader` (2 cases)
- [ ] Implement `citation_grader` (1 case)
- [ ] Implement `output_guardrail_grader` (1 case)
- [ ] Implement `routing_flexible_grader` (1 case)
- [ ] **Run baseline evaluation on 10 cases**

### Week 2: Q2 LLM Graders

- [ ] Implement `response_quality_grader` (3 cases)
- [ ] **Validate against 20 human ratings** (target: ≥70% exact match)
- [ ] Iterate on prompts if validation fails
- [ ] **Run full baseline on 11 cases**

### Week 3: Q4 Complex Graders

- [ ] Implement 4 complex scenario graders (case 13)
- [ ] **Validate against human ratings**
- [ ] **Run complete baseline on all 13 cases**
- [ ] Document baseline for regression protection

---

## Key Takeaways for Your Implementation

1. **Start with Q1** - 6 code graders cover 10/13 cases (77%) and are fastest to build
2. **Validate Q2/Q4** - LLM judges need human calibration before production use
3. **Sequence execution** - Run cheap code graders first, expensive LLM judges only if code checks pass
4. **Standardize output** - All graders return `{passed, score, checks, failed_checks}`
5. **Use binary criteria** - YES/NO questions are more reliable than numeric scales
