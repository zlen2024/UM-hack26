from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import User
from schemas import OpportunityCreate, OpportunityUpdate, OpportunityResponse
from auth import get_current_user
from services import opportunities as opportunities_service

router = APIRouter()

STAGES = ["lead", "qualified", "proposal", "won", "lost"]


@router.get("", response_model=List[OpportunityResponse])
def get_opportunities(
    stage: Optional[str] = None,
    assigned_to: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return opportunities_service.list_opportunities(
        db, current_user.id, stage=stage, assigned_to=assigned_to
    )


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
def get_opportunity(
    opportunity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    opportunity = opportunities_service.get_opportunity(db, current_user.id, opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opportunity


@router.post("", response_model=OpportunityResponse)
def create_opportunity(
    opportunity: OpportunityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return opportunities_service.create_opportunity(
        db, current_user.id, **opportunity.model_dump()
    )


@router.put("/{opportunity_id}", response_model=OpportunityResponse)
def update_opportunity(
    opportunity_id: int,
    opportunity: OpportunityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = opportunities_service.update_opportunity(
        db, current_user.id, opportunity_id, **opportunity.model_dump(exclude_unset=True)
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return updated


@router.put("/{opportunity_id}/stage")
def update_opportunity_stage(
    opportunity_id: int,
    stage: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if stage not in STAGES:
        raise HTTPException(status_code=400, detail="Invalid stage")

    updated = opportunities_service.update_opportunity_stage(
        db, current_user.id, opportunity_id, stage
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return {"message": "Stage updated", "stage": stage}


@router.delete("/{opportunity_id}")
def delete_opportunity(
    opportunity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not opportunities_service.delete_opportunity(db, current_user.id, opportunity_id):
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return {"message": "Opportunity deleted successfully"}
