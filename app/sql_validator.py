"""
Validate generated SQL before it is allowed to run.
"""

from sqlglot import exp, parse


def validate_sql(sql_query):
    """
    Allow exactly one read-only SELECT-style query.

    Returns cleaned PostgreSQL SQL when valid.
    Raises ValueError when invalid or unsafe.
    """

    try:
        statements = parse(sql_query, read="postgres")
    except Exception as error:
        raise ValueError(f"Invalid SQL syntax: {error}") from error


    # Blocking queris such as SELECT , DELETE FROM...
    if len(statements) != 1:
        raise ValueError("Only one SQL Statement is allowed.")

    statement = statements[0]

    allowed_query_types = (exp.Select, exp.Union)

    if not isinstance(statement, allowed_query_types):
        raise ValueError("Only read-only SELECT queries are allowed.")

    return statement.sql(dialect="postgres")


if __name__ == "__main__":
    # Safe query: should pass.
    safe_sql = "SELECT name, price FROM products ORDER BY price DESC LIMIT 5"

    # Unsafe query: should be rejected.
    unsafe_sql = "DELETE FROM products"

    for sql_query in [safe_sql, unsafe_sql]:
        try:
            validated_sql = validate_sql(sql_query)
            print(f"Allowed: {validated_sql}")
        except ValueError as error:
            print(f"Blocked: {error}")