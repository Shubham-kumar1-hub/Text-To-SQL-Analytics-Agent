"""
Creating embeddings for each ecommerce table and storing them in pgvector.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from app.embeddings import create_embedding
from app.schema import get_schema_metadata

load_dotenv()

def build_table_description(table_name, details):
    """ Creating readable text that describes one database table"""

    lines = [
        f"Table name: {table_name}",
        "columns:",
    ]

    # Adding every column name and type.
    for column in details["columns"]:
        lines.append(f"- {column['name']} ({column['type']})")

    # Primary keys help the embedding describes the table identity.
    primary_key = ", ".join(details["primary_key"])
    lines.append(f"Primary key: {primary_key}")

    # Foreign keys help describe relationships between tables.
    if details["foreign_keys"]:
        lines.append("Relationships:")

        for foreign_key in details["foreign_keys"]:
            local_column = ", ".join(foreign_key["columns"])
            referenced_column = ", ".join(foreign_key["references_column"])

            lines.append(
                f"- {local_column} references "
                f"{foreign_key['references_table']}.{referenced_column}"
            )

    return "\n".join(lines)

def vector_to_string(vector):
    """ Converting a Python list into PostgreSQL vector text format"""

    return "[" + ",".join(str(value) for value in vector) + "]"

def index_schema():
    """ Creating embeddings for each table and storing them in pgvector"""

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set.")

    engine = create_engine(database_url)
    schema = get_schema_metadata()

    with engine.begin() as connection:
        for table_name, details in schema.items():
            schema_text = build_table_description(table_name, details)

            # Converting the table description into a 384-dimensional vetcor
            embedding = create_embedding(schema_text)

            connection.execute(
                text(
                    """
                    INSERT INTO schema_embeddings(
                        table_name,
                        schema_text,
                        embedding,
                        updated_at,
                    )
                    VALUES (
                        :table_name,
                        :schema_text,
                        CAST(:embedding AS vector),
                        CURRENT_TIMESTAMP
                    )
                    ON CONFLICT (table_name)
                    DO UPDATE SET
                        schema_text = EXCLUDED.schema_text,
                        embedding = EXCLUDED.embedding,
                        updated_at = CURRENT_TIMESTAMP
                    """
                ),
                {
                    "table_name": table_name,
                    "schema_text": schema_text,
                    "embedding": vector_to_string(embedding),
                },
            )

            print(f"Indexed: {table_name}")

    print(f"\nIndexed {len(schema)} ecommerce tables.")


if __name__ == "__main__":
    index_schema()
