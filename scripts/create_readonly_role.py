""" 
Creating a PostgreSQL role that can read tables but cannot modify the data.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

READONLY_ROLE_NAME = "analytics_reader"

def create_readonly_role():
    """ Create or update a PostgreSQL role with read-only access to all tables in the database. """

    datbase_url = os.getenv("DATABASE_URL")
    readonly_password = os.getenv("READONLY_DB_PASSWORD")

    if not datbase_url:
        raise ValueError("DATABASE_URL is not set in the environment variables.")

    if not readonly_password:
        raise ValueError("READONLY_DB_PASSWORD is not set in the environment variables.")

    safe_password = readonly_password.replace("'", "''")  # Escaping single quotes in the password

    engine = create_engine(datbase_url)

    with engine.begin() as connection:
        role_exists = connection.execute(
            text(
                """
                SELECT 1
                FROM pg_roles
                WHERE rolname = :role_name
                """
            ),
            {"role_name": READONLY_ROLE_NAME},
        ).scalar()

        if role_exists:
            # Updating the password if the role already exists
            connection.execute(
                text(
                    f"ALTER ROLE {READONLY_ROLE_NAME} "
                    f"LOGIN PASSWORD '{safe_password}'"
                )
            )
        else:
            # Creating the role for the first time.
            connection.execute(
                text(
                    f"CREATE ROLE {READONLY_ROLE_NAME}"
                    f" LOGIN PASSWORD '{safe_password}'"
                )
            )

        # Allowing connection and reading , but granting no write permissions.
        connection.execute(
            text(
                f"GRANT CONNECT ON DATABASE ecommerce "
                f"TO {READONLY_ROLE_NAME}"
            )
        )

        connection.execute(
            text(
                f"GRANT USAGE ON SCHEMA public "
                f"TO {READONLY_ROLE_NAME}"
            )
        )


        connection.execute(
            text(
                f"GRANT SELECT ON ALL TABLES IN SCHEMA public "
                f"TO {READONLY_ROLE_NAME}"
            )
        )

        # New tables created later will also be readable by this role
        connection.execute(
            text(
                f"ALTER DEFAULT PRIVILEGES IN SCHEMA public "
                f"GRANT SELECT ON TABLES TO {READONLY_ROLE_NAME}"
            )
        )

    print(f"Read-only-role '{READONLY_ROLE_NAME}' is ready.")


if __name__ == "__main__":
    create_readonly_role()