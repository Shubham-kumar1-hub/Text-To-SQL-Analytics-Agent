"""
Generates a PostgreSQL SELECT query from a user's plain English question.
"""

import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from app.schema_retriever import (
    format_retrieved_schema,
    retrieve_relevant_schema,
)
from app.sql_validator import validate_sql

load_dotenv()


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
)

def generate_sql(question, error_message=None):
    """Generates a SQL query based on the user's question and the database schema."""
    # This stays empyt during the first attempt.
    # On a retry, it tells the LLM why the previous query failed.

    error_context = ""

    if error_message:
        error_context = f"""
The previous SQL attempt failed with this error:
{error_message}

Generate a corrected SQL query that fixes this error.
"""

    # Retrieving only the tables most relevant to the user's question.
    retrieved_tables = retrieve_relevant_schema(
        question=question,
        top_k=5,
    )

    # Converting the retrieved table descriptions into LLM ready text.
    schema_text = format_retrieved_schema(retrieved_tables)

    prompt = f"""
You are a PostgreSQL analytics assistant.

Use the database schema below to answer the user's question.

{schema_text}

{error_context}

User question: {question}

Rules:
- Generate exactly one PostgreSQL SELECT query.
- Use only the tables and columns listed in the schema.
- Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, or TRUNCATE.
- Do not add filters, assumptions, or business rules that the user did not request. For example, only filter by is_active when the user explicitly asks for active products.
- For queries that return multiple rows, include LIMIT 20 unless the user asks for a different number of rows.
- Return only SQL. Do not add explanations or Markdown code fences.
"""

    response = llm.invoke(prompt)

    # Validate the LLM output before returning it to the rest of the application.
    generated_sql = response.content.strip()

    return validate_sql(generated_sql)


if __name__ == "__main__":
    question = "How many payments have been successfully paid?"

    sql_query = generate_sql(question)

    print("Question:", question)
    print("\nGenerated SQL:")
    print(sql_query)