from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from database import get_db
from models import User, WhatsAppPhoneNumber
import requests

router = APIRouter()


class WhatsAppConfigSchema(BaseModel):
    phone_number_id: str
    display_phone_number: str
    access_token: str
    verify_token: str
    user_id: int


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


def find_whatsapp_config(db: Session, display_phone: str) -> Optional[WhatsAppPhoneNumber]:
    """Find WhatsApp config by display phone number"""
    config = db.query(WhatsAppPhoneNumber).filter(
        WhatsAppPhoneNumber.display_phone_number == display_phone
    ).first()
    return config


def send_whatsapp_message(phone_number_id: str, access_token: str, recipient: str, message: str) -> Dict[str, Any]:
    """Send WhatsApp message via Meta API"""
    url = f"https://graph.facebook.com/v25.0/{phone_number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    if response.status_code >= 400:
        print(f"[WhatsApp] Error sending message: {result}")
        return {"success": False, "error": result}
    
    return {"success": True, "response": result}


@router.get("/webhook")
def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    db: Session = Depends(get_db),
):
    """Verify webhook with Meta (GET request)"""
    if hub_mode == "subscribe":
        config = db.query(WhatsAppPhoneNumber).filter(
            WhatsAppPhoneNumber.verify_token == hub_verify_token
        ).first()
        
        if config and hub_challenge:
            return PlainTextResponse(content=hub_challenge)
    
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

    whatsapp_config = find_whatsapp_config(db, display_phone)
    if not whatsapp_config:
        return {"status": "ignored", "reason": "whatsapp_config_not_found"}

    user = db.query(User).filter(User.id == whatsapp_config.user_id).first()
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

    response_text = result.get("response", "")
    if response_text:
        send_result = send_whatsapp_message(
            phone_number_id=whatsapp_config.phone_number_id,
            access_token=whatsapp_config.access_token,
            recipient=message["from"],
            message=response_text
        )
        result["sent"] = send_result

    return {"status": "processed", "result": result}


@router.post("/config")
def create_whatsapp_config(
    config: WhatsAppConfigSchema,
    db: Session = Depends(get_db)
):
    """Create or update WhatsApp phone number configuration"""
    existing = db.query(WhatsAppPhoneNumber).filter(
        WhatsAppPhoneNumber.phone_number_id == config.phone_number_id
    ).first()
    
    if existing:
        existing.display_phone_number = config.display_phone_number
        existing.access_token = config.access_token
        existing.verify_token = config.verify_token
        existing.user_id = config.user_id
    else:
        whatsapp_config = WhatsAppPhoneNumber(
            phone_number_id=config.phone_number_id,
            display_phone_number=config.display_phone_number,
            access_token=config.access_token,
            verify_token=config.verify_token,
            user_id=config.user_id
        )
        db.add(whatsapp_config)
    
    db.commit()
    return {"status": "created", "phone_number_id": config.phone_number_id}


@router.get("/config/{phone_number_id}")
def get_whatsapp_config(phone_number_id: str, db: Session = Depends(get_db)):
    """Get WhatsApp phone number configuration"""
    config = db.query(WhatsAppPhoneNumber).filter(
        WhatsAppPhoneNumber.phone_number_id == phone_number_id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    return {
        "phone_number_id": config.phone_number_id,
        "display_phone_number": config.display_phone_number,
        "user_id": config.user_id,
    }
