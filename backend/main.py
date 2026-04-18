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
)

app = FastAPI(title="UM CRM API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


def ensure_activity_columns() -> None:
    with engine.begin() as conn:
        result = conn.execute(text("PRAGMA table_info(activities)")).fetchall()
        columns = {row[1] for row in result}
        if "source" not in columns:
            conn.execute(text("ALTER TABLE activities ADD COLUMN source TEXT"))
        if "external_id" not in columns:
            conn.execute(text("ALTER TABLE activities ADD COLUMN external_id TEXT"))

def ensure_user_columns() -> None:
    with engine.begin() as conn:
        result = conn.execute(text("PRAGMA table_info(users)")).fetchall()
        columns = {row[1] for row in result}
        if "google_email" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN google_email TEXT"))
        if "google_access_token" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN google_access_token TEXT"))
        if "google_refresh_token" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN google_refresh_token TEXT"))

ensure_activity_columns()
ensure_user_columns()

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


@app.get("/")
def root():
    return {"message": "UM CRM API"}


@app.get("/api/health")
def health():
    return {"status": "healthy"}


@app.get("/api/test-google")
def test_google():
    return {"message": "Test route works!"}
