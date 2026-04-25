from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from database import get_db
from models import User
from auth import get_current_user
from agents.memory import get_history

router = APIRouter()

@router.get("/{session_id}")
def get_session_history(
    session_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get chat history for a session."""
    messages = get_history(db, session_id, limit=limit)
    return [
        {
            "id": m.id,
            "session_id": m.session_id,
            "role": m.role,
            "content": m.content,
            "is_compacted": m.is_compacted,
            "created_at": m.created_at.isoformat()
        }
        for m in messages
    ]
