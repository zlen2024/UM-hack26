from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import User, Activity
from schemas import ActivityCreate, ActivityUpdate, ActivityResponse
from auth import get_current_user

router = APIRouter()


@router.get("", response_model=List[ActivityResponse])
def get_activities(
    contact_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Activity).filter(Activity.user_id == current_user.id)
    if contact_id:
        query = query.filter(Activity.contact_id == contact_id)
    if opportunity_id:
        query = query.filter(Activity.opportunity_id == opportunity_id)
    return query.order_by(Activity.created_at.desc()).all()


@router.get("/{activity_id}", response_model=ActivityResponse)
def get_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    activity = (
        db.query(Activity)
        .filter(Activity.id == activity_id, Activity.user_id == current_user.id)
        .first()
    )
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity


@router.post("", response_model=ActivityResponse)
def create_activity(
    activity: ActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_activity = Activity(**activity.model_dump(), user_id=current_user.id)
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity


@router.put("/{activity_id}", response_model=ActivityResponse)
def update_activity(
    activity_id: int,
    activity: ActivityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_activity = (
        db.query(Activity)
        .filter(Activity.id == activity_id, Activity.user_id == current_user.id)
        .first()
    )
    if not db_activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    update_data = activity.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_activity, key, value)

    db.commit()
    db.refresh(db_activity)
    return db_activity


@router.delete("/{activity_id}")
def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_activity = (
        db.query(Activity)
        .filter(Activity.id == activity_id, Activity.user_id == current_user.id)
        .first()
    )
    if not db_activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    db.delete(db_activity)
    db.commit()
    return {"message": "Activity deleted successfully"}
