import json
import os
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Contact, Opportunity, Task, Activity, User


def get_db_session():
    """Get database session."""
    return SessionLocal()


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

# ============ Tool Implementations ============

@tool("create_contact", args_schema=CreateContactInput)
def create_contact(user_id: int = 1, name: str = "", email: Optional[str] = None, phone: Optional[str] = None,
                 company: Optional[str] = None, notes: Optional[str] = None) -> str:
    """Create a new contact in the CRM system. Use when a customer provides their name or wants to register."""
    try:
        # Get actual user_id from context if not provided
        actual_user_id = user_id or UserContext.get_user_id() or 1
        
        db: Session = get_db_session()
        try:
            db_contact = Contact(
                user_id=actual_user_id,
                name=name,
                email=email,
                phone=phone,
                company=company,
                notes=notes,
            )
            db.add(db_contact)
            db.commit()
            db.refresh(db_contact)
            return json.dumps({
                "success": True,
                "contact_id": db_contact.id,
                "message": f"Contact '{name}' created successfully",
                "data": {
                    "id": db_contact.id,
                    "name": db_contact.name,
                    "email": db_contact.email,
                    "phone": db_contact.phone,
                    "company": db_contact.company,
                }
            })
        finally:
            db.close()
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": "internal_error",
            "message": "Failed to create contact. Please try again."
        })


@tool("get_contact", args_schema=GetContactInput)
def get_contact(user_id: int = 1, contact_id: int = 0) -> str:
    """Retrieve a contact by their ID. Use to look up customer details."""
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            contact = db.query(Contact).filter(
                Contact.id == contact_id, 
                Contact.user_id == actual_user_id
            ).first()
            if not contact:
                return json.dumps({
                    "success": False,
                    "error": "not_found",
                    "message": f"Contact with ID {contact_id} not found."
                })
            return json.dumps({
                "success": True,
                "data": {
                    "id": contact.id,
                    "name": contact.name,
                    "email": contact.email,
                    "phone": contact.phone,
                    "company": contact.company,
                    "notes": contact.notes,
                }
            })
        finally:
            db.close()
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "error_type": "internal_error"})


@tool("list_contacts", args_schema=ListContactsInput)
def list_contacts(user_id: int = 1, search: Optional[str] = None) -> str:
    """List all contacts or search by name/email/company. Use to find customers."""
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            query = db.query(Contact).filter(Contact.user_id == actual_user_id)
            if search:
                query = query.filter(
                    (Contact.name.contains(search)) |
                    (Contact.email.contains(search)) |
                    (Contact.company.contains(search))
                )
            contacts = query.order_by(Contact.created_at.desc()).limit(50).all()
            return json.dumps({
                "success": True,
                "contacts": [{
                    "id": c.id,
                    "name": c.name,
                    "email": c.email,
                    "phone": c.phone,
                    "company": c.company,
                } for c in contacts]
            })
        finally:
            db.close()
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "error_type": "internal_error"})


@tool("update_contact", args_schema=UpdateContactInput)
def update_contact(user_id: int = 1, contact_id: int = 0, name: Optional[str] = None, email: Optional[str] = None,
                 phone: Optional[str] = None, company: Optional[str] = None,
                 notes: Optional[str] = None) -> str:
    """Update an existing contact's information."""
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            contact = db.query(Contact).filter(
                Contact.id == contact_id,
                Contact.user_id == actual_user_id
            ).first()
            if not contact:
                return json.dumps({
                    "success": False,
                    "error": "not_found",
                    "message": f"Contact with ID {contact_id} not found."
                })
            if name:
                contact.name = name
            if email:
                contact.email = email
            if phone:
                contact.phone = phone
            if company:
                contact.company = company
            if notes:
                contact.notes = notes
            db.commit()
            return json.dumps({
                "success": True,
                "message": "Contact updated successfully",
                "data": {"id": contact.id, "name": contact.name}
            })
        finally:
            db.close()
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "error_type": "internal_error"})


@tool("create_opportunity", args_schema=CreateOpportunityInput)
def create_opportunity(user_id: int = 1, title: str = "", value: float = 0, stage: str = "lead",
                      contact_id: Optional[int] = None,
                      expected_close_date: Optional[str] = None) -> str:
    """Create a new sales opportunity/deal. Use when a customer shows buying interest."""
    valid_stages = ["lead", "qualified", "proposal", "won", "lost"]
    if stage not in valid_stages:
        stage = "lead"
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            close_date = None
            if expected_close_date:
                close_date = datetime.strptime(expected_close_date, "%Y-%m-%d").date()
            db_opportunity = Opportunity(
                user_id=actual_user_id,
                title=title,
                value=Decimal(str(value)),
                stage=stage,
                contact_id=contact_id,
                expected_close_date=close_date,
            )
            db.add(db_opportunity)
            db.commit()
            db.refresh(db_opportunity)
            return json.dumps({
                "success": True,
                "opportunity_id": db_opportunity.id,
                "message": f"Opportunity '{title}' created at {stage} stage",
                "data": {
                    "id": db_opportunity.id,
                    "title": db_opportunity.title,
                    "value": str(db_opportunity.value),
                    "stage": db_opportunity.stage,
                }
            })
        finally:
            db.close()
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "error_type": "internal_error"})


