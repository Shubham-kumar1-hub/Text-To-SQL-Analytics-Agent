""" 
Measuring execution accuracy by comparing agent results with trusted SQL results.
"""

import json
from pathlib import Path
from datetime import datetime

from app.agent import run_agent
from app.sql_executor import execute_sql


# Finding the evaluation file relative to the project root.
EVALUATION_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "evaluation_cases.json"
)

RESULTS_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "evaluation_results.json"
)

def normalize_rows(rows):
    """Comparing result values while ignoring SQL column aliases."""

    return [
        tuple(str(value) for value in row.values())
        for row in rows
    ]

def evaluate_case(case):
    """Running one question and comparing agent output with trusted SQL output."""

    # The reference query provides the expected database result.
    expected_result = execute_sql(case["reference_sql"])
    expected_rows = expected_result["rows"]

    # Running the complete LangGraph agent.
    agent_response = run_agent(case["question"])
    actual_rows = agent_response.get("result", {}).get("rows", [])

    is_correct = normalize_rows(actual_rows) == normalize_rows(expected_rows)

    return {
        "id": case["id"],
        "question": case["question"],
        "is_correct": is_correct,
        "generated_sql": agent_response.get("sql"),
        "agent_answer": agent_response["answer"],
        "expected_rows": expected_rows,
        "actual_rows": actual_rows,
    }


def run_evaluation():
    """Evaluating every case and printing execution accuracy."""

    with open(EVALUATION_FILE, encoding="utf-8") as file:
        cases = json.load(file)

    results = []

    for case in cases:
        print(f"\nRunning: {case['id']}")

        result = evaluate_case(case)
        results.append(result)

        status = "PASS" if result["is_correct"] else "FAIL"
        print(f"{status}: {case['question']}")
        print("Generated SQL:", result["generated_sql"])
        print("Agent Answer:", result["agent_answer"])

    passed_cases = sum(
        result["is_correct"]
        for result in results
    )

    total_cases = len(results)
    accuracy = (passed_cases / total_cases) * 100

    print("\n" + "=" * 40)
    print(f"Execution accuracy: {passed_cases}/{total_cases} ({accuracy:.1f}%)")

    # Save a report that can later be displayed in the API and frontend.
    report = {
        "evaluated_at": datetime.now().astimezone().isoformat(),
        "passed_cases": passed_cases,
        "total_cases": total_cases,
        "execution_accuracy_percent": accuracy,
        "results": results,
    }

    with open(RESULTS_FILE, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, default=str)

    print(f"Saved evaluation report: {RESULTS_FILE}")

    return report


if __name__ == "__main__":
    run_evaluation()