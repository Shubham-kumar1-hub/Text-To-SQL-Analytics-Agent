"""
Generates a PostgreSQL SELECT query from a user's plain English question.
"""

import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from app.schema import get_schema_metadata
from app.schema_context import format_schema_for_llm
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

    # Reading the current database structure and formatting it for the LLM
    database_Schema = get_schema_metadata()
    schema_text = format_schema_for_llm(database_Schema)

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
- Return only SQL. Do not add explanations or Markdown code fences.
"""

    response = llm.invoke(prompt)

    # Validate the LLM output before returning it to the rest of the application.
    generated_sql = response.content.strip()

    return validate_sql(generated_sql)


if __name__ == "__main__":
    question = "Which 5 products have the highest price?"

    sql_query = generate_sql(question)

    print("Question:", question)
    print("\nGenerated SQL:")
    print(sql_query)