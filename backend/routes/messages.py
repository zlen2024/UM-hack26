from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Dict, Any
from database import get_db
from models import User, ChatMessage, Contact
from auth import get_current_user

router = APIRouter()

@router.get("")
def get_all_messages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all chat messages for the current user's customers."""
    messages = db.query(ChatMessage).filter(
        ChatMessage.user_id == current_user.id
    ).order_by(desc(ChatMessage.created_at)).all()
    
    # Pre-fetch all contacts for the current user to avoid N+1 query
    contacts = db.query(Contact).filter(Contact.user_id == current_user.id).all()
    contact_by_id = {c.id: c for c in contacts}
    contact_by_phone = {c.phone: c for c in contacts if c.phone}
    
    result = []
    for m in messages:
        phone = ""
        name = "Unknown"
        if m.session_id:
            if m.session_id.startswith("wa_"):
                phone = m.session_id[3:]
            elif m.session_id.startswith("tg_"):
                phone = m.session_id[3:]
            else:
                phone = m.session_id
        
        if m.contact_id and m.contact_id in contact_by_id:
            contact = contact_by_id[m.contact_id]
            name = contact.name or name
            phone = contact.phone or phone
        elif phone in contact_by_phone:
            contact = contact_by_phone[phone]
            name = contact.name or name
            
        result.append({
            "id": m.id,
            "session_id": m.session_id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
            "sender": {
                "name": name,
                "phone": phone
            }
        })
        
    return result
