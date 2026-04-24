import os
import requests
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import ChateryWhatsAppSession, User
from pydantic import BaseModel
import json
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logger = logging.getLogger("chatery")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

router = APIRouter()

CHATERY_API_URL = "https://chatery-whatsapp.fly.dev/api/whatsapp"
CHATERY_API_KEY = os.environ.get("CHATERY_API_KEY", "")

def get_chatery_headers():
    headers = {"Content-Type": "application/json"}
    if CHATERY_API_KEY:
        headers["X-Api-Key"] = CHATERY_API_KEY
    return headers

class ConnectRequest(BaseModel):
    user_id: int
    webhook_url: str

@router.post("/connect")
def connect_chatery(req: ConnectRequest, db: Session = Depends(get_db)):
    session_id = str(req.user_id)
    logger.info(f"Initiating Chatery connection for user {req.user_id} with session_id {session_id}")

    # Check if session exists in DB, else create
    session = db.query(ChateryWhatsAppSession).filter(ChateryWhatsAppSession.session_id == session_id).first()
    if not session:
        logger.info(f"Creating new DB session for {session_id}")
        session = ChateryWhatsAppSession(session_id=session_id, user_id=req.user_id, status="connecting")
        db.add(session)
        db.commit()
    else:
        logger.info(f"Updating existing DB session for {session_id} to connecting")
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
    headers = get_chatery_headers()

    logger.info(f"Sending POST to Chatery API: {url} with webhook {req.webhook_url}")
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        logger.info(f"Chatery API response status: {response.status_code}")
        logger.debug(f"Chatery API response data: {data}")
        
        if data.get("success"):
            logger.info(f"Successfully initiated connection for session {session_id}")
            return data
        else:
            logger.error(f"Chatery API connection failed for session {session_id}: {data.get('message')}")
            raise HTTPException(status_code=400, detail=data.get("message", "Failed to connect to Chatery API"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Exception during Chatery connection for {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{user_id}")
def get_status(user_id: int, db: Session = Depends(get_db)):
    session_id = str(user_id)
    session = db.query(ChateryWhatsAppSession).filter(ChateryWhatsAppSession.session_id == session_id).first()
    if not session:
        logger.debug(f"Status check for {session_id}: Session not found in DB, returning disconnected")
        return {"status": "disconnected"}
    logger.debug(f"Status check for {session_id}: returning {session.status}")
    return {"status": session.status}

@router.get("/qr/{user_id}")
def get_qr(user_id: int, db: Session = Depends(get_db)):
    session_id = str(user_id)
    url = f"{CHATERY_API_URL}/sessions/{session_id}/qr"
    logger.info(f"Fetching QR code for session {session_id} from {url}")
    try:
        response = requests.get(url, headers=get_chatery_headers())
        logger.info(f"Chatery QR API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Successfully retrieved QR data for session {session_id}")
            return data
        else:
            logger.error(f"Failed to fetch QR code for session {session_id}: Status {response.status_code}, Body: {response.text}")
            raise HTTPException(status_code=400, detail=f"Failed to get QR code: {response.text}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Exception during QR code fetch for {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/disconnect")
def disconnect_chatery(req: ConnectRequest, db: Session = Depends(get_db)):
    session_id = str(req.user_id)
    logger.info(f"Disconnecting session {session_id}")
    
    session = db.query(ChateryWhatsAppSession).filter(ChateryWhatsAppSession.session_id == session_id).first()
    if session:
        logger.info(f"Deleting session {session_id} from database")
        db.delete(session)
        db.commit()

    url = f"{CHATERY_API_URL}/sessions/{session_id}"
    try:
        logger.info(f"Sending DELETE to Chatery API: {url}")
        requests.delete(url, headers=get_chatery_headers())
        logger.info(f"Successfully sent disconnect request to Chatery for {session_id}")
    except Exception as e:
        logger.error(f"Error deleting session {session_id} on Chatery API: {e}")

    return {"success": True, "message": "Session disconnected"}

@router.post("/webhook")
async def chatery_webhook(request: Request, db: Session = Depends(get_db)):
    logger.info("Received Chatery webhook request")
    try:
        payload = await request.json()
        logger.info(f"Webhook payload: {json.dumps(payload)}")
    except Exception as e:
        logger.error(f"Failed to parse webhook JSON: {e}")
        return {"status": "error", "message": "Invalid JSON"}

    event = payload.get("event")
    session_id = payload.get("sessionId")
    logger.info(f"Webhook Event: {event}, Session ID: {session_id}")

    if not session_id:
        logger.warning("Webhook received without a sessionId")
        return {"status": "ok", "message": "No session ID"}

    if event == "connection.update":
        status = payload.get("data", {}).get("status") or payload.get("status")
        logger.info(f"Connection update for {session_id}: status={status}")
        
        if status:
            session = db.query(ChateryWhatsAppSession).filter(ChateryWhatsAppSession.session_id == session_id).first()
            if session:
                logger.info(f"Updating DB session {session_id} to status '{status}'")
                session.status = status
                db.commit()
            else:
                logger.warning(f"Connection update received for unknown session {session_id}")
        return {"status": "ok"}

    if event == "message":
        message_data = payload.get("data", {})
        message_id = message_data.get("id")
        from_phone = message_data.get("from")
        contact_name = message_data.get("id") 
        
        # Extract text based on message type
        msg_type = message_data.get("type")
        if msg_type == "text":
            text = message_data.get("content")
        else:
            text = message_data.get("caption")
            
        if not text:
            text = ""
        
        logger.info(f"Message received for session {session_id} from {from_phone} ({contact_name})")
        logger.debug(f"Message text: {text}")

        if not from_phone:
            logger.warning("Message webhook: Missing senderPhone")
            return {"status": "ok", "message": "Missing senderPhone"}

        if not text.strip():
            logger.info("Message webhook: Empty text, skipping AI processing")
            return {"status": "ok", "message": "Empty text"}

        session = db.query(ChateryWhatsAppSession).filter(ChateryWhatsAppSession.session_id == session_id).first()
        if not session:
            logger.warning(f"Message webhook: Session {session_id} not found in DB")
            return {"status": "ok", "message": "Session not found in DB"}

        user = db.query(User).filter(User.id == session.user_id).first()
        if not user:
            logger.warning(f"Message webhook: User {session.user_id} not found for session {session_id}")
            return {"status": "ok", "message": "User not found"}

        agent_payload = {
            "user_id": user.id,
            "contact_name": contact_name,
            "phone": from_phone,
            "message": text,
        }

        logger.info(f"Processing message via cs_agent for user {user.id}")
        logger.info(f"Agent payload being sent: {json.dumps(agent_payload)}")
        from agents.cs_agent import process_whatsapp_message
        result = process_whatsapp_message(agent_payload)
        logger.info(f"Agent result received: {json.dumps(result)}")
        response_text = result.get("response", "")

        if response_text:
            logger.info(f"Sending automated reply to {from_phone} for session {session_id}")
            url = f"{CHATERY_API_URL}/chats/send-text"
            send_payload = {
                "sessionId": session_id,
                "chatId": from_phone.replace('@s.whatsapp.net', '') if from_phone else "",
                "message": response_text,
                "typingTime": 1500  # Make it look natural
            }

            try:
                requests.post(url, json=send_payload, headers=get_chatery_headers())
                logger.info(f"Successfully sent automated reply to {from_phone}")
            except Exception as e:
                logger.error(f"Error sending automated reply via Chatery: {e}")

        return {"status": "processed", "result": result}

    if event == "message.sent":
        message_data = payload.get("data", {})
        to_phone = message_data.get("to") or message_data.get("chatId")
        logger.info(f"Message sent confirmation received for session {session_id} to {to_phone}")
        return {"status": "ok", "message": "Message sent confirmation"}

    logger.info(f"Unhandled webhook event: {event}")
    return {"status": "ok", "message": "Unhandled event"}
