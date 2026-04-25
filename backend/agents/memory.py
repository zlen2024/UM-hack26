import json
import logging
from sqlalchemy.orm import Session
from sqlalchemy import asc
from typing import List, Optional, Dict, Any
from models import ChatMessage

logger = logging.getLogger(__name__)

def save_message(
    db: Session,
    session_id: str,
    role: str,
    content: Optional[str] = None,
    user_id: Optional[int] = None,
    contact_id: Optional[int] = None,
    tool_calls: Optional[List[Dict[str, Any]]] = None,
    tool_results: Optional[List[Dict[str, Any]]] = None,
    token_count: Optional[int] = None,
    source: Optional[str] = None,
    is_compacted: bool = False
) -> ChatMessage:
    """Save a single chat message to the database."""
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        user_id=user_id,
        contact_id=contact_id,
        tool_calls_json=json.dumps(tool_calls) if tool_calls else None,
        tool_results_json=json.dumps(tool_results) if tool_results else None,
        token_count=token_count,
        source=source,
        is_compacted=is_compacted
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    
    # Check if compaction is needed
    try:
        compact_messages(db, session_id)
    except Exception as e:
        logger.error(f"Error compacting messages: {e}")
        
    return message

def get_history(db: Session, session_id: str, limit: int = 50) -> List[ChatMessage]:
    """Get chat history for a session."""
    return db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(asc(ChatMessage.created_at)).limit(limit).all()

def compact_messages(db: Session, session_id: str) -> None:
    """Compact chat history if it exceeds 50 messages.
    Summarizes the first 30 messages into 1.
    """
    # Count total messages for the session
    count = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).count()

    if count > 50:
        # Get the first 30 messages that are not already compacted
        messages_to_compact = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id,
            ChatMessage.is_compacted == False
        ).order_by(asc(ChatMessage.created_at)).limit(30).all()
        
        if not messages_to_compact or len(messages_to_compact) < 30:
            return

        # Prepare text for LLM
        history_text = "\n".join([f"{msg.role}: {msg.content}" for msg in messages_to_compact if msg.content])
        
        try:
            from agents.graph.agent import get_openrouter_client
            client = get_openrouter_client()
            response = client.chat.completions.create(
                model="openrouter/elephant-alpha",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes chat history. Provide a concise summary of the conversation so far."},
                    {"role": "user", "content": f"Please summarize the following chat history:\n\n{history_text}"}
                ],
                temperature=0.3,
                max_tokens=500
            )
            summary = response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM compaction failed: {e}")
            summary = "Summary of previous messages:\n" + history_text[:500] + "..."

        # Create the compacted message
        compacted_msg = ChatMessage(
            session_id=session_id,
            role="system",
            content=f"[COMPACTED 30 MESSAGES] {summary}",
            is_compacted=True
        )
        db.add(compacted_msg)
        
        # Delete the old messages
        for msg in messages_to_compact:
            db.delete(msg)
            
        db.commit()
