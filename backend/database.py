import kuzu
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./crm.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KUZU_DB_PATH = os.path.join(BASE_DIR, "knowledge.lbug")
kuzu_db = kuzu.Database(KUZU_DB_PATH)
kuzu_conn = kuzu.Connection(kuzu_db)

def init_graph_db():
    try:
        kuzu_conn.execute("CREATE NODE TABLE Entity (id STRING, label STRING, properties STRING, PRIMARY KEY (id))")
    except Exception as e:
        if "already exists" not in str(e):
            print(f"Error creating Entity table: {e}")

    try:
        kuzu_conn.execute("CREATE REL TABLE RelatedTo (FROM Entity TO Entity, relationship_type STRING, properties STRING)")
    except Exception as e:
        if "already exists" not in str(e):
            print(f"Error creating RelatedTo table: {e}")

def get_graph_conn():
    return kuzu_conn
