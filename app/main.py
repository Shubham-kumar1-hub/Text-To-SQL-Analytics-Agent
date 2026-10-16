"""
FastAPI backend for the Text-to-SQL analytics agent.
"""

# python -m uvicorn app.main:app --reload

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app import agent
from app.agent import run_agent

app = FastAPI(
    title="Text-to-SQL Analytics Agent",
    description="Ask ecommerce questions in plain English and get SQL queries and answers.",
    version="0.1.0",
)

# The evaluator writes the latest benchmark report to this file.
EVALUATION_RESULTS_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "evaluation_results.json"
)

class QueryRequest(BaseModel):
    """ Expected JSOn body for an analytics question. """

    question: str = Field(
        min_length=3,
        description="A plain English ecommerce analytics question."
    )

@app.get("/health")
def health_check():
    """ Confirming that the FastAPI server is running and healthy. """

    return {"status": "Okay SON!"}


@app.get("/metrics")
def get_metrics():
    """ Returning the latest evaluation metrics for the Text-to-SQL agent. """

    if not EVALUATION_RESULTS_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="No evaluation report has been generated yet."
        )

    with open(EVALUATION_RESULTS_FILE, encoding="utf-8") as file:
        report = json.load(file)

    # Returning the headline mrtics , not all the individual test details.
    return {
        "evaluated_at": report["evaluated_at"],
        "passed_cases": report["passed_cases"],
        "total_cases": report["total_cases"],
        "execution_accuracy_percent": report["execution_accuracy_percent"],
    }

@app.post("/query")
def query_agent(request: QueryRequest):
    """ Running the complete Text-to-SQL analytics agent pipeline for a user's question. """


    try:
        agent_response = run_agent(request.question)

        # Ambiguous question have an answer but no SQL query or result.
        query_result = agent_response.get("result", {})

        return {
            "question": agent_response["question"],
            "answer": agent_response["answer"],
            "sql": agent_response.get("sql"),
            "rows": query_result.get("rows", []),
            "sql_attempts": agent_response["attempts"],
            "needs_clarification": not agent_response.get("is_clear", True),
        }


    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="The analytics request could not be completed."
        ) from error