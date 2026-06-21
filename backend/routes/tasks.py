from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import User
from schemas import TaskCreate, TaskUpdate, TaskResponse
from auth import get_current_user
from services import tasks as tasks_service

router = APIRouter()

TASK_STATUSES = ["pending", "in_progress", "completed"]


@router.get("", response_model=List[TaskResponse])
def get_tasks(
    status: Optional[str] = None,
    assigned_to: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return tasks_service.list_tasks(db, current_user.id, status=status, assigned_to=assigned_to)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = tasks_service.get_task(db, current_user.id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("", response_model=TaskResponse)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return tasks_service.create_task(db, current_user.id, **task.model_dump())


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = tasks_service.update_task(
        db, current_user.id, task_id, **task.model_dump(exclude_unset=True)
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated


@router.put("/{task_id}/status")
def update_task_status(
    task_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if status not in TASK_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")

    updated = tasks_service.update_task_status(db, current_user.id, task_id, status)
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Status updated", "status": status}


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not tasks_service.delete_task(db, current_user.id, task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}
