from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from database import get_db
from models import User, WhatsAppPhoneNumber
import requests
import hashlib
import hmac
import json

router = APIRouter()


class WhatsAppConfigSchema(BaseModel):
    phone_number_id: str
    display_phone_number: str
    access_token: str
    app_secret: Optional[str] = None
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


def validate_webhook_signature(raw_body: bytes, signature_header: str, app_secret: str) -> bool:
    """
    Validate the X-Hub-Signature-256 header from Meta's webhook POST request.
    
    Generates an HMAC-SHA256 hash using the raw JSON payload as the message
    and the app secret as the key, then compares it to the provided signature
    using hmac.compare_digest to prevent timing attacks.
    
    Returns True if the signature is valid, False otherwise.
    """
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected_hash = hmac.new(
        key=app_secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    received_hash = signature_header[len("sha256="):]

    return hmac.compare_digest(expected_hash, received_hash)


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
        print(f"[WhatsApp] Raw payload that failed: {payload}")
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

def process_whatsapp_update_and_reply(
    *,
    user_id: int,
    contact_name: str,
    recipient: str,
    message_text: str,
    phone_number_id: str,
    access_token: str,
) -> None:
    try:
        from agents.cs_agent import process_whatsapp_message

        message_data = {
            "user_id": user_id,
            "contact_name": contact_name,
            "phone": recipient,
            "message": message_text,
        }

        def send_immediate_reply(text: str):
            send_whatsapp_message(
                phone_number_id=phone_number_id,
                access_token=access_token,
                recipient=recipient,
                message=text,
            )

        result = process_whatsapp_message(message_data, send_callback=send_immediate_reply)
        response_text = result.get("response", "")

        if not response_text:
            return

        send_whatsapp_message(
            phone_number_id=phone_number_id,
            access_token=access_token,
            recipient=recipient,
            message=response_text,
        )
    except Exception as e:
        print(f"[WhatsApp] Background task error: {e}")


@router.get("/webhook")
def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    db: Session = Depends(get_db),
):
    """Verify webhook with Meta (GET request)"""
    print(f"[WhatsApp] Webhook verification - hub_mode: {hub_mode}, hub_verify_token: {hub_verify_token}, hub_challenge: {hub_challenge}")
    
    if hub_mode == "subscribe":
        config = db.query(WhatsAppPhoneNumber).filter(
            WhatsAppPhoneNumber.verify_token == hub_verify_token
        ).first()
        
        if config and hub_challenge:
            return PlainTextResponse(content=hub_challenge)
    
    raise HTTPException(status_code=403, detail="Webhook verification failed")


@router.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Handle incoming WhatsApp webhook POST from Meta.
    
    Per Meta's spec:
    - Validates the X-Hub-Signature-256 HMAC-SHA256 signature against the raw body
    - Returns HTTP 200 if the payload is valid
    - Returns HTTP 400 if the signature is invalid or missing
    """
    # Read the raw body bytes (needed for HMAC signature validation)
    raw_body = await request.body()

    # Parse JSON from raw bytes
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        print("[WhatsApp] Invalid JSON in webhook payload")
        return JSONResponse(status_code=400, content={"status": "error", "reason": "invalid_json"})

    print(f"[WhatsApp] Received webhook payload: {payload}")

    # --- HMAC-SHA256 Signature Validation ---
    # Extract the display_phone_number early to look up the app_secret
    extracted = extract_message_data(payload)
    
    signature_header = request.headers.get("X-Hub-Signature-256", "")
    
    if signature_header:
        # We need to find the app_secret to validate against.
        # Try to find it from the payload's metadata phone number first,
        # then fall back to checking all configs with an app_secret.
        app_secret = None

        if extracted:
            config = find_whatsapp_config(db, extracted["display_phone_number"])
            if config and config.app_secret:
                app_secret = config.app_secret

        if not app_secret:
            # Fallback: try all configs that have an app_secret
            configs_with_secret = db.query(WhatsAppPhoneNumber).filter(
                WhatsAppPhoneNumber.app_secret.isnot(None)
            ).all()
            for cfg in configs_with_secret:
                if validate_webhook_signature(raw_body, signature_header, cfg.app_secret):
                    app_secret = cfg.app_secret
                    break

        if app_secret:
            if not validate_webhook_signature(raw_body, signature_header, app_secret):
                print("[WhatsApp] Webhook signature validation FAILED — rejecting payload")
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "reason": "invalid_signature"},
                )
            print("[WhatsApp] Webhook signature validated successfully")
        else:
            # No app_secret configured — log a warning but still process
            # (allows onboarding before the secret is set)
            print("[WhatsApp] WARNING: No app_secret configured — skipping signature validation. "
                  "Set app_secret on your WhatsApp config for security.")
    else:
        print("[WhatsApp] WARNING: No X-Hub-Signature-256 header present in request")

    # --- Process the payload ---
    print(f"[WhatsApp] Extracted data: {extracted}")

    if not extracted:
        # Meta may send status updates, errors, etc. — acknowledge them with 200
        return JSONResponse(status_code=200, content={"status": "ok", "reason": "no_message_to_process"})

    display_phone = extracted["display_phone_number"]
    contact = extracted["contact"]
    message = extracted["message"]

    whatsapp_config = find_whatsapp_config(db, display_phone)
    print(f"[WhatsApp] Looking for config with display_phone: {display_phone}")
    print(f"[WhatsApp] Config found: {whatsapp_config}")
    
    if not whatsapp_config:
        print(f"[WhatsApp] Config not found for display_phone: {display_phone}")
        return JSONResponse(status_code=200, content={"status": "ok", "reason": "config_not_found"})

    user = db.query(User).filter(User.id == whatsapp_config.user_id).first()
    print(f"[WhatsApp] Looking for user with id: {whatsapp_config.user_id}")
    print(f"[WhatsApp] User found: {user}")
    
    if not user:
        print(f"[WhatsApp] User not found for id: {whatsapp_config.user_id}")
        return JSONResponse(status_code=200, content={"status": "ok", "reason": "user_not_found"})

    background_tasks.add_task(
        process_whatsapp_update_and_reply,
        user_id=user.id,
        contact_name=contact["name"],
        recipient=message["from"],
        message_text=message["text_body"],
        phone_number_id=whatsapp_config.phone_number_id,
        access_token=whatsapp_config.access_token,
    )

    return JSONResponse(status_code=200, content={"status": "accepted", "queued": True})


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
        existing.app_secret = config.app_secret
        existing.verify_token = config.verify_token
        existing.user_id = config.user_id
    else:
        whatsapp_config = WhatsAppPhoneNumber(
            phone_number_id=config.phone_number_id,
            display_phone_number=config.display_phone_number,
            access_token=config.access_token,
            app_secret=config.app_secret,
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
        "has_app_secret": config.app_secret is not None,
    }
