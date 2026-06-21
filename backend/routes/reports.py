from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import User
from schemas import PipelineReport, ContactActivityReport, DashboardMetrics
from auth import get_current_user
from services import reports as reports_service

router = APIRouter()


@router.get("/pipeline", response_model=List[PipelineReport])
def get_pipeline_report(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return reports_service.get_pipeline_report(db, current_user.id)


@router.get("/contacts", response_model=List[ContactActivityReport])
def get_contact_activity_report(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return reports_service.get_contact_activity_report(db, current_user.id)


@router.get("/dashboard", response_model=DashboardMetrics)
def get_dashboard_metrics(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return reports_service.get_dashboard(db, current_user.id)
