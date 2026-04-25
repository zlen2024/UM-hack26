import json
import logging
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc, or_
from typing import List, Optional, Dict, Any
from models import BusinessBackground, BusinessRule

logger = logging.getLogger(__name__)

def save(
    db: Session,
    user_id: int,
    category: str,
    title: str,
    content: str,
    tags: Optional[List[str]] = None,
    is_active: bool = True,
    priority: int = 0,
    background_id: Optional[int] = None
) -> Optional[BusinessBackground]:
    """Create or update a business background entry."""
    if background_id:
        bg = db.query(BusinessBackground).filter(
            BusinessBackground.id == background_id,
            BusinessBackground.user_id == user_id
        ).first()
        if bg:
            bg.category = category
            bg.title = title
            bg.content = content
            if tags is not None:
                bg.tags_json = json.dumps(tags)
            bg.is_active = is_active
            bg.priority = priority
            db.commit()
            db.refresh(bg)
            return bg
        else:
            return None
            
    # Create new
    bg = BusinessBackground(
        user_id=user_id,
        category=category,
        title=title,
        content=content,
        tags_json=json.dumps(tags) if tags else None,
        is_active=is_active,
        priority=priority
    )
    db.add(bg)
    db.commit()
    db.refresh(bg)
    return bg

def list_backgrounds(db: Session, user_id: int) -> List[BusinessBackground]:
    """List all business backgrounds for a user."""
    return db.query(BusinessBackground).filter(
        BusinessBackground.user_id == user_id
    ).order_by(desc(BusinessBackground.created_at)).all()

def search(db: Session, user_id: int, query: str) -> List[BusinessBackground]:
    """Search business backgrounds by title or content."""
    return db.query(BusinessBackground).filter(
        BusinessBackground.user_id == user_id,
        or_(
            BusinessBackground.title.ilike(f"%{query}%"),
            BusinessBackground.content.ilike(f"%{query}%"),
            BusinessBackground.category.ilike(f"%{query}%")
        )
    ).order_by(desc(BusinessBackground.priority)).all()

def get_active(db: Session, user_id: int) -> List[BusinessBackground]:
    """Get all active business backgrounds for use in context."""
    return db.query(BusinessBackground).filter(
        BusinessBackground.user_id == user_id,
        BusinessBackground.is_active == True
    ).order_by(desc(BusinessBackground.priority)).all()

def get_business_rule(db: Session, user_id: int) -> Optional[str]:
    """Get the business rules text for a user."""
    rule = db.query(BusinessRule).filter(BusinessRule.user_id == user_id).first()
    if not rule or not rule.rules_text or not rule.rules_text.strip():
        return None
    return rule.rules_text

def update_business_rule(db: Session, user_id: int, rules_text: Optional[str]) -> Optional[BusinessRule]:
    """Create or update the business rule for a user."""
    rule = db.query(BusinessRule).filter(BusinessRule.user_id == user_id).first()
    
    if not rules_text or not rules_text.strip():
        if rule:
            rule.rules_text = None
            db.commit()
            db.refresh(rule)
        return None

    if rule:
        rule.rules_text = rules_text
        db.commit()
        db.refresh(rule)
        return rule
        
    rule = BusinessRule(user_id=user_id, rules_text=rules_text)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

