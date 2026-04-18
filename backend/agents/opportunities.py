from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import date
from models import Opportunity


STAGES = ["lead", "qualified", "proposal", "won", "lost"]


def create_opportunity(
    db: Session,
    user_id: int,
    title: str,
    value: Decimal,
    stage: str = "lead",
    contact_id: Optional[int] = None,
    assigned_to: Optional[int] = None,
    expected_close_date: Optional[date] = None,
) -> Dict[str, Any]:
    if stage not in STAGES:
        stage = "lead"
    db_opportunity = Opportunity(
        user_id=user_id,
        title=title,
        value=value,
        stage=stage,
        contact_id=contact_id,
        assigned_to=assigned_to,
        expected_close_date=expected_close_date,
    )
    db.add(db_opportunity)
    db.commit()
    db.refresh(db_opportunity)
    return {
        "id": db_opportunity.id,
        "user_id": db_opportunity.user_id,
        "title": db_opportunity.title,
        "value": str(db_opportunity.value),
        "stage": db_opportunity.stage,
        "contact_id": db_opportunity.contact_id,
        "assigned_to": db_opportunity.assigned_to,
        "expected_close_date": db_opportunity.expected_close_date.isoformat() if db_opportunity.expected_close_date else None,
        "created_at": db_opportunity.created_at.isoformat(),
        "updated_at": db_opportunity.updated_at.isoformat(),
    }


def get_opportunity(db: Session, user_id: int, opportunity_id: int) -> Optional[Dict[str, Any]]:
    opportunity = (
        db.query(Opportunity)
        .filter(Opportunity.id == opportunity_id, Opportunity.user_id == user_id)
        .first()
    )
    if not opportunity:
        return None
    return {
        "id": opportunity.id,
        "user_id": opportunity.user_id,
        "title": opportunity.title,
        "value": str(opportunity.value),
        "stage": opportunity.stage,
        "contact_id": opportunity.contact_id,
        "assigned_to": opportunity.assigned_to,
        "expected_close_date": opportunity.expected_close_date.isoformat() if opportunity.expected_close_date else None,
        "created_at": opportunity.created_at.isoformat(),
        "updated_at": opportunity.updated_at.isoformat(),
    }


def list_opportunities(
    db: Session,
    user_id: int,
    stage: Optional[str] = None,
    assigned_to: Optional[int] = None,
) -> List[Dict[str, Any]]:
    query = db.query(Opportunity).filter(Opportunity.user_id == user_id)
    if stage:
        query = query.filter(Opportunity.stage == stage)
    if assigned_to:
        query = query.filter(Opportunity.assigned_to == assigned_to)
    opportunities = query.order_by(Opportunity.created_at.desc()).all()
    return [
        {
            "id": o.id,
            "user_id": o.user_id,
            "title": o.title,
            "value": str(o.value),
            "stage": o.stage,
            "contact_id": o.contact_id,
            "assigned_to": o.assigned_to,
            "expected_close_date": o.expected_close_date.isoformat() if o.expected_close_date else None,
            "created_at": o.created_at.isoformat(),
            "updated_at": o.updated_at.isoformat(),
        }
        for o in opportunities
    ]


def update_opportunity(
    db: Session,
    user_id: int,
    opportunity_id: int,
    title: Optional[str] = None,
    value: Optional[Decimal] = None,
    stage: Optional[str] = None,
    contact_id: Optional[int] = None,
    assigned_to: Optional[int] = None,
    expected_close_date: Optional[date] = None,
) -> Optional[Dict[str, Any]]:
    opportunity = (
        db.query(Opportunity)
        .filter(Opportunity.id == opportunity_id, Opportunity.user_id == user_id)
        .first()
    )
    if not opportunity:
        return None

    if title is not None:
        opportunity.title = title
    if value is not None:
        opportunity.value = value
    if stage is not None and stage in STAGES:
        opportunity.stage = stage
    if contact_id is not None:
        opportunity.contact_id = contact_id
    if assigned_to is not None:
        opportunity.assigned_to = assigned_to
    if expected_close_date is not None:
        opportunity.expected_close_date = expected_close_date

    db.commit()
    db.refresh(opportunity)
    return {
        "id": opportunity.id,
        "user_id": opportunity.user_id,
        "title": opportunity.title,
        "value": str(opportunity.value),
        "stage": opportunity.stage,
        "contact_id": opportunity.contact_id,
        "assigned_to": opportunity.assigned_to,
        "expected_close_date": opportunity.expected_close_date.isoformat() if opportunity.expected_close_date else None,
        "created_at": opportunity.created_at.isoformat(),
        "updated_at": opportunity.updated_at.isoformat(),
    }


def update_opportunity_stage(
    db: Session, user_id: int, opportunity_id: int, stage: str
) -> Optional[Dict[str, Any]]:
    if stage not in STAGES:
        return None

    opportunity = (
        db.query(Opportunity)
        .filter(Opportunity.id == opportunity_id, Opportunity.user_id == user_id)
        .first()
    )
    if not opportunity:
        return None

    opportunity.stage = stage
    db.commit()
    db.refresh(opportunity)
    return {
        "id": opportunity.id,
        "user_id": opportunity.user_id,
        "title": opportunity.title,
        "value": str(opportunity.value),
        "stage": opportunity.stage,
        "contact_id": opportunity.contact_id,
        "assigned_to": opportunity.assigned_to,
        "expected_close_date": opportunity.expected_close_date.isoformat() if opportunity.expected_close_date else None,
        "created_at": opportunity.created_at.isoformat(),
        "updated_at": opportunity.updated_at.isoformat(),
    }


def delete_opportunity(db: Session, user_id: int, opportunity_id: int) -> bool:
    opportunity = (
        db.query(Opportunity)
        .filter(Opportunity.id == opportunity_id, Opportunity.user_id == user_id)
        .first()
    )
    if not opportunity:
        return False
    db.delete(opportunity)
    db.commit()
    return True