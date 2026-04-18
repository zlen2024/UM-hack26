from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from typing import Dict, Any, List
from models import Contact, Opportunity, Task, Activity


def get_dashboard(db: Session, user_id: int) -> Dict[str, Any]:
    total_contacts = db.query(Contact).filter(Contact.user_id == user_id).count()
    total_opportunities = (
        db.query(Opportunity).filter(Opportunity.user_id == user_id).count()
    )
    total_tasks = db.query(Task).filter(Task.user_id == user_id).count()
    open_tasks = (
        db.query(Task).filter(Task.user_id == user_id, Task.status != "completed").count()
    )
    pipeline_value = db.query(func.sum(Opportunity.value)).filter(
        Opportunity.user_id == user_id,
        Opportunity.stage.in_(["lead", "qualified", "proposal"]),
    ).scalar() or Decimal("0")
    won_value = (
        db.query(func.sum(Opportunity.value))
        .filter(Opportunity.user_id == user_id, Opportunity.stage == "won")
        .scalar()
        or Decimal("0")
    )
    leads_count = (
        db.query(Opportunity)
        .filter(Opportunity.user_id == user_id, Opportunity.stage == "lead")
        .count()
    )
    qualified_count = (
        db.query(Opportunity)
        .filter(Opportunity.user_id == user_id, Opportunity.stage == "qualified")
        .count()
    )
    proposal_count = (
        db.query(Opportunity)
        .filter(Opportunity.user_id == user_id, Opportunity.stage == "proposal")
        .count()
    )
    return {
        "total_contacts": total_contacts,
        "total_opportunities": total_opportunities,
        "total_tasks": total_tasks,
        "open_tasks": open_tasks,
        "pipeline_value": str(pipeline_value),
        "won_value": str(won_value),
        "leads_count": leads_count,
        "qualified_count": qualified_count,
        "proposal_count": proposal_count,
    }


def get_pipeline_report(db: Session, user_id: int) -> List[Dict[str, Any]]:
    stages = ["lead", "qualified", "proposal", "won", "lost"]
    results = []
    for stage in stages:
        count = (
            db.query(Opportunity)
            .filter(Opportunity.user_id == user_id, Opportunity.stage == stage)
            .count()
        )
        total = (
            db.query(func.sum(Opportunity.value))
            .filter(Opportunity.user_id == user_id, Opportunity.stage == stage)
            .scalar()
            or Decimal("0")
        )
        results.append({"stage": stage, "count": count, "total_value": str(total)})
    return results


def get_contact_activity_report(db: Session, user_id: int) -> List[Dict[str, Any]]:
    contacts = db.query(Contact).filter(Contact.user_id == user_id).all()
    results = []
    for contact in contacts:
        activity_count = (
            db.query(Activity).filter(Activity.contact_id == contact.id).count()
        )
        last_activity = (
            db.query(Activity)
            .filter(Activity.contact_id == contact.id)
            .order_by(Activity.created_at.desc())
            .first()
        )
        results.append(
            {
                "contact_id": contact.id,
                "contact_name": contact.name,
                "activity_count": activity_count,
                "last_activity": last_activity.created_at.isoformat() if last_activity else None,
            }
        )
    return results