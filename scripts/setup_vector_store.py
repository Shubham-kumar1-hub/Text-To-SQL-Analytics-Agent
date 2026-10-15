"""
Creating the PostgreSQL pgvector extension and schema embedding table.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

EMBEDDING_DIMENSION = 384


def setup_vector_store():
    """ Creating the pgvector extension and schema_embedding table"""

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set.")

    engine = create_engine(database_url)

    with engine.begin() as connection:
        # Enabling pgvector in the ecommerce datbase
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # Storing one schema description and vector for each database table.
        connection.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS schema_embeddings (
                    table_name TEXT PRIMARY KEY,
                    schema_text TEXT NOT NULL,
                    embedding VECTOR({EMBEDDING_DIMENSION}) NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
            )
        )

    print("pgvector is enabled.")
    print("schema_embeddings table is ready.")


if __name__ == "__main__":
    setup_vector_store()
