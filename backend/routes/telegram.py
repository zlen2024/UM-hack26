from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
from database import get_db
from models import User, TelegramBot
import requests
import json

router = APIRouter()

class TelegramConfigSchema(BaseModel):
    bot_token: str
    user_id: int
    webhook_url: str

def find_telegram_bot(db: Session, bot_token: str) -> Optional[TelegramBot]:
    return db.query(TelegramBot).filter(TelegramBot.bot_token == bot_token).first()

def send_telegram_message(bot_token: str, chat_id: str, message: str) -> Dict[str, Any]:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": message
    }

    response = requests.post(url, json=data)
    result = response.json()

    if response.status_code >= 400:
        print(f"[Telegram] Error sending message: {result}")
        return {"success": False, "error": result}

    return {"success": True, "response": result}

def process_telegram_update_and_reply(
    *,
    bot_token: str,
    user_id: int,
    chat_id: str,
    contact_name: str,
    text: str,
) -> None:
    try:
        from agents.cs_agent import process_telegram_message

        message_data = {
            "user_id": user_id,
            "contact_name": contact_name,
            "chat_id": chat_id,
            "message": text,
        }

        result = process_telegram_message(message_data)
        response_text = result.get("response", "")

        if not response_text:
            return

        send_telegram_message(
            bot_token=bot_token,
            chat_id=chat_id,
            message=response_text,
        )
    except Exception as e:
        print(f"[Telegram] Background task error: {e}")

@router.post("/config")
def create_telegram_config(
    config: TelegramConfigSchema,
    db: Session = Depends(get_db)
):
    """Create or update Telegram bot configuration and set webhook"""
    # 1. Save to DB
    existing = find_telegram_bot(db, config.bot_token)

    # Optional: fetch bot info to get username
    bot_info_url = f"https://api.telegram.org/bot{config.bot_token}/getMe"
    try:
        bot_res = requests.get(bot_info_url)
        if bot_res.status_code == 200:
            bot_data = bot_res.json()
            username = bot_data.get("result", {}).get("username")
        else:
            username = None
    except Exception:
        username = None

    if existing:
        existing.user_id = config.user_id
        if username:
            existing.username = username
    else:
        telegram_config = TelegramBot(
            bot_token=config.bot_token,
            user_id=config.user_id,
            username=username
        )
        db.add(telegram_config)

    db.commit()

    # 2. Set Webhook
    webhook_url = f"https://api.telegram.org/bot{config.bot_token}/setWebhook"
    set_webhook_data = {
        "url": config.webhook_url
    }
    try:
        res = requests.post(webhook_url, json=set_webhook_data)
        if res.status_code >= 400:
            print(f"[Telegram] Failed to set webhook: {res.text}")
    except Exception as e:
        print(f"[Telegram] Exception setting webhook: {e}")

    return {"status": "created", "bot_token": config.bot_token, "username": username}

@router.get("/config/{bot_token}")
def get_telegram_config(bot_token: str, db: Session = Depends(get_db)):
    """Get Telegram bot configuration"""
    config = find_telegram_bot(db, bot_token)

    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    return {
        "bot_token": config.bot_token,
        "user_id": config.user_id,
        "username": config.username,
    }

@router.post("/webhook/{bot_token}")
async def receive_webhook(bot_token: str, request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Handle incoming Telegram webhook POST."""
    raw_body = await request.body()
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        print("[Telegram] Invalid JSON in webhook payload")
        return JSONResponse(status_code=400, content={"status": "error", "reason": "invalid_json"})

    print(f"[Telegram] Received payload: {payload}")

    if "message" not in payload:
        # Might be another type of update (edited_message, callback_query, etc.)
        return JSONResponse(status_code=200, content={"status": "ignored"})

    message = payload["message"]
    chat = message.get("chat", {})
    chat_id = str(chat.get("id"))
    text_body = message.get("text", "")
    from_user = message.get("from", {})

    # Reconstruct name
    first_name = from_user.get("first_name", "")
    last_name = from_user.get("last_name", "")
    contact_name = f"{first_name} {last_name}".strip() or "Unknown"

    if not text_body:
        return JSONResponse(status_code=200, content={"status": "ignored", "reason": "no text"})

    bot_config = find_telegram_bot(db, bot_token)
    if not bot_config:
        print(f"[Telegram] Config not found for bot: {bot_token}")
        return JSONResponse(status_code=200, content={"status": "error", "reason": "config_not_found"})

    user = db.query(User).filter(User.id == bot_config.user_id).first()
    if not user:
        print(f"[Telegram] User not found for id: {bot_config.user_id}")
        return JSONResponse(status_code=200, content={"status": "error", "reason": "user_not_found"})

    background_tasks.add_task(
        process_telegram_update_and_reply,
        bot_token=bot_token,
        user_id=user.id,
        chat_id=chat_id,
        contact_name=contact_name,
        text=text_body,
    )

    return JSONResponse(status_code=200, content={"status": "accepted", "queued": True})
