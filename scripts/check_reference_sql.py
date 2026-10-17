import json
import sys
from pathlib import Path

from app.sql_executor import execute_sql

# Path to the new eval file
EVAL_FILE = Path(__file__).resolve().parent.parent / "data" / "eval_cases.json"

# filter: "python -m scripts.check_reference_sql t3" checks only t3_* cases

prefix = sys.argv[1] if len(sys.argv) > 1 else ""

with open(EVAL_FILE, encoding="utf-8") as file:
    cases = json.load(file)

for case in cases:
    # Skipping cases that don't match the prefix filter
    if not case["id"].startswith(prefix):
        continue

    print(f"\n{case['id']} [{case['split']}] {case['question']}")

    # Ambiguous cases have no reference SQL, so we skip them
    if not case["reference_sql"]:
        print(" (no reference SQL, expects clarification)")
        continue

    # Running the reference SQL and show up to 5 rows of the result
    result = execute_sql(case["reference_sql"])
    print(f" rows returned: {result['row_count']}")
    for row in result["rows"][:12]:
        print(" ", row)