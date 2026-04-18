from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import User, Opportunity
from schemas import OpportunityCreate, OpportunityUpdate, OpportunityResponse
from auth import get_current_user

router = APIRouter()

STAGES = ["lead", "qualified", "proposal", "won", "lost"]


@router.get("", response_model=List[OpportunityResponse])
def get_opportunities(
    stage: Optional[str] = None,
    assigned_to: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Opportunity)
    if stage:
        query = query.filter(Opportunity.stage == stage)
    if assigned_to:
        query = query.filter(Opportunity.assigned_to == assigned_to)
    return query.order_by(Opportunity.created_at.desc()).all()


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
def get_opportunity(
    opportunity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opportunity


@router.post("", response_model=OpportunityResponse)
def create_opportunity(
    opportunity: OpportunityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_opportunity = Opportunity(**opportunity.model_dump(), user_id=current_user.id)
    db.add(db_opportunity)
    db.commit()
    db.refresh(db_opportunity)
    return db_opportunity


@router.put("/{opportunity_id}", response_model=OpportunityResponse)
def update_opportunity(
    opportunity_id: int,
    opportunity: OpportunityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not db_opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    update_data = opportunity.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_opportunity, key, value)

    db.commit()
    db.refresh(db_opportunity)
    return db_opportunity


@router.put("/{opportunity_id}/stage")
def update_opportunity_stage(
    opportunity_id: int,
    stage: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if stage not in STAGES:
        raise HTTPException(status_code=400, detail="Invalid stage")

    db_opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not db_opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    db_opportunity.stage = stage
    db.commit()
    return {"message": "Stage updated", "stage": stage}


@router.delete("/{opportunity_id}")
def delete_opportunity(
    opportunity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not db_opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    db.delete(db_opportunity)
    db.commit()
    return {"message": "Opportunity deleted successfully"}
