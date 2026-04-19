from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client | None = None
if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)

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


ensure_activity_columns()

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


@app.get("/", response_class=HTMLResponse)
def root():
    if not supabase:
        return "<h1>Error</h1><p>Supabase not configured</p>"
    try:
        response = supabase.table('todos').select("*").execute()
        todos = response.data
        html = '<h1>Todos</h1><ul>'
        for todo in todos:
            html += f'<li>{todo["name"]}</li>'
        html += '</ul>'
        return html
    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p>"



@app.get("/api/health")
def health():
    return {"status": "healthy"}


@app.get("/api/test-google")
def test_google():
    return {"message": "Test route works!"}
