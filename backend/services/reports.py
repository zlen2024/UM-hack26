from sqlalchemy.orm import Session
from sqlalchemy import func, case
from decimal import Decimal
from typing import Any, Dict, List
from models import Contact, Opportunity, Task, Activity


STAGES = ["lead", "qualified", "proposal", "won", "lost"]


def _iso(value):
    """SQLite returns aggregate datetimes as strings; normalize either form."""
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def get_dashboard(db: Session, user_id: int) -> Dict[str, Any]:
    total_contacts = db.query(Contact).filter(Contact.user_id == user_id).count()

    # One pass over opportunities via conditional aggregation.
    opp = (
        db.query(
            func.count(Opportunity.id).label("total"),
            func.sum(
                case(
                    (Opportunity.stage.in_(["lead", "qualified", "proposal"]), Opportunity.value),
                    else_=0,
                )
            ).label("pipeline_value"),
            func.sum(case((Opportunity.stage == "won", Opportunity.value), else_=0)).label("won_value"),
            func.sum(case((Opportunity.stage == "lead", 1), else_=0)).label("leads"),
            func.sum(case((Opportunity.stage == "qualified", 1), else_=0)).label("qualified"),
            func.sum(case((Opportunity.stage == "proposal", 1), else_=0)).label("proposal"),
        )
        .filter(Opportunity.user_id == user_id)
        .first()
    )

    task = (
        db.query(
            func.count(Task.id).label("total"),
            func.sum(case((Task.status != "completed", 1), else_=0)).label("open"),
        )
        .filter(Task.user_id == user_id)
        .first()
    )

    return {
        "total_contacts": total_contacts,
        "total_opportunities": (opp.total or 0) if opp else 0,
        "total_tasks": (task.total or 0) if task else 0,
        "open_tasks": (task.open or 0) if task else 0,
        "pipeline_value": str((opp.pipeline_value if opp else None) or Decimal("0")),
        "won_value": str((opp.won_value if opp else None) or Decimal("0")),
        "leads_count": (opp.leads or 0) if opp else 0,
        "qualified_count": (opp.qualified or 0) if opp else 0,
        "proposal_count": (opp.proposal or 0) if opp else 0,
    }


def get_pipeline_report(db: Session, user_id: int) -> List[Dict[str, Any]]:
    rows = (
        db.query(
            Opportunity.stage,
            func.count(Opportunity.id).label("count"),
            func.sum(Opportunity.value).label("total_value"),
        )
        .filter(Opportunity.user_id == user_id)
        .group_by(Opportunity.stage)
        .all()
    )
    stage_map = {r.stage: r for r in rows}
    results = []
    for stage in STAGES:
        row = stage_map.get(stage)
        results.append(
            {
                "stage": stage,
                "count": row.count if row else 0,
                "total_value": str((row.total_value if row else None) or Decimal("0")),
            }
        )
    return results


def get_contact_activity_report(db: Session, user_id: int) -> List[Dict[str, Any]]:
    rows = (
        db.query(
            Contact.id,
            Contact.name,
            func.count(Activity.id).label("activity_count"),
            func.max(Activity.created_at).label("last_activity"),
        )
        .outerjoin(Activity, Contact.id == Activity.contact_id)
        .filter(Contact.user_id == user_id)
        .group_by(Contact.id, Contact.name)
        .all()
    )
    return [
        {
            "contact_id": r.id,
            "contact_name": r.name,
            "activity_count": r.activity_count or 0,
            "last_activity": _iso(r.last_activity),
        }
        for r in rows
    ]
