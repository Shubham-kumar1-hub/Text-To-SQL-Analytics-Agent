""" 
Retrieves the most relevant database tables using pgvector  similarity search.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from app.embeddings import create_embedding
from app.schema import get_schema_metadata


load_dotenv()

def vector_to_string(vetcor):
    """ Converting a Python list into PostgreSQL vector text format"""

    return "[" + ",".join(str(value) for value in vetcor) + "]"


def get_related_tables():
    """ Returns direct tables relationship in both directions."""

    schema = get_schema_metadata()

    related_tables = {
        table_name: set()
        for table_name in schema
    }

    for table_name, details in schema.items():
        for foreign_key in details["foreign_keys"]:
            referenced_table = foreign_key["references_table"]

            # Add both directions:
            # order_items -> orders, and orders -> order_items.
            related_tables[table_name].add(referenced_table)
            related_tables[referenced_table].add(table_name)

    return related_tables


def retrieve_relevant_schema(question, top_k=5):
    """ 
    Finding the top 5 schema description most relevant to the user's question
    """

    database_url = os.getenv("READONLY_DATABASE_URL")

    if not database_url:
        raise ValueError("READONLY_DATABASE_URL environment variable is not set.")

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
                    """
            ),
            {
                "question_embedding": vector_to_string(question_embedding),
            },
        )

        # Fetching all matches first, then select the strongest semantic matches.
        all_matches = [dict(row._mapping) for row in result]
        semantic_matches = all_matches[:top_k]

        # Adding directly related tables so the LLM can form SQL joins.
        related_tables = get_related_tables()
        selected_table_names = {
            match["table_name"]
            for match in semantic_matches
        }

        for table_name in list(selected_table_names):
            selected_table_names.update(related_tables[table_name])

        # Keeping semantic matches first, then add relationship tables.
        matches_by_name = {
            match["table_name"]: match
            for match in all_matches
        }

        ordered_table_names = [
            match["table_name"]
            for match in semantic_matches
        ]

        relationship_table_names = sorted(
            selected_table_names - set(ordered_table_names)
        )

        ordered_table_names.extend(relationship_table_names)

        return [
            matches_by_name[table_name]
            for table_name in ordered_table_names
        ]


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
