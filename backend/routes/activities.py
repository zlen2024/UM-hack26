from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import User
from schemas import ActivityCreate, ActivityUpdate, ActivityResponse
from auth import get_current_user
from services import activities as activities_service

router = APIRouter()


@router.get("", response_model=List[ActivityResponse])
def get_activities(
    contact_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return activities_service.list_activities(
        db, current_user.id, contact_id=contact_id, opportunity_id=opportunity_id
    )


@router.get("/{activity_id}", response_model=ActivityResponse)
def get_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    activity = activities_service.get_activity(db, current_user.id, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity


@router.post("", response_model=ActivityResponse)
def create_activity(
    activity: ActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return activities_service.create_activity(db, current_user.id, **activity.model_dump())


@router.put("/{activity_id}", response_model=ActivityResponse)
def update_activity(
    activity_id: int,
    activity: ActivityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = activities_service.update_activity(
        db, current_user.id, activity_id, **activity.model_dump(exclude_unset=True)
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Activity not found")
    return updated


@router.delete("/{activity_id}")
def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not activities_service.delete_activity(db, current_user.id, activity_id):
        raise HTTPException(status_code=404, detail="Activity not found")
    return {"message": "Activity deleted successfully"}
