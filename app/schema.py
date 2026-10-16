""" 
Read database schema metadata.

Later, the SQL generation agent will use this information to understand
which tables and columns are relevant to a user's question.
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect

# Internal application tables should never be shown to the SQL-generating LLM.
INTERNAL_TABLES = {"schema_embeddings"}

load_dotenv()

def get_schema_metadata():
    """ Returns tables, columns, primary keys, and foreign-key relationships for the database. """

    database_url = os.getenv("READONLY_DATABASE_URL")

    if not database_url:
        raise ValueError("READONLY_DATABASE_URL environment variable is not set.")

    engine = create_engine(database_url)
    inspector = inspect(engine)

    schema = {}

    # Traversing through all tables in the database in alphabetical order
    for table_name in sorted(inspector.get_table_names()):
        # Skip application tables that are not part of the ecommerce schema.
        if table_name in INTERNAL_TABLES:
            continue
        columns = []

        for column in inspector.get_columns(table_name):
            columns.append(
                {
                    "name": column["name"],
                    "type": str(column["type"]),
                    "nullable": column["nullable"],
                }
            )

        # Foreign keys, we will get the relationships for each table
        foreign_keys = []

        for foreign_key in inspector.get_foreign_keys(table_name):
            foreign_keys.append(
                {
                    "columns": foreign_key["constrained_columns"],
                    "references_table": foreign_key["referred_table"],
                    "references_columns": foreign_key["referred_columns"],
                }
            )

        schema[table_name] = {
            "columns": columns,
            "primary_key": inspector.get_pk_constraint(table_name)["constrained_columns"],
            "foreign_keys": foreign_keys,
        }

    return schema


if __name__ == "__main__":
    database_schema = get_schema_metadata()

    for table_name, details in database_schema.items():
        column_names = [column["name"] for column in details["columns"]]

        print(f"\nTable: {table_name}")
        print("Columns:", ", ".join(column_names))
        print("Primary key:", details["primary_key"])
        print("Foreign keys:", details["foreign_keys"])