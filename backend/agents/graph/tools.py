import json
import os
from typing import Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from sqlalchemy.orm import Session
from database import SessionLocal
from services import (
    activities as activities_service,
    contacts as contacts_service,
    opportunities as opportunities_service,
    reports as reports_service,
    tasks as tasks_service,
)


def get_db_session():
    """Get database session."""
    return SessionLocal()


def _kg_factory():
    """Lazily import the knowledge-graph factory.

    Keeping this import local means the agent graph can be built and the CRM
    tools imported without the optional Ladybug graph-database dependency.
    """
    from knowledge_db import KnowledgeDBFactory
    return KnowledgeDBFactory


# ============ Tool result helpers ============
# The CRM tools delegate all database work to the shared service layer and wrap
# the returned dicts in a small success/error envelope for the LLM.

def _ok(**payload) -> str:
    return json.dumps({"success": True, **payload})


def _err(exc: Exception) -> str:
    return json.dumps({"success": False, "error": str(exc), "error_type": "internal_error"})


def _not_found(message: str) -> str:
    return json.dumps({"success": False, "error": "not_found", "message": message})


# ============ User Context Helper ============

class UserContext:
    """Thread-local user context for tools."""
    _user_id = None

    @classmethod
    def set_user_id(cls, user_id: int):
        cls._user_id = user_id

    @classmethod
    def get_user_id(cls) -> int:
        return cls._user_id or 1


# ============ Pydantic Input Schemas ============

class CreateContactInput(BaseModel):
    user_id: int = Field(default=1, description="The user ID who owns this contact")
    name: str = Field(description="Full name of the contact, e.g. John Smith")
    email: Optional[str] = Field(default=None, description="Email address in format user@domain.com")
    phone: Optional[str] = Field(default=None, description="Phone number with country code, e.g. +1234567890")
    company: Optional[str] = Field(default=None, description="Company or organization name")
    notes: Optional[str] = Field(default=None, description="Additional notes about the contact")


class GetContactInput(BaseModel):
    user_id: int = Field(default=1, description="The user ID who owns this contact")
    contact_id: int = Field(description="The unique ID of the contact to retrieve")


class ListContactsInput(BaseModel):
    user_id: int = Field(default=1, description="The user ID who owns these contacts")
    search: Optional[str] = Field(default=None, description="Search term to filter contacts by name, email, or company")


class UpdateContactInput(BaseModel):
    user_id: int = Field(default=1, description="The user ID who owns this contact")
    contact_id: int = Field(description="The unique ID of the contact to update")
    name: Optional[str] = Field(default=None, description="Full name of the contact")
    email: Optional[str] = Field(default=None, description="Email address")
    phone: Optional[str] = Field(description="Phone number with country code")
    company: Optional[str] = Field(default=None, description="Company name")
    notes: Optional[str] = Field(default=None, description="Additional notes")


class CreateOpportunityInput(BaseModel):
    user_id: int = Field(default=1, description="The user ID who owns this opportunity")
    title: str = Field(description="Title or name of the opportunity/deal")
    value: float = Field(description="Monetary value of the opportunity in USD")
    stage: Optional[str] = Field(default="lead", description="Pipeline stage: lead, qualified, proposal, won, or lost")
    contact_id: Optional[int] = Field(default=None, description="Associated contact ID")
    expected_close_date: Optional[str] = Field(default=None, description="Expected close date in YYYY-MM-DD format")


class GetOpportunityInput(BaseModel):
    user_id: int = Field(default=1, description="The user ID who owns this opportunity")
    opportunity_id: int = Field(description="The unique ID of the opportunity to retrieve")


class ListOpportunitiesInput(BaseModel):
    user_id: int = Field(default=1, description="The user ID who owns these opportunities")
    stage: Optional[str] = Field(default=None, description="Filter by pipeline stage: lead, qualified, proposal, won, or lost")


class UpdateOpportunityStageInput(BaseModel):
    user_id: int = Field(default=1, description="The user ID who owns this opportunity")
    opportunity_id: int = Field(description="The unique ID of the opportunity")
    stage: str = Field(description="New stage: lead, qualified, proposal, won, or lost")


