"""
Programmatic Error Analysis System

Automates systematic error analysis following eval-driven development methodology.
Eliminates manual counting errors and generates reports automatically.

Usage:
    from error_analyzer import AnalyzedCase, analyze_failures, prioritize_fixes

    cases = [
        AnalyzedCase("1", "none", {}),
        AnalyzedCase("2", "TriageAgent.routing", {...}),
    ]

    report = analyze_failures(cases)
    priorities = prioritize_fixes(report, {"TriageAgent.routing": 0.9})
"""

from dataclasses import dataclass, field
from collections import Counter
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class AnalyzedCase:
    """
    Represents a single analyzed test case with complete trace data.

    Attributes:
        case_id: Unique identifier for the test case
        error_location: Which span/component failed (e.g., "TriageAgent.routing", "none" if passed)
        trace: Complete execution trace with all spans
        upstream_issue: Whether failure was due to degraded upstream input
        root_cause: Human-readable description of why it failed
        input_text: Original user input
        expected_output: What we expected
        actual_output: What we got
        passed: Whether the test passed
    """
    case_id: str
    error_location: str  # "none" for passed cases, "Component.span" for failures
    trace: Dict[str, Any]
    upstream_issue: bool = False
    root_cause: str = ""
    input_text: str = ""
    expected_output: Any = None
    actual_output: Any = None
    passed: bool = False

    def __post_init__(self):
        """Validate that passed cases have error_location='none'"""
        if self.passed and self.error_location != "none":
            raise ValueError(f"Passed case {self.case_id} should have error_location='none'")
        if not self.passed and self.error_location == "none":
            raise ValueError(f"Failed case {self.case_id} should have error_location specified")


def analyze_failures(cases: List[AnalyzedCase]) -> Dict[str, Any]:
    """
    Generate error report from analyzed cases.

    Automatically counts failures by component and calculates percentages.

    Args:
        cases: List of AnalyzedCase objects

    Returns:
        dict with:
            - total_cases: Total number of cases
            - failures: Number of failed cases
            - passed: Number of passed cases
            - failure_rate: Percentage of failures
            - pass_rate: Percentage of passes
            - breakdown: Dict of {component: {count, percentage}}
            - top_priority: Component with most failures
            - upstream_issues: Count of failures due to upstream degradation

    Example:
        >>> cases = [
        ...     AnalyzedCase("1", "none", {}, passed=True),
        ...     AnalyzedCase("2", "TriageAgent.routing", {}, passed=False),
        ...     AnalyzedCase("3", "TriageAgent.routing", {}, passed=False),
        ... ]
        >>> report = analyze_failures(cases)
        >>> report["failure_rate"]
        0.6666666666666666
        >>> report["breakdown"]["TriageAgent.routing"]["percentage"]
        100.0
    """
    failed_cases = [c for c in cases if c.error_location != "none"]
    passed_cases = [c for c in cases if c.error_location == "none"]

    total_cases = len(cases)
    total_failures = len(failed_cases)
    total_passed = len(passed_cases)

    if total_failures == 0:
        return {
            "total_cases": total_cases,
            "failures": 0,
            "passed": total_passed,
            "failure_rate": 0.0,
            "pass_rate": 1.0,
            "breakdown": {},
            "top_priority": None,
            "upstream_issues": 0,
        }

    # Count failures by component
    error_counts = Counter(case.error_location for case in failed_cases)

    # Count upstream issues
    upstream_count = sum(1 for case in failed_cases if case.upstream_issue)

    # Calculate percentages of total failures
    error_percentages = {
        location: {
            "count": count,
            "percentage": (count / total_failures) * 100,
            "percentage_of_total": (count / total_cases) * 100,
        }
        for location, count in error_counts.most_common()
    }

    return {
        "total_cases": total_cases,
        "failures": total_failures,
        "passed": total_passed,
        "failure_rate": total_failures / total_cases,
        "pass_rate": total_passed / total_cases,
        "breakdown": error_percentages,
        "top_priority": error_counts.most_common(1)[0][0] if error_counts else None,
        "upstream_issues": upstream_count,
        "upstream_percentage": (upstream_count / total_failures * 100) if total_failures > 0 else 0,
    }


