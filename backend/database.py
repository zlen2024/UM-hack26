import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Use NullPool for Supabase connection pooling (prevents prepared statement issues)
engine = create_engine(DATABASE_URL, poolclass=NullPool)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def run_migrations():
    """Run database migrations for new columns"""
    db = SessionLocal()
    try:
        # Check if calendar_access_token column exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'calendar_access_token'
        """))
        if not result.fetchone():
            db.execute(text("ALTER TABLE users ADD COLUMN calendar_access_token VARCHAR"))
            print("[Migration] Added calendar_access_token column")
        
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'calendar_refresh_token'
        """))
        if not result.fetchone():
            db.execute(text("ALTER TABLE users ADD COLUMN calendar_refresh_token VARCHAR"))
            print("[Migration] Added calendar_refresh_token column")
        
        db.commit()
        print("[Migration] Database migrations complete")
    except Exception as e:
        print(f"[Migration] Error: {e}")
        db.rollback()
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Run migrations on import
run_migrations()
