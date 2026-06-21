"""Nodes for the customer-service agent graph: router, manager, worker.

Flow: router -> (manager <-> worker)* -> END
Every customer-facing reply is written by the manager (one engaging, on-brand
sales persona), so the router only records the turn and flags it for background
knowledge-graph extraction. The manager plans/answers and may emit tool calls;
the worker executes them and loops back. ``MAX_TOOL_ITERATIONS`` caps the loop,
after which ``force_response`` produces a final plain-text answer.
"""

import json
import logging
import re

from .llm import CHAT_MODEL, format_tool_to_openai, get_chat_client
from .prompts import manager_system_prompt
from .state import AgentState
from .tools import CRM_TOOLS

logger = logging.getLogger("CS_Agent_Workflow")

# How many manager -> worker round trips before we force a final answer.
MAX_TOOL_ITERATIONS = 5

_OPENAI_TOOLS = [format_tool_to_openai(t) for t in CRM_TOOLS]
_TOOL_MAP = {t.name: t for t in CRM_TOOLS}

_GREETINGS = {
    "hi", "hello", "hey", "hye", "hye again", "greetings", "good morning",
    "good afternoon", "good evening", "thanks", "thank you", "ok", "okay",
}


def gatekeeper_node(state: AgentState) -> dict:
    """Record the turn and flag it for KG extraction; the manager writes the reply.

    No LLM call and no canned replies — routing everything to the manager means
    every message gets the same engaging, channel-formatted, business-aware
    answer instead of a weaker router-written one.
    """
    logger.info("--- [NODE: ROUTER] Executing ---")
    user_input = state.get("user_input", "")

    normalized = re.sub(r"[^a-z\s]", "", user_input.lower()).strip()
    is_trivial = normalized in _GREETINGS or len(normalized) < 2

    return {
        # agent_loop stays True so the manager always answers; downstream readers
        # (response extraction, kg route) keep working unchanged.
        "gatekeeper_response": {
            "response": "",
            "agent_loop": True,
            "query": user_input,
            "contains_knowledge": not is_trivial,
        },
        "messages": [{"role": "user", "content": user_input}],
        # Extract knowledge from any non-trivial turn (greetings/thanks excluded).
        "trigger_kg": not is_trivial,
    }


def manager_node(state: AgentState) -> dict:
    """Plan/answer the query, optionally emitting tool calls for the worker."""
    logger.info("--- [NODE: MANAGER] Executing ---")
    messages = state.get("messages", [])
    if not messages:
        gatekeeper_resp = state.get("gatekeeper_response", {})
        query = gatekeeper_resp.get("query", state.get("user_input", ""))
        messages = [{"role": "user", "content": query}]

    api_messages = [{"role": "system", "content": manager_system_prompt(state)}] + messages

    try:
        response = get_chat_client().chat.completions.create(
            model=CHAT_MODEL,
            messages=api_messages,
            tools=_OPENAI_TOOLS,
            temperature=0,
            max_tokens=2000,
        )
        msg = response.choices[0].message

        assistant_msg = {"role": "assistant"}
        if msg.content is not None:
            assistant_msg["content"] = msg.content
        if msg.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]
        logger.info(f"[Manager] tool_calls={len(assistant_msg.get('tool_calls', []))}")
        return {"messages": [assistant_msg], "worker_error": ""}
    except Exception as e:
        logger.error(f"[Manager] Error: {e}", exc_info=True)
        return {
            "messages": [{
                "role": "assistant",
                "content": "I'm sorry, I'm having trouble planning the tasks to resolve your query.",
            }],
            "worker_error": str(e),
        }


def worker_node(state: AgentState) -> dict:
    """Execute the manager's tool calls and return one tool message per call."""
    logger.info("--- [NODE: WORKER] Executing ---")
    messages = state.get("messages", [])
    if not messages:
        return {}

    tool_calls = messages[-1].get("tool_calls", [])
    logger.info(f"[Worker] Executing {len(tool_calls)} tool call(s).")

    error = ""
    user_id = state.get("user_id")
    new_messages = []

    for tc in tool_calls:
        tool_name = tc.get("function", {}).get("name", "unknown")
        try:
            args_str = tc["function"]["arguments"]
            tool_args = json.loads(args_str) if args_str else {}
            if "user_id" not in tool_args and user_id:
                tool_args["user_id"] = user_id

            if tool_name not in _TOOL_MAP:
                raise ValueError(f"Tool '{tool_name}' not found.")

            result = _TOOL_MAP[tool_name].invoke(tool_args)
            new_messages.append({
                "tool_call_id": tc["id"],
                "role": "tool",
                "name": tool_name,
                "content": str(result),
            })
        except Exception as e:
            error = str(e)
            logger.error(f"[Worker] Tool '{tool_name}' failed: {error}", exc_info=True)
            new_messages.append({
                "tool_call_id": tc["id"],
                "role": "tool",
                "name": tool_name,
                "content": f"Error: {error}",
            })

    return {
        "messages": new_messages,
        "worker_error": error,
        "tool_iterations": state.get("tool_iterations", 0) + 1,
    }


def force_response_node(state: AgentState) -> dict:
    """Produce a final answer (no tools) once the tool-loop cap is reached."""
    logger.info("--- [NODE: FORCE_RESPONSE] Tool-loop cap reached ---")
    messages = list(state.get("messages", []))

    # Drop a dangling assistant tool-call message that has no tool replies, so the
    # API doesn't reject the request.
    if messages and messages[-1].get("role") == "assistant" and messages[-1].get("tool_calls"):
        messages = messages[:-1]

    system_prompt = manager_system_prompt(state) + (
        "\n\nYou have reached the tool-call limit. Provide your best final answer "
        "to the user now WITHOUT calling any tools."
    )

    try:
        response = get_chat_client().chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "system", "content": system_prompt}] + messages,
            temperature=0,
            max_tokens=1500,
        )
        content = response.choices[0].message.content
    except Exception as e:
        logger.error(f"[Force Response] Error: {e}", exc_info=True)
        content = None

    return {
        "messages": [{
            "role": "assistant",
            "content": content or "I'm sorry, I couldn't fully complete that request.",
        }]
    }
