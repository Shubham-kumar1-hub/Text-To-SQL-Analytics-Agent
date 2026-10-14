"""
Convert database schema metadata into text that an LLM can understand.
"""

from app.schema import get_schema_metadata

def format_schema_for_llm(schema):
    """Converting schema metadata into readable text for the LLM prompt."""

    lines = ["Database schema:"]

    for table_name, details in schema.items():
        # shows each column with its data types
        columns = ", ".join(
            f"{column['name']} ({column['type']})"
            for column in details["columns"]
        )

        lines.append(f"\nTable: {table_name}")
        lines.append(f"Columns: {columns}")

        # Including relationships for tables that have foreign keys
        for foreign_key in details["foreign_keys"]:
            local_column = ", ".join(foreign_key["columns"])
            referenced_column = ", ".join(foreign_key["references_columns"])

            lines.append(
                f"Relationship: {table_name}.{local_column} "
                f"-> {foreign_key['references_table']}.{referenced_column}"
            )

    return "\n".join(lines)


if __name__ == "__main__":
    database_schema = get_schema_metadata()
    schema_text = format_schema_for_llm(database_schema)

    print(schema_text)