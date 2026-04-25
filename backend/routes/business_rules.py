from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models import User, BusinessRule
from auth import get_current_user

router = APIRouter()

class BusinessRuleUpdate(BaseModel):
    rules_text: str

@router.get("")
def get_business_rule(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the single business rule for the current user."""
    rule = db.query(BusinessRule).filter(BusinessRule.user_id == current_user.id).first()
    if not rule:
        return {"rules_text": ""}
    return {"rules_text": rule.rules_text or ""}

@router.put("")
def update_business_rule(
    data: BusinessRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create or update the single business rule for the current user."""
    rule = db.query(BusinessRule).filter(BusinessRule.user_id == current_user.id).first()
    if rule:
        rule.rules_text = data.rules_text
    else:
        rule = BusinessRule(user_id=current_user.id, rules_text=data.rules_text)
        db.add(rule)
    db.commit()
    db.refresh(rule)
    return {"success": True, "rules_text": rule.rules_text}
