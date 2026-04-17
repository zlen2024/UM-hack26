from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from typing import List
from database import get_db
from models import User, Contact, Opportunity, Task, Activity
from schemas import PipelineReport, ContactActivityReport, DashboardMetrics
from auth import get_current_user

router = APIRouter()


@router.get("/pipeline", response_model=List[PipelineReport])
def get_pipeline_report(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    stages = ["lead", "qualified", "proposal", "won", "lost"]
    results = []

    for stage in stages:
        count = (
            db.query(Opportunity)
            .filter(Opportunity.user_id == current_user.id, Opportunity.stage == stage)
            .count()
        )

        total = db.query(func.sum(Opportunity.value)).filter(
            Opportunity.user_id == current_user.id, Opportunity.stage == stage
        ).scalar() or Decimal("0")

        results.append(PipelineReport(stage=stage, count=count, total_value=total))

    return results


@router.get("/contacts", response_model=List[ContactActivityReport])
def get_contact_activity_report(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    contacts = db.query(Contact).filter(Contact.user_id == current_user.id).all()
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
            ContactActivityReport(
                contact_id=contact.id,
                contact_name=contact.name,
                activity_count=activity_count,
                last_activity=last_activity.created_at if last_activity else None,
            )
        )

    return results


@router.get("/dashboard", response_model=DashboardMetrics)
def get_dashboard_metrics(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    total_contacts = (
        db.query(Contact).filter(Contact.user_id == current_user.id).count()
    )

    total_opportunities = (
        db.query(Opportunity).filter(Opportunity.user_id == current_user.id).count()
    )

    pipeline_value = db.query(func.sum(Opportunity.value)).filter(
        Opportunity.user_id == current_user.id,
        Opportunity.stage.in_(["lead", "qualified", "proposal"]),
    ).scalar() or Decimal("0")

    won_value = db.query(func.sum(Opportunity.value)).filter(
        Opportunity.user_id == current_user.id, Opportunity.stage == "won"
    ).scalar() or Decimal("0")

    total_tasks = db.query(Task).filter(Task.user_id == current_user.id).count()

    open_tasks = (
        db.query(Task)
        .filter(Task.user_id == current_user.id, Task.status != "completed")
        .count()
    )

    leads_count = (
        db.query(Opportunity)
        .filter(Opportunity.user_id == current_user.id, Opportunity.stage == "lead")
        .count()
    )

    qualified_count = (
        db.query(Opportunity)
        .filter(
            Opportunity.user_id == current_user.id, Opportunity.stage == "qualified"
        )
        .count()
    )

    proposal_count = (
        db.query(Opportunity)
        .filter(Opportunity.user_id == current_user.id, Opportunity.stage == "proposal")
        .count()
    )

    return DashboardMetrics(
        total_contacts=total_contacts,
        total_opportunities=total_opportunities,
        total_tasks=total_tasks,
        open_tasks=open_tasks,
        pipeline_value=pipeline_value,
        won_value=won_value,
        leads_count=leads_count,
        qualified_count=qualified_count,
        proposal_count=proposal_count,
    )
