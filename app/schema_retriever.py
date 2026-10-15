""" 
Retrieves the most relevant database tables using pgvector  similarity search.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from app.embeddings import create_embedding


load_dotenv()

def vector_to_string(vetcor):
    """ Converting a Python list into PostgreSQL vector text format"""

    return "[" + ",".join(str(value) for value in vetcor) + "]"

def retrieve_relevant_schema(question, top_k=5):
    """ 
    Finding the top 5 schema description most relevant to the user's question
    """

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set.")

    # Creating an embedding for the user's question
    question_embedding = create_embedding(question)

    engine = create_engine(database_url)

    with engine.connect() as connection:
        result = connection.execute(
            text(
                """ 
                SELECT 
                    table_name,
                    schema_text,
                    1 - (embedding <=> CAST(:question_embedding AS vector))
                        AS similarity
                    FROM schema_embeddings
                    ORDER BY embedding <=> CAST(:question_embedding AS vector)
                    LIMIT :top_k
                    """
            ),
            {
                "question_embedding": vector_to_string(question_embedding),
                "top_k": top_k,
            },
        )

        return [dict(row._mapping) for row in result]


def format_retrieved_schema(retrieved_tables):
    """ Combining the retrieved schema descriptions into a single string for the SQL-generating LLM."""

    return "\n\n".join(
        table["schema_text"]
        for table in retrieved_tables
    )


if __name__ == "__main__":
    test_question = "Which customers returned the most products?"

    matches = retrieve_relevant_schema(test_question)

    print("Question:", test_question)
    print("\nMost relevant tables:")

    for match in matches:
        print(
            f"- {match['table_name']} "
            f"(similarity: {match['similarity']:.3f})"
        )
