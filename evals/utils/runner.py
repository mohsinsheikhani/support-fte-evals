"""Evaluation runner - executes dataset through agent and graders."""

import asyncio
import json
from pathlib import Path


def load_dataset(path: str = "dataset.json") -> dict:
    """Load evaluation dataset from JSON."""
    with open(Path(__file__).parent / path) as f:
        return json.load(f)


def save_results(results: dict, path: str = "results.json"):
    """Save evaluation results to JSON."""
    with open(Path(__file__).parent / path, "w") as f:
        json.dump(results, f, indent=2)


async def run_single_case(case: dict) -> dict:
    """
    Run a single evaluation case.

    Args:
        case: Test case from dataset

    Returns:
        dict with case_id, output, and grader scores
    """
    # TODO: Import and call handle_message
    # from src.main import handle_message
    # output = await handle_message(case["input"])

    # TODO: Run graders
    # routing_result = grade_routing(output, case)
    # guardrail_result = grade_guardrail(output, case)

    # TODO: Return structured result
    pass


async def run_eval_suite(dataset: dict) -> dict:
    """
    Run full evaluation suite.

    Args:
        dataset: Loaded dataset with cases

    Returns:
        dict with aggregate scores and per-case results
    """
    results = []

    for case in dataset["cases"]:
        # TODO: Run each case and collect results
        pass

    # TODO: Aggregate results
    # - Overall pass rate
    # - Per-criterion scores
    # - Failed case IDs

    return {
        "aggregate": {},
        "by_criterion": {},
        "cases": results
    }


async def main():
    """Run evaluation and save results."""
    print("Loading dataset...")
    dataset = load_dataset()

    print(f"Running {len(dataset['cases'])} cases...")
    results = await run_eval_suite(dataset)

    print("Saving results...")
    save_results(results)

    # Print summary
    print("\n" + "=" * 40)
    print("EVALUATION SUMMARY")
    print("=" * 40)
    # TODO: Print aggregate scores


if __name__ == "__main__":
    asyncio.run(main())
