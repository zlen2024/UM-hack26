from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
)

app = FastAPI(title="UM CRM API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

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


@app.get("/")
def root():
    return {"message": "UM CRM API"}


@app.get("/api/health")
def health():
    return {"status": "healthy"}
