from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging

from database import get_db
from models import User
from auth import get_current_user
from agents.cs_agent import graph
from agents.memory import save_message, get_history
from knowledge_db import knowledge_db

logger = logging.getLogger("KG_Routes")
router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    contact_name: str = "Unknown"

class ChatResponse(BaseModel):
    response: str
    kg_extracted: bool = False
    kg_queries: list = []

@router.post("/chat", response_model=ChatResponse)
def test_chat_endpoint(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id
    session_id = f"test_chat_{user_id}"
    
    try:
        # Save user message
        save_message(db, session_id, "user", req.message, user_id=user_id)
        
        # Load history (up to 20 messages for context)
        db_history = get_history(db, session_id, limit=20, user_id=user_id)
        
        history_messages = []
        for msg in db_history[:-1]:
            if msg.role in ["user", "assistant", "system"]:
                history_messages.append({"role": msg.role, "content": msg.content})
        
        initial_state = {
            "user_input": req.message,
            "user_id": user_id,
            "contact_name": req.contact_name,
            "messages": history_messages
        }
        
        # Execute the graph
        current_state = initial_state.copy()
        for event in graph.stream(initial_state):
            for node_name, node_state in event.items():
                current_state.update(node_state)
        
        gatekeeper_resp = current_state.get("gatekeeper_response", {})
        if not gatekeeper_resp.get("agent_loop", False):
            ai_response = gatekeeper_resp.get("response", "")
        else:
            messages = current_state.get("messages", [])
            if messages:
                last_message = messages[-1]
                ai_response = last_message.get("content", "")
            else:
                ai_response = "I'm sorry, I'm having trouble processing your request right now."
        
        if ai_response:
            save_message(db, session_id, "assistant", ai_response, user_id=user_id)
            
        kg_extracted = current_state.get("trigger_kg", False)
        kg_queries = current_state.get("executed_kg_queries", [])
            
        return ChatResponse(
            response=ai_response,
            kg_extracted=kg_extracted,
            kg_queries=kg_queries
        )
        
    except Exception as e:
        logger.error(f"[KG Chat Endpoint] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/graph")
def get_graph_data(current_user: User = Depends(get_current_user)):
    try:
        data = knowledge_db.get_all_graph_data()
        return data
    except Exception as e:
        logger.error(f"[KG Graph Endpoint] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
