"""
Test SQL validation safety rules.
"""

import unittest

from app.sql_validator import validate_sql


class SQLValidatorTest(unittest.TestCase):
    """Verify allowed and blocked SQL patterns."""

    def test_allows_safe_select_query(self):
        sql_query = "SELECT name, price FROM products LIMIT 5"

        validated_sql = validate_sql(sql_query)

        self.assertIn("SELECT", validated_sql)

    def test_blocks_delete_query(self):
        sql_query = "DELETE FROM products"

        with self.assertRaises(ValueError):
            validate_sql(sql_query)

    def test_blocks_multiple_statements(self):
        sql_query = "SELECT * FROM products; DELETE FROM products"

        with self.assertRaises(ValueError):
            validate_sql(sql_query)

    def test_blocks_system_tables(self):
        with self.assertRaises(ValueError):
            validate_sql("SELECT rolname FROM pg_roles")

    def test_blocks_information_schema(self):
        with self.assertRaises(ValueError):
            validate_sql("SELECT table_name FROM information_schema.tables")

    def test_blocks_internal_embeddings_table(self):
        with self.assertRaises(ValueError):
            validate_sql("SELECT * FROM schema_embeddings")

    def test_allows_cte_with_join(self):
        sql_query = """
        WITH t AS (SELECT customer_id FROM orders)
        SELECT COUNT(*) FROM t JOIN customers c ON c.customer_id = t.customer_id
        """

        self.assertIn("SELECT", validate_sql(sql_query))

    def test_blocks_writable_cte(self):
        # This looks like a SELECT, but its CTE tries to delete data.
        sql_query = """
        WITH deleted_rows AS (
            DELETE FROM products
            RETURNING product_id
        )
        SELECT * FROM deleted_rows
        """

        with self.assertRaises(ValueError):
            validate_sql(sql_query)


if __name__ == "__main__":
    unittest.main()