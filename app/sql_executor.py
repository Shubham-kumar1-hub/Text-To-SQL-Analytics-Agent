"""
Run validated read only SQL queries against PostgreSQL.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


from app.sql_validator import validate_sql

load_dotenv()

# Safety limits for every analytics query.
MAX_ROWS = 100
STATEMENT_TIMEOUT_MS = 5000


def execute_sql(sql_query):
    """
    Validate, explain, and execute a read only SQL query.

    Returns column names, result rows, and whether the row limit was reached.
    """

    database_url = os.getenv("READONLY_DATABASE_URL")

    if not database_url:
        raise ValueError("READONLY_DATABASE_URL environment variable is not set.")


    validated_sql = validate_sql(sql_query)

    # The outer LIMIT prevents the application from returning too many rows.
    limited_sql = (
        f"SELECT * FROM ({validated_sql}) AS analytics_result "
        f"LIMIT {MAX_ROWS}"
    )

    engine = create_engine(database_url)

    with engine.connect() as connection:
        with connection.begin():
            # PostgreSQL blocks writes for this transaction.
            connection.execute(text("SET TRANSACTION READ ONLY"))

            # PostgreSQL cancels a query that takes too long.
            connection.execute(
                text(f"SET LOCAL statement_timeout = '{STATEMENT_TIMEOUT_MS}ms'")
            )

            # Check that PostgresSQL can build a query plan before executing the query.
            connection.execute(text(f"EXPLAIN {limited_sql}"))


            # RUN the validayed limited query
            result = connection.execute(text(limited_sql))

            columns = list(result.keys())
            rows = [dict(row._mapping) for row in result.fetchall()]

    return {
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "truncated": len(rows) == MAX_ROWS,
    }

if __name__ == "__main__":
    # A simple execution test.
    test_sql = """
    SELECT product_id, name, price
    FROM products
    ORDER BY price DESC
    LIMIT 5
    """

    query_result = execute_sql(test_sql)

    print("Columns:", query_result["columns"])
    print("Rows:")

    for row in query_result["rows"]:
        print(row)

    