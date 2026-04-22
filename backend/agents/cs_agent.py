from typing import Dict, Any, Optional
from .graph.agent import run_agent


def process_whatsapp_message(message_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process WhatsApp message and return AI response.

    Args:
        message_data: Structured payload with:
            - user_id: int
            - contact_name: str
            - phone: str
            - message: str

    Returns:
        AI response from LangGraph agent
    """
    user_id = message_data.get("user_id")
    contact_name = message_data.get("contact_name", "")
    phone = message_data.get("phone", "")
    message = message_data.get("message", "")

    thread_id = f"wa-{phone}"

    result = run_agent(message=message, user_id=user_id, thread_id=thread_id)

    return {
        "response": result.get("response", "I'm here to help!"),
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
        AI response from LangGraph agent
    """
    user_id = message_data.get("user_id")
    contact_name = message_data.get("contact_name", "")
    chat_id = message_data.get("chat_id", "")
    message = message_data.get("message", "")

    thread_id = f"tg-{chat_id}"

    result = run_agent(message=message, user_id=user_id, thread_id=thread_id)

    return {
        "response": result.get("response", "I'm here to help!"),
        "user_id": user_id,
        "contact_name": contact_name,
        "chat_id": chat_id,
    }