@tool("get_opportunity", args_schema=GetOpportunityInput)
def get_opportunity(user_id: int = 1, opportunity_id: int = 0) -> str:
    """Retrieve an opportunity by ID."""
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            opp = db.query(Opportunity).filter(
                Opportunity.id == opportunity_id,
                Opportunity.user_id == actual_user_id
            ).first()
            if not opp:
                return json.dumps({"success": False, "error": "not_found", "message": "Opportunity not found"})
            return json.dumps({
                "success": True,
                "data": {
                    "id": opp.id,
                    "title": opp.title,
                    "value": str(opp.value),
                    "stage": opp.stage,
                    "contact_id": opp.contact_id,
                }
            })
        finally:
            db.close()
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "error_type": "internal_error"})


@tool("list_opportunities", args_schema=ListOpportunitiesInput)
def list_opportunities(user_id: int = 1, stage: Optional[str] = None) -> str:
    """List sales opportunities, optionally filtered by stage."""
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            query = db.query(Opportunity).filter(Opportunity.user_id == actual_user_id)
            if stage:
                query = query.filter(Opportunity.stage == stage)
            opps = query.order_by(Opportunity.created_at.desc()).limit(50).all()
            return json.dumps({
                "success": True,
                "opportunities": [{
                    "id": o.id,
                    "title": o.title,
                    "value": str(o.value),
                    "stage": o.stage,
                } for o in opps]
            })
        finally:
            db.close()
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "error_type": "internal_error"})


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
            opp = db.query(Opportunity).filter(
                Opportunity.id == opportunity_id,
                Opportunity.user_id == actual_user_id
            ).first()
            if not opp:
                return json.dumps({"success": False, "error": "not_found", "message": "Opportunity not found"})
            opp.stage = stage
            db.commit()
            return json.dumps({
                "success": True,
                "message": f"Opportunity moved to '{stage}'",
                "data": {"id": opp.id, "stage": opp.stage}
            })
        finally:
            db.close()
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "error_type": "internal_error"})


@tool("create_task", args_schema=CreateTaskInput)
def create_task(user_id: int = 1, title: str = "", description: Optional[str] = None, status: str = "pending",
             priority: str = "medium", due_date: Optional[str] = None,
             contact_id: Optional[int] = None,
             opportunity_id: Optional[int] = None) -> str:
    """Create a follow-up task or to-do item."""
    valid_statuses = ["pending", "in_progress", "completed"]
    valid_priorities = ["low", "medium", "high", "urgent"]
    if status not in valid_statuses:
        status = "pending"
    if priority not in valid_priorities:
        priority = "medium"
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            due = None
            if due_date:
                due = datetime.strptime(due_date, "%Y-%m-%d")
            db_task = Task(
                user_id=actual_user_id,
                title=title,
                description=description,
                status=status,
                priority=priority,
                due_date=due,
                contact_id=contact_id,
                opportunity_id=opportunity_id,
            )
            db.add(db_task)
            db.commit()
            db.refresh(db_task)
            return json.dumps({
                "success": True,
                "task_id": db_task.id,
                "message": f"Task '{title}' created",
                "data": {"id": db_task.id, "title": db_task.title, "status": db_task.status}
            })
        finally:
            db.close()
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "error_type": "internal_error"})


@tool("get_task", args_schema=GetTaskInput)
def get_task(user_id: int = 1, task_id: int = 0) -> str:
    """Get a task by ID."""
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            task = db.query(Task).filter(
                Task.id == task_id,
                Task.user_id == actual_user_id
            ).first()
            if not task:
                return json.dumps({"success": False, "error": "not_found", "message": "Task not found"})
            return json.dumps({
                "success": True,
                "data": {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "priority": task.priority,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                }
            })
        finally:
            db.close()
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "error_type": "internal_error"})


