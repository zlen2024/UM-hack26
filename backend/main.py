from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from database import engine, Base
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
    telegram,
)

app = FastAPI(title="UM CRM API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "https://um-hack26-zf1hkq.fly.dev"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


def ensure_activity_columns() -> None:
    with engine.begin() as conn:
        result = conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'activities'"
        )).fetchall()
        columns = {row[0] for row in result}
        if "source" not in columns:
            conn.execute(text("ALTER TABLE activities ADD COLUMN source TEXT"))
        if "external_id" not in columns:
            conn.execute(text("ALTER TABLE activities ADD COLUMN external_id TEXT"))

def ensure_user_columns() -> None:
    with engine.begin() as conn:
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
    with engine.begin() as conn:
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
            cols = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'whatsapp_phone_numbers'"
            )).fetchall()
            col_names = {row[0] for row in cols}
            if "app_secret" not in col_names:
                conn.execute(text("ALTER TABLE whatsapp_phone_numbers ADD COLUMN app_secret VARCHAR"))


def ensure_telegram_table() -> None:
    with engine.begin() as conn:
        result = conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'telegram_bots'"
        )).fetchone()
        if not result:
            conn.execute(text("""
                CREATE TABLE telegram_bots (
                    bot_token VARCHAR PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    username VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX idx_telegram_user_id ON telegram_bots(user_id)"))

ensure_activity_columns()
ensure_user_columns()
ensure_whatsapp_table()
ensure_telegram_table()

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
app.include_router(telegram.router, prefix="/api/telegram", tags=["telegram"])
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
