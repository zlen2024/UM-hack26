from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from database import get_db
from models import User
import os
import hmac
import hashlib

router = APIRouter()

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "whatsapp_verify_token_12345")


class WhatsAppWebhookPayload(BaseModel):
    object: str
    entry: List[Dict[str, Any]]


class WhatsAppMessage(BaseModel):
    from_: str
    id: str
    timestamp: str
    type: str
    text: Optional[Dict[str, str]] = None
    context: Optional[Dict[str, Any]] = None
    referral: Optional[Dict[str, Any]] = None


class WhatsAppContact(BaseModel):
    profile: Dict[str, str]
    wa_id: str
    identity_key_hash: Optional[str] = None


class WhatsAppValue(BaseModel):
    messaging_product: str
    metadata: Dict[str, str]
    contacts: Optional[List[WhatsAppContact]] = None
    messages: Optional[List[WhatsAppMessage]] = None


class WhatsAppChange(BaseModel):
    value: WhatsAppValue
    field: str


class WhatsAppEntry(BaseModel):
    id: str
    changes: List[WhatsAppChange]


def verify_webhook_token(mode: str, token: str, challenge: Optional[str] = None) -> bool:
    """Verify the webhook token from Meta"""
    expected_token = VERIFY_TOKEN
    if mode == "subscribe":
        if token == expected_token:
            return True
    elif mode == "hub.mode" and challenge:
        return True
    return False


def extract_message_data(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract relevant data from WhatsApp webhook payload"""
    try:
        entry_list = payload.get("entry", [])
        if not entry_list:
            return None

        entry = entry_list[0]
        changes = entry.get("changes", [])
        if not changes:
            return None

        change = changes[0]
        value = change.get("value", {})

        metadata = value.get("metadata", {})
        display_phone_number = metadata.get("display_phone_number")

        contacts = value.get("contacts", [])
        messages = value.get("messages", [])

        contact_data = None
        if contacts:
            contact = contacts[0]
            contact_data = {
                "name": contact.get("profile", {}).get("name", ""),
                "wa_id": contact.get("wa_id", ""),
            }

        message_data = None
        if messages:
            msg = messages[0]
            message_data = {
                "from": msg.get("from", ""),
                "id": msg.get("id", ""),
                "timestamp": msg.get("timestamp", ""),
                "type": msg.get("type", ""),
                "text_body": msg.get("text", {}).get("body", "") if msg.get("text") else "",
            }

        if not display_phone_number or not contact_data or not message_data:
            return None

        return {
            "display_phone_number": display_phone_number,
            "contact": contact_data,
            "message": message_data,
        }

    except Exception as e:
        print(f"[WhatsApp] Error extracting message data: {e}")
        return None


def find_user_by_agent_phone(db: Session, display_phone: str) -> Optional[User]:
    """Find user by their agent phone number"""
    user = db.query(User).filter(User.agent_phone_number == display_phone).first()
    return user


@router.get("/webhook")
def verify_webhook(
    hub_mode: str = Query(...),
    hub_verify_token: str = Query(...),
    hub_challenge: Optional[str] = Query(None),
):
    """Verify webhook with Meta (GET request)"""
    if hub_verify_token == VERIFY_TOKEN:
        if hub_mode == "subscribe":
            return {"hub_challenge": "Webhook verified successfully!"}
        elif hub_mode == "hub.mode" and hub_challenge:
            return {"hub_challenge": hub_challenge}
    raise HTTPException(status_code=403, detail="Webhook verification failed")


@router.post("/webhook")
def receive_webhook(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """Handle incoming WhatsApp messages from Meta"""
    extracted = extract_message_data(payload)

    if not extracted:
        return {"status": "ignored", "reason": "no_valid_message"}

    display_phone = extracted["display_phone_number"]
    contact = extracted["contact"]
    message = extracted["message"]

    user = find_user_by_agent_phone(db, display_phone)
    if not user:
        return {"status": "ignored", "reason": "user_not_found"}

    message_data = {
        "user_id": user.id,
        "contact_name": contact["name"],
        "phone": message["from"],
        "message": message["text_body"],
    }

    from agents.cs_agent import process_whatsapp_message

    result = process_whatsapp_message(message_data)

    return {"status": "processed", "result": result}