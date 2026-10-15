"""
FastAPI backend for the Text-to-SQL analytics agent.
"""

# python -m uvicorn app.main:app --reload

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app import agent
from app.agent import run_agent

app = FastAPI(
    title="Text-to-SQL Analytics Agent",
    description="Ask ecommerce questions in plain English and get SQL queries and answers.",
    version="0.1.0",
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