class CreateTaskInput(BaseModel):
    user_id: int = Field(default=1, description="The user ID who owns this task")
    title: str = Field(description="Title or name of the task")
    description: Optional[str] = Field(default=None, description="Task description")
    status: Optional[str] = Field(default="pending", description="Task status: pending, in_progress, or completed")
    priority: Optional[str] = Field(default="medium", description="Priority: low, medium, high, or urgent")
    due_date: Optional[str] = Field(default=None, description="Due date in YYYY-MM-DD format")
    contact_id: Optional[int] = Field(default=None, description="Associated contact ID")
    opportunity_id: Optional[int] = Field(default=None, description="Associated opportunity ID")


class GetTaskInput(BaseModel):
    user_id: int = Field(default=1, description="The user ID who owns this task")
    task_id: int = Field(description="The unique ID of the task to retrieve")


class ListTasksInput(BaseModel):
    user_id: int = Field(default=1, description="The user ID who owns these tasks")
    status: Optional[str] = Field(default=None, description="Filter by status: pending, in_progress, or completed")


class UpdateTaskStatusInput(BaseModel):
    user_id: int = Field(default=1, description="The user ID who owns this task")
    task_id: int = Field(description="The unique ID of the task")
    status: str = Field(description="New status: pending, in_progress, or completed")


class CreateActivityInput(BaseModel):
    user_id: int = Field(default=1, description="The user ID who owns this activity")
    activity_type: str = Field(description="Type of activity: call, email, meeting, note, task, or other")
    description: Optional[str] = Field(default=None, description="Description of the activity")
    contact_id: Optional[int] = Field(default=None, description="Associated contact ID")
    opportunity_id: Optional[int] = Field(default=None, description="Associated opportunity ID")
    scheduled_at: Optional[str] = Field(default=None, description="Scheduled time in ISO format")


class ListActivitiesInput(BaseModel):
    user_id: int = Field(default=1, description="The user ID who owns these activities")
    contact_id: Optional[int] = Field(default=None, description="Filter by contact ID")
    opportunity_id: Optional[int] = Field(default=None, description="Filter by opportunity ID")


class GetDashboardInput(BaseModel):
    user_id: int = Field(default=1, description="The user ID for the dashboard")

class SaveChatMessageInput(BaseModel):
    session_id: str = Field(description="The unique session ID for the chat")
    role: str = Field(description="Role of the message sender: 'user', 'assistant', 'system', or 'tool'")
    content: str = Field(description="Content of the message")
    contact_id: Optional[int] = Field(default=None, description="Optional contact ID associated with the message")

class GetChatHistoryInput(BaseModel):
    session_id: str = Field(description="The unique session ID for the chat")
    limit: Optional[int] = Field(default=50, description="Maximum number of messages to retrieve")

class QueryKnowledgeGraphInput(BaseModel):
    query: str = Field(description="Cypher query to execute on the knowledge graph.")

class AddKgNodeInput(BaseModel):
    node_id: str = Field(description="Unique ID for the node")
    label: str = Field(description="Label or type of the node")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Dictionary of properties")

class UpdateKgNodeInput(BaseModel):
    node_id: str = Field(description="Unique ID for the node")
    label: str = Field(description="Label or type of the node")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Dictionary of properties")

class AddKgEdgeInput(BaseModel):
    source_id: str = Field(description="Source node ID")
    target_id: str = Field(description="Target node ID")
    edge_type: str = Field(description="Type of the relationship")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Dictionary of properties")

class UpdateKgEdgeInput(BaseModel):
    source_id: str = Field(description="Source node ID")
    target_id: str = Field(description="Target node ID")
    edge_type: str = Field(description="Type of the relationship")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Dictionary of properties")

# ============ Tool Implementations ============
# Each CRM tool resolves the user, opens a session, delegates to the service
# layer, and wraps the result for the agent.

@tool("create_contact", args_schema=CreateContactInput)
def create_contact(user_id: int = 1, name: str = "", email: Optional[str] = None, phone: Optional[str] = None,
                 company: Optional[str] = None, notes: Optional[str] = None) -> str:
    """Create a new contact in the CRM system. Use when a customer provides their name or wants to register."""
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            data = contacts_service.create_contact(
                db, actual_user_id, name=name, email=email, phone=phone, company=company, notes=notes
            )
        finally:
            db.close()
        return _ok(contact_id=data["id"], message=f"Contact '{name}' created successfully", data=data)
    except Exception as e:
        return _err(e)


