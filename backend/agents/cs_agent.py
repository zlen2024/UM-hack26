"""Public entry points for the customer-service agent.

The LangGraph workflow itself lives in ``agents.graph``. This module is a thin
adapter between the messaging channels (WhatsApp / Telegram / Chatery) and that
graph: it loads context, runs the graph, persists the conversation, and kicks
off background knowledge-graph extraction.
"""

import logging
import threading
from typing import Any, Callable, Dict, Optional

from .graph import graph
from .graph.kg import evaluate_kg_trigger, run_kg_extraction_in_background
from .graph.llm import get_chat_client, get_ilmu_client, parse_llm_json

logger = logging.getLogger("CS_Agent_Workflow")

# Per-channel differences: session-id prefix and the field carrying the
# conversation id in the incoming payload.
_CHANNELS = {
    "whatsapp": {"prefix": "wa", "id_field": "phone"},
    "telegram": {"prefix": "tg", "id_field": "chat_id"},
}

_FALLBACK = "I'm sorry, I'm having trouble processing your request right now."


def _load_context(db, user_id: Optional[int], message: str) -> tuple[str, str]:
    """Build the (business_context + kg_context, business_rules) prompt blocks."""
    from agents.business_context import get_active, get_business_rule

    business_context = ""
    business_rules = ""
    kg_context = ""

    if user_id:
        active_bgs = get_active(db, user_id)
        if active_bgs:
            business_context = "=== BUSINESS BACKGROUND ===\n"
            for bg in active_bgs:
                business_context += f"[{bg.category}] {bg.title}: {bg.content}\n"
            business_context += "\n"

        rules_text = get_business_rule(db, user_id)
        if rules_text:
            business_rules = f"=== BUSINESS RULES ===\n{rules_text}\n\n"

        try:
            from knowledge_db import KnowledgeDBFactory

            kg_context = KnowledgeDBFactory.get_instance(user_id).get_relevant_context(message)
        except Exception as e:
            logger.error(f"[Agent] Error querying KG context: {e}")

    return business_context + kg_context, business_rules


def _run_graph(initial_state: dict, send_callback: Optional[Callable[[str], None]]) -> dict:
    """Stream the graph, returning the final state.

    The gatekeeper's preliminary "on it" reply is sent only when the agent is
    actually about to run tools (i.e. there will be a real wait). For plain
    conversational turns the manager's single reply is sent on its own, so the
    user never gets two messages that both answer the same thing.
    """
    final_state = dict(initial_state)
    preliminary_sent = False

    for state in graph.stream(initial_state, stream_mode="values"):
        final_state = state
        if preliminary_sent or not send_callback:
            continue

        resp = state.get("gatekeeper_response") or {}
        messages = state.get("messages") or []
        last_message = messages[-1] if messages else {}
        # Only ack when a tool call is pending execution (the slow path).
        if resp.get("response") and last_message.get("role") == "assistant" and last_message.get("tool_calls"):
            logger.info(f"[Agent] Sending preliminary response: {resp['response']}")
            send_callback(resp["response"])
            preliminary_sent = True

    return final_state


def _extract_response(state: dict) -> str:
    """Pull the user-facing reply out of the final graph state."""
    resp = state.get("gatekeeper_response", {})
    if not resp.get("agent_loop", False):
        return resp.get("response", "")

    for message in reversed(state.get("messages", [])):
        if message.get("role") == "assistant" and message.get("content"):
            return message["content"]
    return _FALLBACK


def _run_agent(message_data: Dict[str, Any], channel: str,
               send_callback: Optional[Callable[[str], None]]) -> str:
    """Shared pipeline for every messaging channel. Returns the reply text."""
    cfg = _CHANNELS[channel]
    user_id = message_data.get("user_id")
    contact_name = message_data.get("contact_name", "")
    conversation_id = message_data.get(cfg["id_field"], "")
    message = message_data.get("message", "")
    session_id = f"{cfg['prefix']}_{conversation_id}"

    try:
        from database import SessionLocal
        from agents.memory import get_history, save_message

        db = SessionLocal()
        try:
            context_block, rules_block = _load_context(db, user_id, message)

            save_message(db, session_id, "user", message, user_id=user_id)
            db_history = get_history(db, session_id, limit=20, user_id=user_id)
            history_messages = [
                {"role": m.role, "content": m.content}
                for m in db_history[:-1]  # exclude the message we just saved
                if m.role in ("user", "assistant", "system")
            ]

            initial_state = {
                "user_input": message,
                "user_id": user_id,
                "contact_name": contact_name,
                "phone": conversation_id,
                "business_context": context_block,
                "business_rules": rules_block,
                "messages": history_messages,
            }

            final_state = _run_graph(initial_state, send_callback)
            ai_response = _extract_response(final_state)

            if ai_response:
                save_message(db, session_id, "assistant", ai_response, user_id=user_id)

            if final_state.get("trigger_kg"):
                logger.info("[Agent] Triggering background KG extraction...")
                threading.Thread(
                    target=run_kg_extraction_in_background,
                    args=(final_state,),
                    daemon=True,
                ).start()

            return ai_response
        finally:
            db.close()
    except Exception as e:
        logger.error(f"[Agent] Error running graph: {e}", exc_info=True)
        return _FALLBACK


def process_whatsapp_message(
    message_data: Dict[str, Any],
    send_callback: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """Process a WhatsApp message and return the AI response.

    ``message_data`` keys: user_id, contact_name, phone, message.
    ``send_callback`` optionally receives the gatekeeper's preliminary reply.
    """
    response = _run_agent(message_data, "whatsapp", send_callback)
    return {
        "response": response,
        "user_id": message_data.get("user_id"),
        "contact_name": message_data.get("contact_name", ""),
        "phone": message_data.get("phone", ""),
    }


def process_telegram_message(
    message_data: Dict[str, Any],
    send_callback: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """Process a Telegram message and return the AI response.

    ``message_data`` keys: user_id, contact_name, chat_id, message.
    ``send_callback`` optionally receives the gatekeeper's preliminary reply.
    """
    response = _run_agent(message_data, "telegram", send_callback)
    return {
        "response": response,
        "user_id": message_data.get("user_id"),
        "contact_name": message_data.get("contact_name", ""),
        "chat_id": message_data.get("chat_id", ""),
    }


__all__ = [
    "graph",
    "process_whatsapp_message",
    "process_telegram_message",
    "evaluate_kg_trigger",
    "get_chat_client",
    "get_ilmu_client",
    "parse_llm_json",
    "run_kg_extraction_in_background",
]
