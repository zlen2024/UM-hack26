import contextlib
from fastapi import FastAPI

from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from database import engine, Base
from neonize_client import manager
from routes import (
    auth,
    contacts,
    opportunities,
    tasks,
    activities,
    reports,
    users,
    agent,
    google_calendar,
    gmail,
    emails,
    whatsapp,
    privacy,
)

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("[Lifespan] Starting Neonize auto-reconnect...")
    await manager.start_all_clients()
    yield
    # Shutdown (if needed)
    print("[Lifespan] Shutting down...")

app = FastAPI(title="UM CRM API", version="1.0.0", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "https://um-hack26-zf1hkq.fly.dev"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


def ensure_activity_columns() -> None:
    from database import DATABASE_URL
    with engine.begin() as conn:
        if "sqlite" in DATABASE_URL:
            result = conn.execute(text("PRAGMA table_info(activities)")).fetchall()
            columns = {row[1] for row in result}
        else:
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'activities'"
            )).fetchall()
            columns = {row[0] for row in result}

        if "source" not in columns:
            conn.execute(text("ALTER TABLE activities ADD COLUMN source TEXT"))
        if "external_id" not in columns:
            conn.execute(text("ALTER TABLE activities ADD COLUMN external_id TEXT"))

def ensure_user_columns() -> None:
    from database import DATABASE_URL
    with engine.begin() as conn:
        if "sqlite" in DATABASE_URL:
            result = conn.execute(text("PRAGMA table_info(users)")).fetchall()
            columns = {row[1] for row in result}
        else:
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"
            )).fetchall()
            columns = {row[0] for row in result}

        if "google_email" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN google_email TEXT"))
        if "google_access_token" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN google_access_token TEXT"))
        if "google_refresh_token" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN google_refresh_token TEXT"))
        if "calendar_access_token" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN calendar_access_token TEXT"))
        if "calendar_refresh_token" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN calendar_refresh_token TEXT"))
        if "gmail_watch_expiration" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN gmail_watch_expiration TIMESTAMP"))
        if "gmail_watch_history_id" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN gmail_watch_history_id TEXT"))
        if "agent_phone_number" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN agent_phone_number TEXT"))

def ensure_whatsapp_table() -> None:
    from database import DATABASE_URL
    with engine.begin() as conn:
        if "sqlite" in DATABASE_URL:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='whatsapp_phone_numbers'")).fetchone()
        else:
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_name = 'whatsapp_phone_numbers'"
            )).fetchone()

        if not result:
            conn.execute(text("""
                CREATE TABLE whatsapp_phone_numbers (
                    phone_number_id VARCHAR PRIMARY KEY,
                    display_phone_number VARCHAR UNIQUE,
                    access_token VARCHAR NOT NULL,
                    app_secret VARCHAR,
                    verify_token VARCHAR NOT NULL,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX idx_whatsapp_user_id ON whatsapp_phone_numbers(user_id)"))
            conn.execute(text("CREATE INDEX idx_whatsapp_display_phone ON whatsapp_phone_numbers(display_phone_number)"))
        else:
            # Ensure app_secret column exists on existing tables
            if "sqlite" in DATABASE_URL:
                cols = conn.execute(text("PRAGMA table_info(whatsapp_phone_numbers)")).fetchall()
                col_names = {row[1] for row in cols}
            else:
                cols = conn.execute(text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'whatsapp_phone_numbers'"
                )).fetchall()
                col_names = {row[0] for row in cols}
            if "app_secret" not in col_names:
                conn.execute(text("ALTER TABLE whatsapp_phone_numbers ADD COLUMN app_secret VARCHAR"))

def ensure_neonize_table() -> None:
    from database import DATABASE_URL
    with engine.begin() as conn:
        if "sqlite" in DATABASE_URL:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='neonize_config'")).fetchone()
        else:
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_name = 'neonize_config'"
            )).fetchone()

        if not result:
            id_col = "id INTEGER PRIMARY KEY AUTOINCREMENT" if "sqlite" in DATABASE_URL else "id SERIAL PRIMARY KEY"
            conn.execute(text(f"""
                CREATE TABLE neonize_config (
                    {id_col},
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    session_name VARCHAR DEFAULT 'default',
                    phone_number VARCHAR,
                    is_connected BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX idx_neonize_user_id ON neonize_config(user_id)"))

ensure_activity_columns()
ensure_user_columns()
ensure_whatsapp_table()
ensure_neonize_table()


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(contacts.router, prefix="/api/contacts", tags=["contacts"])
app.include_router(
    opportunities.router, prefix="/api/opportunities", tags=["opportunities"]
)
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(activities.router, prefix="/api/activities", tags=["activities"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(agent.router, prefix="/api/agent", tags=["agent"])
app.include_router(
    google_calendar.router, prefix="/api/google-calendar", tags=["google-calendar"]
)
app.include_router(
    gmail.router, prefix="/api/gmail", tags=["gmail"]
)
app.include_router(
    emails.router, prefix="/api/emails", tags=["emails"]
)
app.include_router(whatsapp.router, prefix="/api/whatsapp", tags=["whatsapp"])
app.include_router(privacy.router, prefix="/api/privacy", tags=["privacy"])


@app.get("/")
def root():
    return {"message": "UM CRM API"}


@app.get("/api/health")
def health():
    return {"status": "healthy"}


@app.get("/api/test-google")
def test_google():
    return {"message": "Test route works!"}


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