@tool("get_contact", args_schema=GetContactInput)
def get_contact(user_id: int = 1, contact_id: int = 0) -> str:
    """Retrieve a contact by their ID. Use to look up customer details."""
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            data = contacts_service.get_contact(db, actual_user_id, contact_id)
        finally:
            db.close()
        if not data:
            return _not_found(f"Contact with ID {contact_id} not found.")
        return _ok(data=data)
    except Exception as e:
        return _err(e)


@tool("list_contacts", args_schema=ListContactsInput)
def list_contacts(user_id: int = 1, search: Optional[str] = None) -> str:
    """List all contacts or search by name/email/company. Use to find customers."""
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            data = contacts_service.list_contacts(db, actual_user_id, search=search)
        finally:
            db.close()
        return _ok(contacts=data)
    except Exception as e:
        return _err(e)


@tool("update_contact", args_schema=UpdateContactInput)
def update_contact(user_id: int = 1, contact_id: int = 0, name: Optional[str] = None, email: Optional[str] = None,
                 phone: Optional[str] = None, company: Optional[str] = None, notes: Optional[str] = None) -> str:
    """Update an existing contact's details such as email, phone, company, or notes."""
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            data = contacts_service.update_contact(
                db, actual_user_id, contact_id,
                name=name, email=email, phone=phone, company=company, notes=notes,
            )
        finally:
            db.close()
        if not data:
            return _not_found(f"Contact with ID {contact_id} not found.")
        return _ok(message="Contact updated successfully", data=data)
    except Exception as e:
        return _err(e)


@tool("create_opportunity", args_schema=CreateOpportunityInput)
def create_opportunity(user_id: int = 1, title: str = "", value: float = 0, stage: str = "lead",
                      contact_id: Optional[int] = None,
                      expected_close_date: Optional[str] = None) -> str:
    """Create a new sales opportunity/deal. Use when a customer shows buying interest."""
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        close_date = datetime.strptime(expected_close_date, "%Y-%m-%d").date() if expected_close_date else None
        db: Session = get_db_session()
        try:
            data = opportunities_service.create_opportunity(
                db, actual_user_id, title=title, value=Decimal(str(value)), stage=stage,
                contact_id=contact_id, expected_close_date=close_date,
            )
        finally:
            db.close()
        return _ok(
            opportunity_id=data["id"],
            message=f"Opportunity '{title}' created at {data['stage']} stage",
            data=data,
        )
    except Exception as e:
        return _err(e)


@tool("get_opportunity", args_schema=GetOpportunityInput)
def get_opportunity(user_id: int = 1, opportunity_id: int = 0) -> str:
    """Retrieve an opportunity by ID."""
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            data = opportunities_service.get_opportunity(db, actual_user_id, opportunity_id)
        finally:
            db.close()
        if not data:
            return _not_found("Opportunity not found")
        return _ok(data=data)
    except Exception as e:
        return _err(e)


@tool("list_opportunities", args_schema=ListOpportunitiesInput)
def list_opportunities(user_id: int = 1, stage: Optional[str] = None) -> str:
    """List sales opportunities, optionally filtered by stage."""
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            data = opportunities_service.list_opportunities(db, actual_user_id, stage=stage)
        finally:
            db.close()
        return _ok(opportunities=data)
    except Exception as e:
        return _err(e)


@tool("update_opportunity_stage", args_schema=UpdateOpportunityStageInput)
def update_opportunity_stage(user_id: int = 1, opportunity_id: int = 0, stage: str = "") -> str:
    """Update the stage of a sales opportunity."""
    valid_stages = ["lead", "qualified", "proposal", "won", "lost"]
    if stage not in valid_stages:
        return json.dumps({
            "success": False,
            "error": "invalid_stage",
            "message": f"Invalid stage. Use: {', '.join(valid_stages)}"
        })
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            data = opportunities_service.update_opportunity_stage(db, actual_user_id, opportunity_id, stage)
        finally:
            db.close()
        if not data:
            return _not_found("Opportunity not found")
        return _ok(message=f"Opportunity moved to '{stage}'", data=data)
    except Exception as e:
        return _err(e)


