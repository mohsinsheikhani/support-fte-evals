"""Regression Protection: Comparison & Detection Engine.

Compares eval runs against a baseline to detect regressions.
Implements the 4 core components:
  1. EvalRun — stores eval results
  2. compare_versions() — computes deltas
  3. RegressionConfig — thresholds
  4. check_regression() — returns BLOCK/WARN/SHIP
  5. identify_improvement_target() — finds weakest criterion

Thresholds: 5% overall, 10% per-criterion (standard for customer support agents).
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class EvalRun:
    """Stores eval results with per-criterion breakdown."""

    passed: int
    total: int
    pass_rate: float
    by_criterion: dict[str, float] = field(default_factory=dict)  # grader_name -> pass_rate


@dataclass
class RegressionConfig:
    """Thresholds for regression detection."""

    overall_threshold: float = 0.05  # 5% overall drop triggers regression
    criterion_threshold: float = 0.10  # 10% per-criterion drop triggers regression
    block_on_regression: bool = True  # Exit non-zero on regression


def results_to_eval_run(results: dict[str, Any]) -> EvalRun:
    """Convert our results dict (from JSON) to EvalRun.

    Our JSON format:
    {
        "total_cases": 14,
        "total_passed": 14,
        "overall_pass_rate": 1.0,
        "grader_summaries": {
            "routing": {"total": 7, "passed": 7, "pass_rate": 1.0},
            ...
        }
    }
    """
    by_criterion = {}
    for grader_name, summary in results.get("grader_summaries", {}).items():
        by_criterion[grader_name] = summary["pass_rate"]

    return EvalRun(
        passed=results["total_passed"],
        total=results["total_cases"],
        pass_rate=results["overall_pass_rate"],
        by_criterion=by_criterion,
    )


def load_baseline(path: str) -> EvalRun:
    """Load baseline results JSON and convert to EvalRun."""
    with open(path) as f:
        data = json.load(f)
    return results_to_eval_run(data)


def compare_versions(baseline: EvalRun, current: EvalRun) -> dict[str, Any]:
    """Compare current eval run against baseline.

    Returns:
        dict with overall_delta, per_criterion deltas, regressions, improvements, additions
    """
    overall_delta = current.pass_rate - baseline.pass_rate

    per_criterion = {}
    regressions = []
    improvements = []
    additions = []

    # Check all criteria in current run
    for criterion, current_rate in current.by_criterion.items():
        if criterion in baseline.by_criterion:
            baseline_rate = baseline.by_criterion[criterion]
            delta = current_rate - baseline_rate
            per_criterion[criterion] = {
                "baseline": baseline_rate,
                "current": current_rate,
                "delta": delta,
            }
            if delta < 0:
                regressions.append(criterion)
            elif delta > 0:
                improvements.append(criterion)
        else:
            # New criterion not in baseline — report as addition, not regression
            per_criterion[criterion] = {
                "baseline": None,
                "current": current_rate,
                "delta": None,
            }
            additions.append(criterion)

    # Check for removed criteria (in baseline but not current)
    removed = []
    for criterion in baseline.by_criterion:
        if criterion not in current.by_criterion:
            removed.append(criterion)

    return {
        "overall_delta": overall_delta,
        "baseline_pass_rate": baseline.pass_rate,
        "current_pass_rate": current.pass_rate,
        "per_criterion": per_criterion,
        "regressions": regressions,
        "improvements": improvements,
        "additions": additions,
        "removed": removed,
    }


def check_regression(
    comparison: dict[str, Any], config: RegressionConfig | None = None
) -> dict[str, Any]:
    """Check if regressions exceed thresholds.

    Returns:
        dict with passed, should_block, issues, recommendation (BLOCK/WARN/SHIP)
    """
    if config is None:
        config = RegressionConfig()

    issues = []

    # Check overall regression
    overall_delta = comparison["overall_delta"]
    if overall_delta < -config.overall_threshold:
        issues.append(
            f"Overall pass rate dropped {abs(overall_delta)*100:.1f}% "
            f"(threshold: {config.overall_threshold*100:.1f}%)"
        )

    # Check per-criterion regressions
    for criterion in comparison["regressions"]:
        info = comparison["per_criterion"][criterion]
        delta = info["delta"]
        if abs(delta) > config.criterion_threshold:
            issues.append(
                f"{criterion}: dropped {abs(delta)*100:.1f}% "
                f"({info['baseline']*100:.1f}% -> {info['current']*100:.1f}%, "
                f"threshold: {config.criterion_threshold*100:.1f}%)"
            )

    # Determine recommendation
    if issues:
        passed = False
        should_block = config.block_on_regression
        recommendation = "BLOCK" if should_block else "WARN"
    else:
        passed = True
        should_block = False
        # Minor regressions exist but below threshold?
        if comparison["regressions"]:
            recommendation = "WARN"
        else:
            recommendation = "SHIP"

    return {
        "passed": passed,
        "should_block": should_block,
        "issues": issues,
        "recommendation": recommendation,
    }


def identify_improvement_target(eval_result: EvalRun) -> str | None:
    """Find the criterion with the lowest pass rate (the iteration loop target).

    Returns:
        Name of the weakest criterion, or None if no criteria exist.
    """
    if not eval_result.by_criterion:
        return None

    return min(eval_result.by_criterion, key=eval_result.by_criterion.get)


def print_regression_report(comparison: dict[str, Any], check_result: dict[str, Any]):
    """Print human-readable regression report with per-grader delta table."""
    rec = check_result["recommendation"]
    symbols = {"SHIP": "+", "WARN": "~", "BLOCK": "!"}
    symbol = symbols.get(rec, "?")

    print(f"\n{'='*70}")
    print(f"REGRESSION CHECK: [{symbol}] {rec}")
    print(f"{'='*70}\n")

    # Overall
    baseline = comparison["baseline_pass_rate"]
    current = comparison["current_pass_rate"]
    delta = comparison["overall_delta"]
    delta_str = f"+{delta*100:.1f}%" if delta >= 0 else f"{delta*100:.1f}%"
    print(f"Overall: {baseline*100:.1f}% -> {current*100:.1f}% ({delta_str})\n")

    # Per-criterion delta table
    print(f"{'Grader':<25s} {'Baseline':>10s} {'Current':>10s} {'Delta':>10s}  Status")
    print(f"{'─'*70}")

    for criterion, info in comparison["per_criterion"].items():
        if info["baseline"] is not None:
            b = f"{info['baseline']*100:.1f}%"
            c = f"{info['current']*100:.1f}%"
            d = info["delta"]
            d_str = f"+{d*100:.1f}%" if d >= 0 else f"{d*100:.1f}%"

            if d < 0:
                status = "REGRESSION"
            elif d > 0:
                status = "IMPROVED"
            else:
                status = "STABLE"
        else:
            b = "N/A"
            c = f"{info['current']*100:.1f}%"
            d_str = "NEW"
            status = "NEW"

        print(f"{criterion:<25s} {b:>10s} {c:>10s} {d_str:>10s}  {status}")

    # Additions
    if comparison["additions"]:
        print(f"\nNew criteria: {', '.join(comparison['additions'])}")

    # Removed
    if comparison["removed"]:
        print(f"Removed criteria: {', '.join(comparison['removed'])}")

    # Issues
    if check_result["issues"]:
        print(f"\nIssues ({len(check_result['issues'])}):")
        for issue in check_result["issues"]:
            print(f"  ! {issue}")

    # Recommendation
    print(f"\nRecommendation: {rec}")
    if rec == "BLOCK":
        print("  Regressions exceed thresholds. Fix before deploying.")
    elif rec == "WARN":
        print("  Minor regressions detected but within thresholds.")
    else:
        print("  No regressions detected. Safe to deploy.")

    print(f"{'='*70}\n")
