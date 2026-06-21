"""Shared state for the customer-service agent graph.

Messages are kept in OpenAI chat format (plain dicts) because the worker has to
round-trip tool calls and tool results through the OpenAI-compatible client.
The ``append_messages`` reducer lets every node return only the *new* messages
it produced instead of rebuilding and returning the whole list.
"""

from typing import Annotated, Any, List, TypedDict


def append_messages(existing: List[dict], new: Any) -> List[dict]:
    """LangGraph reducer that appends new message dict(s) to the running list."""
    if existing is None:
        existing = []
    if new is None:
        return existing
    if isinstance(new, dict):
        new = [new]
    return list(existing) + list(new)


class AgentState(TypedDict, total=False):
    # --- Inputs (set when the graph is invoked) ---
    user_input: str
    user_id: int
    contact_name: str
    phone: str
    business_context: str
    business_rules: str

    # --- Conversation (OpenAI chat-format dicts) ---
    messages: Annotated[List[dict], append_messages]

    # --- Gatekeeper routing decision ---
    gatekeeper_response: dict

    # --- Worker / tool-loop control ---
    tool_iterations: int
    worker_error: str

    # --- Knowledge-graph extraction (runs in the background) ---
    trigger_kg: bool
    extracted_kg_data: dict
    executed_kg_queries: list
