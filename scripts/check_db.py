import os
from dotenv import load_dotenv
load_dotenv()

# SQLAlchemy connects to the database; inspect lists its tables
from sqlalchemy import create_engine, inspect

# creating a connection engine uisng the DATABASE_URL from the .env file
engine = create_engine(os.getenv("DATABASE_URL"))

# Asking the database for it's tables name
tables = inspect(engine).get_table_names()

print(f"Found {len(tables)} tables:")
for name in sorted(tables):
    print(" -", name)