@tool("create_task", args_schema=CreateTaskInput)
def create_task(user_id: int = 1, title: str = "", description: Optional[str] = None, status: str = "pending",
             priority: str = "medium", due_date: Optional[str] = None,
             contact_id: Optional[int] = None,
             opportunity_id: Optional[int] = None) -> str:
    """Create a follow-up task or to-do item."""
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        due = datetime.strptime(due_date, "%Y-%m-%d") if due_date else None
        db: Session = get_db_session()
        try:
            data = tasks_service.create_task(
                db, actual_user_id, title=title, description=description, status=status,
                priority=priority, due_date=due, contact_id=contact_id, opportunity_id=opportunity_id,
            )
        finally:
            db.close()
        return _ok(task_id=data["id"], message=f"Task '{title}' created", data=data)
    except Exception as e:
        return _err(e)


@tool("get_task", args_schema=GetTaskInput)
def get_task(user_id: int = 1, task_id: int = 0) -> str:
    """Get a task by ID."""
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            data = tasks_service.get_task(db, actual_user_id, task_id)
        finally:
            db.close()
        if not data:
            return _not_found("Task not found")
        return _ok(data=data)
    except Exception as e:
        return _err(e)


@tool("list_tasks", args_schema=ListTasksInput)
def list_tasks(user_id: int = 1, status: Optional[str] = None) -> str:
    """List tasks, optionally filtered by status."""
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            data = tasks_service.list_tasks(db, actual_user_id, status=status)
        finally:
            db.close()
        return _ok(tasks=data)
    except Exception as e:
        return _err(e)


@tool("update_task_status", args_schema=UpdateTaskStatusInput)
def update_task_status(user_id: int = 1, task_id: int = 0, status: str = "") -> str:
    """Update the status of a task."""
    valid_statuses = ["pending", "in_progress", "completed"]
    if status not in valid_statuses:
        return json.dumps({
            "success": False,
            "error": "invalid_status",
            "message": f"Invalid status. Use: {', '.join(valid_statuses)}"
        })
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            data = tasks_service.update_task_status(db, actual_user_id, task_id, status)
        finally:
            db.close()
        if not data:
            return _not_found("Task not found")
        return _ok(message=f"Task marked as '{status}'", data=data)
    except Exception as e:
        return _err(e)


@tool("create_activity", args_schema=CreateActivityInput)
def create_activity(user_id: int = 1, activity_type: str = "", description: Optional[str] = None,
                  contact_id: Optional[int] = None,
                  opportunity_id: Optional[int] = None,
                  scheduled_at: Optional[str] = None) -> str:
    """Log a customer interaction (call, email, meeting, note)."""
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        scheduled = datetime.fromisoformat(scheduled_at) if scheduled_at else None
        db: Session = get_db_session()
        try:
            data = activities_service.create_activity(
                db, actual_user_id, type=activity_type, description=description,
                contact_id=contact_id, opportunity_id=opportunity_id, scheduled_at=scheduled,
            )
        finally:
            db.close()
        return _ok(activity_id=data["id"], message=f"Activity '{data['type']}' logged", data=data)
    except Exception as e:
        return _err(e)


@tool("list_activities", args_schema=ListActivitiesInput)
def list_activities(user_id: int = 1, contact_id: Optional[int] = None,
                   opportunity_id: Optional[int] = None) -> str:
    """List activities/interactions, optionally filtered by contact or opportunity."""
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            data = activities_service.list_activities(
                db, actual_user_id, contact_id=contact_id, opportunity_id=opportunity_id
            )
        finally:
            db.close()
        return _ok(activities=data)
    except Exception as e:
        return _err(e)


@tool("get_dashboard", args_schema=GetDashboardInput)
def get_dashboard(user_id: int = 1) -> str:
    """Get dashboard with sales metrics and overview."""
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            data = reports_service.get_dashboard(db, actual_user_id)
        finally:
            db.close()
        return _ok(data=data)
    except Exception as e:
        return _err(e)


@tool("save_chat_message", args_schema=SaveChatMessageInput)
def save_chat_message(session_id: str, role: str, content: str, contact_id: Optional[int] = None) -> str:
    """Save a chat message to memory. Do NOT use this for normal replies, as normal conversation is automatically saved. Use only for explicit manual logging."""
    from agents.memory import save_message
    try:
        actual_user_id = UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            msg = save_message(
                db=db,
                session_id=session_id,
                role=role,
                content=content,
                user_id=actual_user_id,
                contact_id=contact_id
            )
            return json.dumps({
                "success": True,
                "message_id": msg.id,
                "message": "Chat message saved successfully"
            })
        finally:
            db.close()
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "error_type": "internal_error"})


