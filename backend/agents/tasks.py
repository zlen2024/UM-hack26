from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from datetime import datetime
from models import Task


TASK_STATUSES = ["pending", "in_progress", "completed"]
TASK_PRIORITIES = ["low", "medium", "high", "urgent"]


def create_task(
    db: Session,
    user_id: int,
    title: str,
    description: Optional[str] = None,
    status: str = "pending",
    priority: str = "medium",
    due_date: Optional[datetime] = None,
    assigned_to: Optional[int] = None,
    contact_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
) -> Dict[str, Any]:
    if status not in TASK_STATUSES:
        status = "pending"
    if priority not in TASK_PRIORITIES:
        priority = "medium"

    db_task = Task(
        user_id=user_id,
        title=title,
        description=description,
        status=status,
        priority=priority,
        due_date=due_date,
        assigned_to=assigned_to,
        contact_id=contact_id,
        opportunity_id=opportunity_id,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return {
        "id": db_task.id,
        "user_id": db_task.user_id,
        "title": db_task.title,
        "description": db_task.description,
        "status": db_task.status,
        "priority": db_task.priority,
        "due_date": db_task.due_date.isoformat() if db_task.due_date else None,
        "assigned_to": db_task.assigned_to,
        "contact_id": db_task.contact_id,
        "opportunity_id": db_task.opportunity_id,
        "created_at": db_task.created_at.isoformat(),
        "updated_at": db_task.updated_at.isoformat(),
    }


def get_task(db: Session, user_id: int, task_id: int) -> Optional[Dict[str, Any]]:
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if not task:
        return None
    return {
        "id": task.id,
        "user_id": task.user_id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "assigned_to": task.assigned_to,
        "contact_id": task.contact_id,
        "opportunity_id": task.opportunity_id,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }


def list_tasks(
    db: Session,
    user_id: int,
    status: Optional[str] = None,
    assigned_to: Optional[int] = None,
) -> List[Dict[str, Any]]:
    query = db.query(Task).filter(Task.user_id == user_id)
    if status:
        query = query.filter(Task.status == status)
    if assigned_to:
        query = query.filter(Task.assigned_to == assigned_to)
    tasks = query.order_by(Task.due_date.asc().nullslast(), Task.created_at.desc()).all()
    return [
        {
            "id": t.id,
            "user_id": t.user_id,
            "title": t.title,
            "description": t.description,
            "status": t.status,
            "priority": t.priority,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "assigned_to": t.assigned_to,
            "contact_id": t.contact_id,
            "opportunity_id": t.opportunity_id,
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat(),
        }
        for t in tasks
    ]


def update_task(
    db: Session,
    user_id: int,
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    due_date: Optional[datetime] = None,
    assigned_to: Optional[int] = None,
    contact_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if not task:
        return None

    if title is not None:
        task.title = title
    if description is not None:
        task.description = description
    if status is not None and status in TASK_STATUSES:
        task.status = status
    if priority is not None and priority in TASK_PRIORITIES:
        task.priority = priority
    if due_date is not None:
        task.due_date = due_date
    if assigned_to is not None:
        task.assigned_to = assigned_to
    if contact_id is not None:
        task.contact_id = contact_id
    if opportunity_id is not None:
        task.opportunity_id = opportunity_id

    db.commit()
    db.refresh(task)
    return {
        "id": task.id,
        "user_id": task.user_id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "assigned_to": task.assigned_to,
        "contact_id": task.contact_id,
        "opportunity_id": task.opportunity_id,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }


def update_task_status(
    db: Session, user_id: int, task_id: int, status: str
) -> Optional[Dict[str, Any]]:
    if status not in TASK_STATUSES:
        return None

    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if not task:
        return None

    task.status = status
    db.commit()
    db.refresh(task)
    return {
        "id": task.id,
        "user_id": task.user_id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "assigned_to": task.assigned_to,
        "contact_id": task.contact_id,
        "opportunity_id": task.opportunity_id,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }


def delete_task(db: Session, user_id: int, task_id: int) -> bool:
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if not task:
        return False
    db.delete(task)
    db.commit()
    return True