@tool("list_tasks", args_schema=ListTasksInput)
def list_tasks(user_id: int = 1, status: Optional[str] = None) -> str:
    """List tasks, optionally filtered by status."""
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            query = db.query(Task).filter(Task.user_id == actual_user_id)
            if status:
                query = query.filter(Task.status == status)
            tasks = query.order_by(Task.due_date.asc().nullslast()).limit(50).all()
            return json.dumps({
                "success": True,
                "tasks": [{
                    "id": t.id,
                    "title": t.title,
                    "status": t.status,
                    "priority": t.priority,
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                } for t in tasks]
            })
        finally:
            db.close()
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "error_type": "internal_error"})


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
            task = db.query(Task).filter(
                Task.id == task_id,
                Task.user_id == actual_user_id
            ).first()
            if not task:
                return json.dumps({"success": False, "error": "not_found", "message": "Task not found"})
            task.status = status
            db.commit()
            return json.dumps({
                "success": True,
                "message": f"Task marked as '{status}'",
                "data": {"id": task.id, "status": task.status}
            })
        finally:
            db.close()
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "error_type": "internal_error"})


@tool("create_activity", args_schema=CreateActivityInput)
def create_activity(user_id: int = 1, activity_type: str = "", description: Optional[str] = None,
                  contact_id: Optional[int] = None,
                  opportunity_id: Optional[int] = None,
                  scheduled_at: Optional[str] = None) -> str:
    """Log a customer interaction (call, email, meeting, note)."""
    valid_types = ["call", "email", "meeting", "note", "task", "other"]
    if activity_type not in valid_types:
        activity_type = "other"
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            scheduled = None
            if scheduled_at:
                scheduled = datetime.fromisoformat(scheduled_at)
            db_activity = Activity(
                user_id=actual_user_id,
                type=activity_type,
                description=description,
                contact_id=contact_id,
                opportunity_id=opportunity_id,
                scheduled_at=scheduled,
            )
            db.add(db_activity)
            db.commit()
            db.refresh(db_activity)
            return json.dumps({
                "success": True,
                "activity_id": db_activity.id,
                "message": f"Activity '{activity_type}' logged",
                "data": {"id": db_activity.id, "type": db_activity.type}
            })
        finally:
            db.close()
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "error_type": "internal_error"})


@tool("list_activities", args_schema=ListActivitiesInput)
def list_activities(user_id: int = 1, contact_id: Optional[int] = None,
                   opportunity_id: Optional[int] = None) -> str:
    """List activities/interactions, optionally filtered by contact or opportunity."""
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            query = db.query(Activity).filter(Activity.user_id == actual_user_id)
            if contact_id:
                query = query.filter(Activity.contact_id == contact_id)
            if opportunity_id:
                query = query.filter(Activity.opportunity_id == opportunity_id)
            activities = query.order_by(Activity.created_at.desc()).limit(50).all()
            return json.dumps({
                "success": True,
                "activities": [{
                    "id": a.id,
                    "type": a.type,
                    "description": a.description,
                    "contact_id": a.contact_id,
                    "created_at": a.created_at.isoformat(),
                } for a in activities]
            })
        finally:
            db.close()
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "error_type": "internal_error"})


@tool("get_dashboard", args_schema=GetDashboardInput)
def get_dashboard(user_id: int = 1) -> str:
    """Get dashboard with sales metrics and overview."""
    try:
        actual_user_id = user_id or UserContext.get_user_id() or 1
        db: Session = get_db_session()
        try:
            from sqlalchemy import func
            total_contacts = db.query(Contact).filter(Contact.user_id == actual_user_id).count()
            total_opps = db.query(Opportunity).filter(Opportunity.user_id == actual_user_id).count()
            total_tasks = db.query(Task).filter(Task.user_id == actual_user_id).count()
            open_tasks = db.query(Task).filter(Task.user_id == actual_user_id, Task.status != "completed").count()
            pipeline_value = db.query(func.sum(Opportunity.value)).filter(
                Opportunity.user_id == actual_user_id,
                Opportunity.stage.in_(["lead", "qualified", "proposal"])
            ).scalar() or 0
            won_value = db.query(func.sum(Opportunity.value)).filter(
                Opportunity.user_id == actual_user_id,
                Opportunity.stage == "won"
            ).scalar() or 0
            return json.dumps({
                "success": True,
                "data": {
                    "total_contacts": total_contacts,
                    "total_opportunities": total_opps,
                    "total_tasks": total_tasks,
                    "open_tasks": open_tasks,
                    "pipeline_value": str(pipeline_value),
                    "won_value": str(won_value),
                }
            })
        finally:
            db.close()
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "error_type": "internal_error"})


@tool("save_chat_message", args_schema=SaveChatMessageInput)
def save_chat_message(session_id: str, role: str, content: str, contact_id: Optional[int] = None) -> str:
    """Save a chat message to memory. Used for tracking conversational context."""
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
        db: Session = get_db_session()
        try:
            messages = get_history(db, session_id, limit=limit)
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
]