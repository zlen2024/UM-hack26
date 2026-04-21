from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
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
    
    # Run a single query with GROUP BY instead of 10 queries
    stage_data = db.query(
        Opportunity.stage,
        func.count(Opportunity.id).label('count'),
        func.sum(Opportunity.value).label('total_value')
    ).group_by(Opportunity.stage).all()
    
    stage_map = {row.stage: {"count": row.count, "total_value": row.total_value or Decimal("0")} for row in stage_data}
    
    results = []
    for stage in stages:
        data = stage_map.get(stage, {"count": 0, "total_value": Decimal("0")})
        results.append(PipelineReport(stage=stage, count=data["count"], total_value=data["total_value"]))

    return results


@router.get("/contacts", response_model=List[ContactActivityReport])
def get_contact_activity_report(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    # Use LEFT OUTER JOIN and GROUP BY to fetch all data in 1 query instead of N+1
    contact_data = db.query(
        Contact.id,
        Contact.name,
        func.count(Activity.id).label('activity_count'),
        func.max(Activity.created_at).label('last_activity')
    ).outerjoin(Activity, Contact.id == Activity.contact_id).group_by(Contact.id, Contact.name).all()

    results = []
    for row in contact_data:
        results.append(
            ContactActivityReport(
                contact_id=row.id,
                contact_name=row.name,
                activity_count=row.activity_count,
                last_activity=row.last_activity,
            )
        )

    return results


@router.get("/dashboard", response_model=DashboardMetrics)
def get_dashboard_metrics(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    total_contacts = db.query(Contact).count()

    # Consolidate 5 opportunity queries into 1 using conditional aggregation
    opp_metrics = db.query(
        func.count(Opportunity.id).label('total'),
        func.sum(case((Opportunity.stage.in_(["lead", "qualified", "proposal"]), Opportunity.value), else_=0)).label('pipeline_value'),
        func.sum(case((Opportunity.stage == "won", Opportunity.value), else_=0)).label('won_value'),
        func.sum(case((Opportunity.stage == "lead", 1), else_=0)).label('leads_count'),
        func.sum(case((Opportunity.stage == "qualified", 1), else_=0)).label('qualified_count'),
        func.sum(case((Opportunity.stage == "proposal", 1), else_=0)).label('proposal_count')
    ).first()

    # Consolidate 2 task queries into 1
    task_metrics = db.query(
        func.count(Task.id).label('total'),
        func.sum(case((Task.status != "completed", 1), else_=0)).label('open_tasks')
    ).first()

    return DashboardMetrics(
        total_contacts=total_contacts,
        total_opportunities=opp_metrics.total or 0 if opp_metrics else 0,
        total_tasks=task_metrics.total or 0 if task_metrics else 0,
        open_tasks=task_metrics.open_tasks or 0 if task_metrics else 0,
        pipeline_value=opp_metrics.pipeline_value or Decimal("0") if opp_metrics else Decimal("0"),
        won_value=opp_metrics.won_value or Decimal("0") if opp_metrics else Decimal("0"),
        leads_count=opp_metrics.leads_count or 0 if opp_metrics else 0,
        qualified_count=opp_metrics.qualified_count or 0 if opp_metrics else 0,
        proposal_count=opp_metrics.proposal_count or 0 if opp_metrics else 0,
    )
