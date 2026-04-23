import os
from typing import Dict, Any, Optional
from openai import OpenAI

def get_ilmu_client():
    api_key = os.getenv("ILMU_API_KEY", "")
    return OpenAI(
        base_url="https://api.ilmu.ai/v1",
        api_key=api_key,
    )

def process_whatsapp_message(message_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process WhatsApp message and return AI response.

    Args:
        message_data: Structured payload with:
            - user_id: int
            - contact_name: str
            - phone: str
            - message: str

    Returns:
        AI response from Ilmu AI model
    """
    user_id = message_data.get("user_id")
    contact_name = message_data.get("contact_name", "")
    phone = message_data.get("phone", "")
    message = message_data.get("message", "")

    client = get_ilmu_client()

    try:
        response = client.chat.completions.create(
            model="ilmu-glm-5.1",
            messages=[
                {"role": "system", "content": f"You are a helpful AI assistant replying to WhatsApp messages for a business. The ID of the business user is {user_id}. The customer's name is {contact_name}."},
                {"role": "user", "content": message},
            ],
        )
        ai_response = response.choices[0].message.content
    except Exception as e:
        print(f"[WhatsApp] Error calling Ilmu AI: {e}")
        ai_response = "I'm sorry, I'm having trouble processing your request right now."

    return {
        "response": ai_response,
        "user_id": user_id,
        "contact_name": contact_name,
        "phone": phone,
    }

def process_telegram_message(message_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process Telegram message and return AI response.

    Args:
        message_data: Structured payload with:
            - user_id: int
            - contact_name: str
            - chat_id: str
            - message: str

    Returns:
        AI response from Ilmu AI model
    """
    user_id = message_data.get("user_id")
    contact_name = message_data.get("contact_name", "")
    chat_id = message_data.get("chat_id", "")
    message = message_data.get("message", "")

    client = get_ilmu_client()

    try:
        response = client.chat.completions.create(
            model="ilmu-glm-5.1",
            messages=[
                {"role": "system", "content": f"You are a helpful AI assistant replying to Telegram messages for a business. The ID of the business user is {user_id}. The customer's name is {contact_name}."},
                {"role": "user", "content": message},
            ],
        )
        ai_response = response.choices[0].message.content
    except Exception as e:
        print(f"[Telegram] Error calling Ilmu AI: {e}")
        ai_response = "I'm sorry, I'm having trouble processing your request right now."

    return {
        "response": ai_response,
        "user_id": user_id,
        "contact_name": contact_name,
        "chat_id": chat_id,
    }