@tool("get_chat_history", args_schema=GetChatHistoryInput)
def get_chat_history(session_id: str, limit: int = 50) -> str:
    """Get the recent chat history for a given session."""
    from agents.memory import get_history
    try:
        actual_user_id = UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            messages = get_history(db, session_id, limit=limit, user_id=actual_user_id)
            return json.dumps({
                "success": True,
                "messages": [{
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at.isoformat()
                } for m in messages]
            })
        finally:
            db.close()
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "error_type": "internal_error"})


@tool("query_knowledge_graph", args_schema=QueryKnowledgeGraphInput)
def query_knowledge_graph(query: str) -> str:
    """Execute a Cypher query on the user's knowledge graph to find nodes and edges."""
    try:
        user_id = str(UserContext.get_user_id() or 1)
        db = _kg_factory().get_instance(user_id)
        results = db.execute_cypher(query)
        return json.dumps({
            "success": True,
            "data": results
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "error_type": "internal_error"})


@tool("add_kg_node", args_schema=AddKgNodeInput)
def add_kg_node(node_id: str, label: str, properties: Dict[str, Any] = None) -> str:
    """Add a new node to the user's knowledge graph."""
    if properties is None: properties = {}
    try:
        user_id = str(UserContext.get_user_id() or 1)
        db = _kg_factory().get_instance(user_id)
        db.add_node(node_id, label, json.dumps(properties))
        return json.dumps({"success": True, "message": f"Node '{node_id}' added successfully"})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "error_type": "internal_error"})


@tool("update_kg_node", args_schema=UpdateKgNodeInput)
def update_kg_node(node_id: str, label: str, properties: Dict[str, Any] = None) -> str:
    """Update an existing node in the user's knowledge graph."""
    if properties is None: properties = {}
    try:
        user_id = str(UserContext.get_user_id() or 1)
        db = _kg_factory().get_instance(user_id)
        db.update_node(node_id, label, json.dumps(properties))
        return json.dumps({"success": True, "message": f"Node '{node_id}' updated successfully"})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "error_type": "internal_error"})


@tool("add_kg_edge", args_schema=AddKgEdgeInput)
def add_kg_edge(source_id: str, target_id: str, edge_type: str, properties: Dict[str, Any] = None) -> str:
    """Add a new edge/relationship between nodes in the user's knowledge graph."""
    if properties is None: properties = {}
    try:
        user_id = str(UserContext.get_user_id() or 1)
        db = _kg_factory().get_instance(user_id)
        db.add_edge(source_id, target_id, edge_type, json.dumps(properties))
        return json.dumps({"success": True, "message": f"Edge from '{source_id}' to '{target_id}' of type '{edge_type}' added successfully"})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "error_type": "internal_error"})


@tool("update_kg_edge", args_schema=UpdateKgEdgeInput)
def update_kg_edge(source_id: str, target_id: str, edge_type: str, properties: Dict[str, Any] = None) -> str:
    """Update an existing edge/relationship in the user's knowledge graph."""
    if properties is None: properties = {}
    try:
        user_id = str(UserContext.get_user_id() or 1)
        db = _kg_factory().get_instance(user_id)
        db.update_edge(source_id, target_id, edge_type, json.dumps(properties))
        return json.dumps({"success": True, "message": f"Edge from '{source_id}' to '{target_id}' of type '{edge_type}' updated successfully"})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "error_type": "internal_error"})


# ============ Export All Tools ============

CRM_TOOLS = [
    create_contact,
    get_contact,
    list_contacts,
    update_contact,
    create_opportunity,
    get_opportunity,
    list_opportunities,
    update_opportunity_stage,
    create_task,
    get_task,
    list_tasks,
    update_task_status,
    create_activity,
    list_activities,
    get_dashboard,
    save_chat_message,
    get_chat_history,
    query_knowledge_graph,
    add_kg_node,
    update_kg_node,
    add_kg_edge,
    update_kg_edge,
]
