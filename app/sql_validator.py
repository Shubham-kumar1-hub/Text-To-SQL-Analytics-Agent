"""
Validate generated SQL before it is allowed to run.
"""

from sqlglot import exp, parse

# The only tables the agent is allowed to read
ALLOWED_TABLES = {
    "customers", "addresses", "categories", "brands", "suppliers",
    "products", "inventory", "coupons", "orders", "order_items",
    "order_coupons", "payments", "shipments", "reviews", "returns",
}


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
        raise ValueError("Only read only SELECT queries are allowed.")

    unsafe_expressions_types = (
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Into,
    )

    if any(
        statement.find(expression_type) is not None
        for expression_type in unsafe_expressions_types
    ):
        raise ValueError("Data changing SQL is not allowed.")

        # Names created by WITH clauses are temporary, so they are allowed
    cte_names = {cte.alias_or_name.lower() for cte in statement.find_all(exp.CTE)}

    for table in statement.find_all(exp.Table):
        table_name = table.name.lower()

        # Table functions such as generate_series have no name, so skip them
        if not table_name:
            continue

        # Block other schemas such as information_schema or pg_catalog
        if table.db and table.db.lower() != "public":
            raise ValueError("Only the ecommerce tables are allowed.")

        # Block any table that is not an ecommerce table or a WITH name
        if table_name not in ALLOWED_TABLES and table_name not in cte_names:
            raise ValueError("Only the ecommerce tables are allowed.")

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