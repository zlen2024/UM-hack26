import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

# SQLite is the default. Set DATABASE_URL to a postgresql:// URL to use PostgreSQL.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./um_crm.db")

connect_args = {}
engine_kwargs = {}

if DATABASE_URL.startswith("sqlite"):
    # check_same_thread=False is required because FastAPI serves requests
    # (and the agent fires background threads) across multiple threads.
    connect_args = {"check_same_thread": False}
else:
    # NullPool avoids prepared-statement issues behind connection poolers
    # such as Supabase/PgBouncer.
    engine_kwargs["poolclass"] = NullPool

engine = create_engine(DATABASE_URL, connect_args=connect_args, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Additive column migrations for databases created before a column was added to
# the models. These are written with sqlalchemy.inspect so they work on both
# SQLite and PostgreSQL. On a fresh database, create_all() already builds the
# full schema, so every check below is a no-op.
_COLUMN_MIGRATIONS = {
    "users": {
        "google_email": "VARCHAR",
        "google_access_token": "VARCHAR",
        "google_refresh_token": "VARCHAR",
        "gmail_watch_expiration": "TIMESTAMP",
        "gmail_watch_history_id": "VARCHAR",
        "calendar_access_token": "VARCHAR",
        "calendar_refresh_token": "VARCHAR",
        "agent_phone_number": "VARCHAR",
    },
    "activities": {
        "source": "VARCHAR",
        "external_id": "VARCHAR",
    },
    "whatsapp_phone_numbers": {
        "app_secret": "VARCHAR",
    },
}


def run_migrations():
    """Apply additive column migrations to an existing database.

    Safe to call on every startup and on either SQLite or PostgreSQL.
    """
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table, columns in _COLUMN_MIGRATIONS.items():
            if table not in existing_tables:
                continue
            existing_columns = {c["name"] for c in inspector.get_columns(table)}
            for column, column_type in columns.items():
                if column not in existing_columns:
                    conn.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
                    )
                    print(f"[Migration] Added {table}.{column}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
