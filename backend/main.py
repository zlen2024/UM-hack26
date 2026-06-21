from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, run_migrations
from routes import (
    chatery,
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
    chat_memory,
    business_background,
    business_rules,
    messages,
    kg,
)

app = FastAPI(title="UM CRM API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "https://um-hack26-zf1hkq.fly.dev"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create any missing tables from the ORM models, then apply additive column
# migrations for databases that predate newer columns. Both steps are
# database-agnostic and work on SQLite and PostgreSQL alike.
Base.metadata.create_all(bind=engine)
run_migrations()

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(contacts.router, prefix="/api/contacts", tags=["contacts"])
app.include_router(
    opportunities.router, prefix="/api/opportunities", tags=["opportunities"]
)
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(activities.router, prefix="/api/activities", tags=["activities"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(chatery.router, prefix="/api/chatery", tags=["chatery"])
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
app.include_router(chat_memory.router, prefix="/api/chat-memory", tags=["chat_memory"])
app.include_router(business_background.router, prefix="/api/business-background", tags=["business_background"])
app.include_router(business_rules.router, prefix="/api/business-rules", tags=["business_rules"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
app.include_router(kg.router, prefix="/api", tags=["knowledge-graph"])


@app.get("/")
def root():
    return {"message": "UM CRM API"}


@app.get("/api/health")
def health():
    return {"status": "healthy"}


@app.get("/api/test-google")
def test_google():
    return {"message": "Test route works!"}
