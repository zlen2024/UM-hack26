from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from database import get_db
from models import User, BusinessBackground
from auth import get_current_user
from agents.business_context import save, list_backgrounds, search, get_active

router = APIRouter()

class BusinessBackgroundCreate(BaseModel):
    category: str
    title: str
    content: str
    tags: Optional[List[str]] = None
    is_active: bool = True
    priority: int = 0

class BusinessBackgroundUpdate(BusinessBackgroundCreate):
    pass

@router.post("")
def create_business_background(
    data: BusinessBackgroundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new business background entry."""
    bg = save(
        db=db,
        user_id=current_user.id,
        category=data.category,
        title=data.title,
        content=data.content,
        tags=data.tags,
        is_active=data.is_active,
        priority=data.priority
    )
    return {"success": True, "id": bg.id}

@router.get("")
def get_business_backgrounds(
    query: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List or search business backgrounds."""
    if query:
        bgs = search(db, current_user.id, query)
    else:
        bgs = list_backgrounds(db, current_user.id)
        
    return [
        {
            "id": bg.id,
            "category": bg.category,
            "title": bg.title,
            "content": bg.content,
            "tags": bg.tags_json,
            "is_active": bg.is_active,
            "priority": bg.priority,
            "usage_count": bg.usage_count,
            "created_at": bg.created_at.isoformat()
        }
        for bg in bgs
    ]

@router.get("/active")
def get_active_backgrounds(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get active business backgrounds for context."""
    bgs = get_active(db, current_user.id)
    return [
        {
            "id": bg.id,
            "category": bg.category,
            "title": bg.title,
            "content": bg.content,
            "priority": bg.priority
        }
        for bg in bgs
    ]

@router.put("/{bg_id}")
def update_business_background(
    bg_id: int,
    data: BusinessBackgroundUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a business background entry."""
    bg = save(
        db=db,
        user_id=current_user.id,
        category=data.category,
        title=data.title,
        content=data.content,
        tags=data.tags,
        is_active=data.is_active,
        priority=data.priority,
        background_id=bg_id
    )
    if not bg:
        raise HTTPException(status_code=404, detail="Background not found")
    return {"success": True}

@router.delete("/{bg_id}")
def delete_business_background(
    bg_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a business background entry."""
    bg = db.query(BusinessBackground).filter(
        BusinessBackground.id == bg_id,
        BusinessBackground.user_id == current_user.id
    ).first()
    if not bg:
        raise HTTPException(status_code=404, detail="Background not found")
    db.delete(bg)
    db.commit()
    return {"success": True}