def prioritize_fixes(
    error_report: Dict[str, Any],
    feasibility: Dict[str, float]
) -> List[Dict[str, Any]]:
    """
    Rank components by priority = frequency × feasibility.

    Args:
        error_report: Output from analyze_failures()
        feasibility: Dict mapping component names to feasibility scores (0.0-1.0)
            - 1.0 = Trivial (config change, 5 min)
            - 0.9 = Easy (prompt adjustment, 15-30 min)
            - 0.7 = Moderate (small code change, 1-2h)
            - 0.5 = Hard (architecture change, 4-8h)
            - 0.3 = Very hard (research needed, days)

    Returns:
        List of dicts sorted by priority_score (highest first):
            - component: Component name
            - frequency: Failure frequency (0.0-1.0)
            - feasibility: Feasibility score (0.0-1.0)
            - priority_score: frequency × feasibility
            - count: Number of failures
            - percentage: Percentage of failures

    Example:
        >>> report = {"breakdown": {"CompA": {"count": 5, "percentage": 71.4}}}
        >>> feasibility = {"CompA": 0.9}
        >>> priorities = prioritize_fixes(report, feasibility)
        >>> priorities[0]["priority_score"]
        0.6426
    """
    priorities = []

    for location, data in error_report["breakdown"].items():
        freq = data["percentage"] / 100  # Convert to 0.0-1.0
        feas = feasibility.get(location, 0.5)  # Default to moderate if not specified

        priorities.append({
            "component": location,
            "frequency": freq,
            "feasibility": feas,
            "priority_score": freq * feas,
            "count": data["count"],
            "percentage": data["percentage"],
        })

    # Sort by priority score (highest first)
    return sorted(priorities, key=lambda x: x["priority_score"], reverse=True)


def generate_markdown_report(
    cases: List[AnalyzedCase],
    error_report: Dict[str, Any],
    priorities: List[Dict[str, Any]],
    iteration: int = 1,
    grader_name: str = "Unknown"
) -> str:
    """
    Generate markdown report from analysis data.

    Args:
        cases: List of AnalyzedCase objects
        error_report: Output from analyze_failures()
        priorities: Output from prioritize_fixes()
        iteration: Iteration number
        grader_name: Name of the grader being analyzed

    Returns:
        Markdown-formatted report string
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    md = [
        f"# Error Analysis Report - {grader_name}",
        f"",
        f"**Iteration**: {iteration}",
        f"**Generated**: {timestamp}",
        f"**Total Cases**: {error_report['total_cases']}",
        f"**Pass Rate**: {error_report['pass_rate']:.1%} ({error_report['passed']}/{error_report['total_cases']})",
        f"**Failure Rate**: {error_report['failure_rate']:.1%} ({error_report['failures']}/{error_report['total_cases']})",
        f"",
        f"---",
        f"",
        f"## Failure Breakdown",
        f"",
    ]

    if error_report["failures"] == 0:
        md.append("**✓ All tests passing!**")
        md.append("")
        return "\n".join(md)

    # Frequency table
    md.append("| Component | Failures | Frequency (of failures) | Frequency (of total) |")
    md.append("|-----------|----------|------------------------|---------------------|")

    for location, data in sorted(
        error_report["breakdown"].items(),
        key=lambda x: x[1]["count"],
        reverse=True
    ):
        md.append(
            f"| {location} | {data['count']} | "
            f"{data['percentage']:.1f}% | "
            f"{data['percentage_of_total']:.1f}% |"
        )

    md.append("")
    md.append(f"**Top Priority**: {error_report['top_priority']}")
    md.append(f"**Upstream Issues**: {error_report['upstream_issues']} "
              f"({error_report['upstream_percentage']:.1f}% of failures)")
    md.append("")
    md.append("---")
    md.append("")

    # Prioritization table
    if priorities:
        md.append("## Fix Prioritization")
        md.append("")
        md.append("**Priority = Frequency × Feasibility**")
        md.append("")
        md.append("| Rank | Component | Frequency | Feasibility | Priority Score |")
        md.append("|------|-----------|-----------|-------------|----------------|")

        for i, priority in enumerate(priorities, 1):
            md.append(
                f"| #{i} | {priority['component']} | "
                f"{priority['frequency']:.2f} | "
                f"{priority['feasibility']:.1f} | "
                f"**{priority['priority_score']:.3f}** |"
            )

        md.append("")
        md.append(f"**Recommended Fix**: {priorities[0]['component']} "
                  f"(Priority: {priorities[0]['priority_score']:.3f})")
        md.append("")
        md.append("---")
        md.append("")

    # Failed cases detail
    md.append("## Failed Cases Detail")
    md.append("")

    failed_cases = [c for c in cases if not c.passed]
    for case in failed_cases:
        md.append(f"### Case {case.case_id}")
        md.append(f"")
        md.append(f"**Input**: {case.input_text[:100]}...")
        md.append(f"**Error Location**: {case.error_location}")
        md.append(f"**Upstream Issue**: {'Yes' if case.upstream_issue else 'No'}")
        if case.root_cause:
            md.append(f"**Root Cause**: {case.root_cause}")
        md.append(f"")

    return "\n".join(md)


def generate_spreadsheet_table(cases: List[AnalyzedCase], components: List[str]) -> str:
    """
    Generate component-level spreadsheet in markdown format.

    Args:
        cases: List of AnalyzedCase objects
        components: List of component names in execution order

    Returns:
        Markdown table string
    """
    # Header
    header = "| Case | " + " | ".join(components) + " | Error Location |"
    separator = "|------|" + "|".join(["--------"] * len(components)) + "|----------------|"

    rows = [header, separator]

    for case in cases:
        row_data = [case.case_id]

        for comp in components:
            if case.passed:
                row_data.append("✓")
            elif case.error_location.startswith(comp):
                row_data.append("✗")
            elif any(case.error_location.startswith(prev) for prev in components[:components.index(comp)]):
                row_data.append("-")
            else:
                row_data.append("✓")

        row_data.append(case.error_location if not case.passed else "None")
        rows.append("| " + " | ".join(str(x) for x in row_data) + " |")

    return "\n".join(rows)


def compare_iterations(
    baseline_report: Dict[str, Any],
    current_report: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compare two error reports to track improvement.

    Args:
        baseline_report: Error report from previous iteration
        current_report: Error report from current iteration

    Returns:
        dict with comparison metrics
    """
    return {
        "pass_rate_change": current_report["pass_rate"] - baseline_report["pass_rate"],
        "failure_count_change": current_report["failures"] - baseline_report["failures"],
        "improved": current_report["pass_rate"] > baseline_report["pass_rate"],
        "baseline_pass_rate": baseline_report["pass_rate"],
        "current_pass_rate": current_report["pass_rate"],
        "percentage_improvement": (
            (current_report["pass_rate"] - baseline_report["pass_rate"])
            / baseline_report["pass_rate"] * 100
            if baseline_report["pass_rate"] > 0 else 0
        ),
    }


