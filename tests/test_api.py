"""
Testing FastAPI endpoints without calling the real LLM or Databas.
"""

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

class APITEST(unittest.TestCase):
    """ Verifying API request validation and response structure. """

    def setUp(self):
        self.client = TestClient(app)

    @patch("app.main.run_agent")
    def test_query_returns_agent_response(self, mock_run_agent):
        """ A clear question should rturn SQL, rows, and an answer."""

        mock_run_agent.return_value = {
            "question": "Which 5 products have the highest price?",
            "answer": "Bolt Gaming Laptop is the most expensive product.",
            "sql": "SELECT name, price FROM products ORDER BY price DESC LIMIT 5",
            "result": {
                "rows": [
                    {
                        "name": "Bolt Gaming Laptop",
                        "price": 99990.74,
                    }
                ]
            },
            "attempts": 1,
            "is_clear": True,
        }

        response = self.client.post(
            "/query",
            json={
                "question": "Which 5 products have the highest price?"
            },
        )

        self.assertEqual(response.status_code, 200)

        body = response.json()

        self.assertEqual(body["sql_attempts"], 1)
        self.assertFalse(body["needs_clarification"])
        self.assertEqual(len(body["rows"]), 1)

    @patch("app.main.run_agent")
    def test_query_returns_clarification(self, mock_run_agent):
        """An ambiguous question should return no SQL or rows."""

        mock_run_agent.return_value = {
            "question": "What are the best products?",
            "answer": "Which metric defines best: sales, profit, or rating?",
            "attempts": 0,
            "is_clear": False,
        }

        response = self.client.post(
            "/query",
            json={"question": "What are the best products?"},
        )

        self.assertEqual(response.status_code, 200)

        body = response.json()

        self.assertTrue(body["needs_clarification"])
        self.assertIsNone(body["sql"])
        self.assertEqual(body["rows"], [])
        self.assertEqual(body["sql_attempts"], 0)

    def test_query_rejects_short_question(self):
        """A question shorter than three characters should be rejected."""

        response = self.client.post(
            "/query",
            json={"question": "hi"},
        )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()