import os
import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import ChateryWhatsAppSession, User
from pydantic import BaseModel
import json

router = APIRouter()

CHATERY_API_URL = "https://chatery-whatsapp.fly.dev/api/whatsapp"

class ConnectRequest(BaseModel):
    user_id: int
    webhook_url: str

@router.post("/connect")
def connect_chatery(req: ConnectRequest, db: Session = Depends(get_db)):
    session_id = str(req.user_id)

    # Check if session exists in DB, else create
    session = db.query(ChateryWhatsAppSession).filter(ChateryWhatsAppSession.session_id == session_id).first()
    if not session:
        session = ChateryWhatsAppSession(session_id=session_id, user_id=req.user_id, status="connecting")
        db.add(session)
        db.commit()
    else:
        session.status = "connecting"
        db.commit()

    # Call Chatery API to connect
    url = f"{CHATERY_API_URL}/sessions/{session_id}/connect"
    payload = {
        "metadata": {"userId": req.user_id},
        "webhooks": [
            {
                "url": req.webhook_url,
                "events": ["all"]
            }
        ]
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        if data.get("success"):
            return data
        else:
            raise HTTPException(status_code=400, detail=data.get("message", "Failed to connect to Chatery API"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{user_id}")
def get_status(user_id: int, db: Session = Depends(get_db)):
    session_id = str(user_id)
    session = db.query(ChateryWhatsAppSession).filter(ChateryWhatsAppSession.session_id == session_id).first()
    if not session:
        return {"status": "disconnected"}
    return {"status": session.status}

@router.get("/qr/{user_id}")
def get_qr(user_id: int, db: Session = Depends(get_db)):
    session_id = str(user_id)
    url = f"{CHATERY_API_URL}/sessions/{session_id}/qr/image"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            raise HTTPException(status_code=400, detail="Failed to get QR code")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/disconnect")
def disconnect_chatery(req: ConnectRequest, db: Session = Depends(get_db)):
    session_id = str(req.user_id)
    session = db.query(ChateryWhatsAppSession).filter(ChateryWhatsAppSession.session_id == session_id).first()
    if session:
        db.delete(session)
        db.commit()

    url = f"{CHATERY_API_URL}/sessions/{session_id}"
    try:
        requests.delete(url)
    except Exception as e:
        print(f"Error deleting session on Chatery API: {e}")

    return {"success": True, "message": "Session disconnected"}

@router.post("/webhook")
async def chatery_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
    except Exception as e:
        return {"status": "error", "message": "Invalid JSON"}

    event = payload.get("event")
    session_id = payload.get("sessionId")

    if not session_id:
        return {"status": "ok", "message": "No session ID"}

    if event == "connection.update":
        status = payload.get("data", {}).get("status") or payload.get("status")
        if status:
            session = db.query(ChateryWhatsAppSession).filter(ChateryWhatsAppSession.session_id == session_id).first()
            if session:
                session.status = status
                db.commit()
        return {"status": "ok"}

    if event == "message":
        message_data = payload.get("data", {})
        from_phone = message_data.get("from")
        text = message_data.get("text")

        session = db.query(ChateryWhatsAppSession).filter(ChateryWhatsAppSession.session_id == session_id).first()
        if not session:
            return {"status": "ok", "message": "Session not found in DB"}

        user = db.query(User).filter(User.id == session.user_id).first()
        if not user:
            return {"status": "ok", "message": "User not found"}

        agent_payload = {
            "user_id": user.id,
            "contact_name": "Chatery Contact",  # Chatery webhook might not provide contact name in this event
            "phone": from_phone,
            "message": text,
        }

        from agents.cs_agent import process_whatsapp_message
        result = process_whatsapp_message(agent_payload)
        response_text = result.get("response", "")

        if response_text:
            url = f"{CHATERY_API_URL}/chats/send-text"
            send_payload = {
                "sessionId": session_id,
                "chatId": from_phone.replace('@s.whatsapp.net', '') if from_phone else "",
                "message": response_text
            }
            try:
                requests.post(url, json=send_payload, headers={"Content-Type": "application/json"})
            except Exception as e:
                print(f"Error sending reply via Chatery: {e}")

        return {"status": "processed", "result": result}

    return {"status": "ok", "message": "Unhandled event"}
