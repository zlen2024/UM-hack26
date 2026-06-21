"""Nodes for the customer-service agent graph: gatekeeper, manager, worker.

Flow: gatekeeper -> (manager <-> worker)* -> END

- gatekeeper: the engaging front-line responder. Same sales persona as the
  manager but WITHOUT tools. It answers conversational turns directly and hands
  off to the manager (``agent_loop=true``) when a CRM action is needed.
- manager: same persona WITH CRM tools; may emit tool calls for the worker.
- worker: executes the tool calls and loops back to the manager.
- force_response: final tool-free answer once ``MAX_TOOL_ITERATIONS`` is hit.
"""

import json
import logging

from .llm import CHAT_MODEL, complete_json, format_tool_to_openai, get_chat_client
from .prompts import GATEKEEPER_SCHEMA, gatekeeper_system_prompt, manager_system_prompt
from .state import AgentState
from .tools import CRM_TOOLS

logger = logging.getLogger("CS_Agent_Workflow")

# How many manager -> worker round trips before we force a final answer.
MAX_TOOL_ITERATIONS = 5

_OPENAI_TOOLS = [format_tool_to_openai(t) for t in CRM_TOOLS]
_TOOL_MAP = {t.name: t for t in CRM_TOOLS}


def _short(value, limit: int = 300) -> str:
    """Truncate a value for log output."""
    text = str(value if value is not None else "")
    text = " ".join(text.split())  # collapse newlines/whitespace for one-line logs
    return text if len(text) <= limit else f"{text[:limit]}... (+{len(text) - limit} chars)"


def _history_text(messages: list) -> str:
    lines = []
    for m in messages or []:
        if not m.get("content"):
            continue
        role = "Customer" if m.get("role") == "user" else "Agent"
        lines.append(f"{role}: {m['content']}")
    return "\n".join(lines)


def gatekeeper_node(state: AgentState) -> dict:
    """Engaging front-line responder (no tools): answer directly or hand off."""
    logger.info("--- [NODE: GATEKEEPER] Executing ---")
    user_input = state.get("user_input", "")
    logger.info(f"[Gatekeeper] input: {_short(user_input)}")

    system_prompt = gatekeeper_system_prompt(state)
    history = _history_text(state.get("messages", []))
    if history:
        system_prompt += f"\n\n=== RECENT CONVERSATION ===\n{history}"

    try:
        result = complete_json(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f'Customer message: "{user_input}"\nReply with the JSON object only.'},
            ],
            schema=GATEKEEPER_SCHEMA,
            schema_name="gatekeeper_response",
            max_tokens=2000,
        )
    except Exception as e:
        logger.warning(f"[Gatekeeper] {e} -- handing off to manager")
        result = {"response": "", "agent_loop": True, "contains_knowledge": False}

    agent_loop = bool(result.get("agent_loop"))
    contains_knowledge = bool(result.get("contains_knowledge"))
    logger.info(
        f"[Gatekeeper] GENERATED -> route={'manager (needs tools)' if agent_loop else 'direct reply'}, "
        f"contains_knowledge={contains_knowledge}"
    )
    if not agent_loop:
        logger.info(f"[Gatekeeper] reply: {_short(result.get('response'))}")

    return {
        "gatekeeper_response": result,
        "messages": [{"role": "user", "content": user_input}],
        # Capture knowledge from any turn the gatekeeper flags, or any hand-off
        # to the manager (which usually means a sales-relevant signal).
        "trigger_kg": bool(agent_loop or contains_knowledge),
    }


def manager_node(state: AgentState) -> dict:
    """Plan/answer the query with tools, optionally emitting tool calls."""
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

        tool_calls = assistant_msg.get("tool_calls", [])
        logger.info(
            f"[Manager] GENERATED -> tool_calls={len(tool_calls)}"
            + (f", reply: {_short(assistant_msg.get('content'))}" if assistant_msg.get("content") else "")
        )
        for tc in tool_calls:
            logger.info(f"[Manager]   tool_call: {tc['function']['name']}({_short(tc['function']['arguments'], 200)})")

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
    logger.info(f"[Worker] executing {len(tool_calls)} tool call(s)")

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
            logger.info(f"[Worker] {tool_name}({_short(tool_args, 200)}) -> {_short(result)}")
            new_messages.append({
                "tool_call_id": tc["id"],
                "role": "tool",
                "name": tool_name,
                "content": str(result),
            })
        except Exception as e:
            error = str(e)
            logger.error(f"[Worker] {tool_name} FAILED: {error}", exc_info=True)
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

    logger.info(f"[Force Response] GENERATED -> {_short(content)}")
    return {
        "messages": [{
            "role": "assistant",
            "content": content or "I'm sorry, I couldn't fully complete that request.",
        }]
    }
