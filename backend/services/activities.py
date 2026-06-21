from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from datetime import datetime
from models import Activity


ACTIVITY_TYPES = ["call", "email", "meeting", "note", "task", "other"]


def create_activity(
    db: Session,
    user_id: int,
    type: str,
    description: Optional[str] = None,
    contact_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
    scheduled_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    if type not in ACTIVITY_TYPES:
        type = "other"

    db_activity = Activity(
        user_id=user_id,
        type=type,
        description=description,
        contact_id=contact_id,
        opportunity_id=opportunity_id,
        scheduled_at=scheduled_at,
    )
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return {
        "id": db_activity.id,
        "user_id": db_activity.user_id,
        "type": db_activity.type,
        "description": db_activity.description,
        "contact_id": db_activity.contact_id,
        "opportunity_id": db_activity.opportunity_id,
        "scheduled_at": db_activity.scheduled_at.isoformat() if db_activity.scheduled_at else None,
        "created_at": db_activity.created_at.isoformat(),
    }


def get_activity(db: Session, user_id: int, activity_id: int) -> Optional[Dict[str, Any]]:
    activity = (
        db.query(Activity)
        .filter(Activity.id == activity_id, Activity.user_id == user_id)
        .first()
    )
    if not activity:
        return None
    return {
        "id": activity.id,
        "user_id": activity.user_id,
        "type": activity.type,
        "description": activity.description,
        "contact_id": activity.contact_id,
        "opportunity_id": activity.opportunity_id,
        "scheduled_at": activity.scheduled_at.isoformat() if activity.scheduled_at else None,
        "created_at": activity.created_at.isoformat(),
    }


def list_activities(
    db: Session,
    user_id: int,
    contact_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    query = db.query(Activity).filter(Activity.user_id == user_id)
    if contact_id:
        query = query.filter(Activity.contact_id == contact_id)
    if opportunity_id:
        query = query.filter(Activity.opportunity_id == opportunity_id)
    activities = query.order_by(Activity.created_at.desc()).all()
    return [
        {
            "id": a.id,
            "user_id": a.user_id,
            "type": a.type,
            "description": a.description,
            "contact_id": a.contact_id,
            "opportunity_id": a.opportunity_id,
            "scheduled_at": a.scheduled_at.isoformat() if a.scheduled_at else None,
            "created_at": a.created_at.isoformat(),
        }
        for a in activities
    ]


def update_activity(
    db: Session,
    user_id: int,
    activity_id: int,
    type: Optional[str] = None,
    description: Optional[str] = None,
    contact_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
    scheduled_at: Optional[datetime] = None,
) -> Optional[Dict[str, Any]]:
    activity = (
        db.query(Activity)
        .filter(Activity.id == activity_id, Activity.user_id == user_id)
        .first()
    )
    if not activity:
        return None

    if type is not None and type in ACTIVITY_TYPES:
        activity.type = type
    if description is not None:
        activity.description = description
    if contact_id is not None:
        activity.contact_id = contact_id
    if opportunity_id is not None:
        activity.opportunity_id = opportunity_id
    if scheduled_at is not None:
        activity.scheduled_at = scheduled_at

    db.commit()
    db.refresh(activity)
    return {
        "id": activity.id,
        "user_id": activity.user_id,
        "type": activity.type,
        "description": activity.description,
        "contact_id": activity.contact_id,
        "opportunity_id": activity.opportunity_id,
        "scheduled_at": activity.scheduled_at.isoformat() if activity.scheduled_at else None,
        "created_at": activity.created_at.isoformat(),
    }


def delete_activity(db: Session, user_id: int, activity_id: int) -> bool:
    activity = (
        db.query(Activity)
        .filter(Activity.id == activity_id, Activity.user_id == user_id)
        .first()
    )
    if not activity:
        return False
    db.delete(activity)
    db.commit()
    return True