# Example usage and test
if __name__ == "__main__":
    # Example: Routing grader baseline analysis
    print("Example: Routing Grader Baseline Analysis\n")

    baseline_cases = [
        AnalyzedCase("1", "none", {}, passed=True, input_text="What's your refund policy?"),
        AnalyzedCase("2", "TriageAgent.identity_check", {}, passed=False,
                    input_text="How secure is customer data?",
                    root_cause="Triage asks for email before routing",
                    upstream_issue=False),
        AnalyzedCase("4", "TriageAgent.identity_check", {}, passed=False,
                    input_text="Guide me on pricing?",
                    root_cause="Triage asks for email before routing",
                    upstream_issue=False),
        AnalyzedCase("5", "TriageAgent.identity_check", {}, passed=False,
                    input_text="I was charged twice",
                    root_cause="Triage asks for email before routing",
                    upstream_issue=False),
        AnalyzedCase("6", "TriageAgent.identity_check", {}, passed=False,
                    input_text="Getting 500 error",
                    root_cause="Triage asks for email before routing",
                    upstream_issue=False),
        AnalyzedCase("8", "TriageAgent.identity_check", {}, passed=False,
                    input_text="I'm alice@example.com, refund $50",
                    root_cause="Triage asks for email even though provided",
                    upstream_issue=False),
        AnalyzedCase("9", "none", {}, passed=True,
                    input_text="I'm alice@example.com, refund $150"),
    ]

    # Analyze failures
    report = analyze_failures(baseline_cases)

    print(f"Total Cases: {report['total_cases']}")
    print(f"Pass Rate: {report['pass_rate']:.1%}")
    print(f"Failures: {report['failures']}")
    print(f"\nBreakdown:")
    for component, data in report['breakdown'].items():
        print(f"  {component}: {data['count']} ({data['percentage']:.1f}%)")

    # Prioritize fixes
    feasibility = {
        "TriageAgent.identity_check": 0.9,  # Easy - prompt change
    }

    priorities = prioritize_fixes(report, feasibility)

    print(f"\nPrioritization:")
    for i, p in enumerate(priorities, 1):
        print(f"  #{i} {p['component']}: Priority {p['priority_score']:.3f} "
              f"(freq={p['frequency']:.2f}, feas={p['feasibility']:.1f})")

    # Generate markdown report
    print("\n" + "="*60)
    print("MARKDOWN REPORT:")
    print("="*60 + "\n")

    md_report = generate_markdown_report(baseline_cases, report, priorities,
                                         iteration=1, grader_name="routing_grader")
    print(md_report)
