from typing import Dict, Any, Optional


def process_whatsapp_message(message_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process WhatsApp message and return echo response.

    Args:
        message_data: Structured payload with:
            - user_id: int
            - contact_name: str
            - phone: str
            - message: str

    Returns:
        Echo response with the message
    """
    user_id = message_data.get("user_id")
    contact_name = message_data.get("contact_name", "")
    phone = message_data.get("phone", "")
    message = message_data.get("message", "")

    response_text = f"Echo: {message}"

    return {
        "response": response_text,
        "user_id": user_id,
        "contact_name": contact_name,
        "phone": phone,
    }