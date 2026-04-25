import ladybug as lb
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_graph_dbs = {}
_graph_conns = {}

def get_graph_conn(tenant_id: str):
    # Sanitize tenant_id
    tenant_id = str(tenant_id).replace("/", "").replace("\\", "")
    if tenant_id not in _graph_conns:
        db_path = os.path.join(BASE_DIR, f"{tenant_id}.lbug")
        db = lb.Database(db_path)
        conn = lb.Connection(db)
        _graph_dbs[tenant_id] = db
        _graph_conns[tenant_id] = conn
        
        # Initialize tables for this tenant
        try:
            conn.execute("CREATE NODE TABLE Entity (id STRING, label STRING, properties STRING, PRIMARY KEY (id))")
        except Exception as e:
            pass

        try:
            conn.execute("CREATE REL TABLE RelatedTo (FROM Entity TO Entity, relationship_type STRING, properties STRING)")
        except Exception as e:
            pass
            
    return _graph_conns[tenant_id]

def init_graph_db():
    # Deprecated: DBs are now initialized lazily per tenant in get_graph_conn
    pass

