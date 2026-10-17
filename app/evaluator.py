"""
Measures execution accuracy on the eval set, split into dev and test.

Usage:
    python -m app.evaluator dev    (default, safe for tuning)
    python -m app.evaluator test   (final exam)
"""

import json
import sys
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from itertools import permutations

from app.agent import run_agent
from app.sql_executor import execute_sql

# Folder that holds the eval cases and the saved reports
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EVAL_FILE = DATA_DIR / "eval_cases.json"


def normalize_value(value):
    """Turning one database value into a string that can be compared fairly."""

    # Booleans are a kind of int in Python, so handling them first
    if isinstance(value, bool):
        return str(value)

    # Numbers: round to 2 decimals so ROUND() vs no ROUND() still matches
    if isinstance(value, (int, float, Decimal)):
        return f"{round(float(value), 2):.2f}"

    # Everything else (text, dates, None): compare as trimmed text
    return str(value).strip()


def normalize_rows(rows):
    """Turn each row into a list of normalized strings, keeping column order."""
    return [[normalize_value(value) for value in row.values()] for row in rows]


def rows_match(actual_rows, expected_rows, ordered):
    """
    Compare two result sets.

    The agent may return extra columns or columns in a different order.
    Every expected column must still appear, with matching values row by row.
    """

    actual = normalize_rows(actual_rows)
    expected = normalize_rows(expected_rows)

    # Different row counts can never match
    if len(actual) != len(expected):
        return False

    # Both empty means they match
    if not expected:
        return True

    num_expected = len(expected[0])
    num_actual = len(actual[0])

    # The agent must return at least as many columns as expected
    if num_actual < num_expected:
        return False

    # Without a ranking, row order does not matter
    if not ordered:
        expected = sorted(expected)

    # Try every way of picking and ordering the agent's columns
    for indexes in permutations(range(num_actual), num_expected):
        projected = [[row[i] for i in indexes] for row in actual]

        if not ordered:
            projected = sorted(projected)

        if projected == expected:
            return True

    return False


def evaluate_case(case):
    """Running one question through the agent and grade the outcome."""

    # Start with the fields every result needs
    result = {
        "id": case["id"],
        "split": case["split"],
        "tier": case["tier"],
        "question": case["question"],
        "is_correct": False,
        "failure_reason": "",
        "generated_sql": None,
        "agent_answer": "",
        "expected_rows": [],
        "actual_rows": [],
        "attempts": 0,
    }

    # Run the agent. A crash counts as a failure but must not stop the evaluation.
    try:
        response = run_agent(case["question"])
    except Exception as error:
        result["failure_reason"] = f"agent crashed: {error}"
        return result

    result["generated_sql"] = response.get("sql")
    result["agent_answer"] = response.get("answer", "")
    result["attempts"] = response.get("attempts", 0)

    # The agent asked the user to clarify instead of writing SQL
    asked_clarification = response.get("is_clear") is False

    # Case 1: the question is ambiguous, so the right behavior is to ask
    if case["expect_clarification"]:
        if asked_clarification:
            result["is_correct"] = True
        else:
            result["failure_reason"] = "should have asked for clarification"
        return result

    # Case 2: the question is clear, so asking for clarification is a failure
    if asked_clarification:
        result["failure_reason"] = "asked for clarification on a clear question"
        return result

    # Case 3: compare the agent's rows with the trusted reference rows
    expected_rows = execute_sql(case["reference_sql"])["rows"]
    actual_rows = response.get("result", {}).get("rows", [])

    result["expected_rows"] = expected_rows
    result["actual_rows"] = actual_rows

    if rows_match(actual_rows, expected_rows, case["ordered"]):
        result["is_correct"] = True
    else:
        result["failure_reason"] = "result rows differ from reference"

    return result


def run_evaluation(split):
    """Evaluate all cases in a split, print a summary, and save a report."""

    with open(EVAL_FILE, encoding="utf-8") as file:
        cases = json.load(file)

    # Keep only the requested split ("all" keeps everything)
    if split != "all":
        cases = [case for case in cases if case["split"] == split]

    results = []

    for case in cases:
        result = evaluate_case(case)
        results.append(result)

        status = "PASS" if result["is_correct"] else "FAIL"
        print(f"{status} {case['id']}: {case['question']}")

        # For failures, show what went wrong and the SQL the agent wrote
        if not result["is_correct"]:
            print(f"     reason: {result['failure_reason']}")
            print(f"     sql:    {result['generated_sql']}")
            print(f"     answer: {result['agent_answer'][:200]}")

    # Count passes overall and per tier
    passed = sum(result["is_correct"] for result in results)
    total = len(results)
    accuracy = (passed / total) * 100

    by_tier = defaultdict(lambda: {"passed": 0, "total": 0})
    for result in results:
        by_tier[result["tier"]]["total"] += 1
        by_tier[result["tier"]]["passed"] += int(result["is_correct"])

    print("\n" + "=" * 40)
    print(f"Split: {split}")
    for tier, counts in by_tier.items():
        print(f"  {tier}: {counts['passed']}/{counts['total']}")
    print(f"Execution accuracy: {passed}/{total} ({accuracy:.1f}%)")

    # Save the report (the API reads eval_results_test.json for /metrics)
    report = {
        "evaluated_at": datetime.now().astimezone().isoformat(),
        "split": split,
        "passed_cases": passed,
        "total_cases": total,
        "execution_accuracy_percent": accuracy,
        "by_tier": dict(by_tier),
        "results": results,
    }

    report_file = DATA_DIR / f"eval_results_{split}.json"
    with open(report_file, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, default=str)

    print(f"Saved report: {report_file}")

    return report


if __name__ == "__main__":
    # Default to dev so the test split is never run by accident
    chosen_split = sys.argv[1] if len(sys.argv) > 1 else "dev"

    if chosen_split not in ("dev", "test", "all"):
        raise SystemExit("Split must be dev, test, or all.")

    run_evaluation(chosen_split)