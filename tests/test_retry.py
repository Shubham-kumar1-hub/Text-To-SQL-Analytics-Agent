"""
Testing that the LangGraph workflow retries SQL generation after an execution error. 
"""

import unittest
from unittest.mock import patch

from app.agent import run_agent
from app.sql_executor import execute_sql as real_execute_sql


class RetryWorkflowTest(unittest.TestCase):
    """Verifying that one execution error triggers one retry."""

    def test_agent_retries_after_execution_error(self):
        execution_attempts = 0

        def fail_once_then_execute(sql_query):
            """Fail the first execution, then use the real database executor."""

            nonlocal execution_attempts

            execution_attempts += 1

            if execution_attempts == 1:
                raise RuntimeError("Simulated temporary database error.")

            return real_execute_sql(sql_query)

        # Replace execute_sql only during this test.
        with patch(
            "app.agent.execute_sql",
            side_effect=fail_once_then_execute,
        ):
            response = run_agent(
                "Which 5 products have the highest price?"
            )

        # The first simulated failure should cause exactly one retry.
        self.assertEqual(response["attempts"], 2)

        # The second attempt should complete successfully.
        self.assertIn("result", response)
        self.assertIn("answer", response)


if __name__ == "__main__":
    unittest.main()