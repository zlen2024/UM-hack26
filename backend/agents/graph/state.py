from typing import TypedDict, Annotated
from langgraph.graph import add_messages


class AgentState(TypedDict):
    """State for the CRM agent graph."""
    messages: Annotated[list, add_messages]
    user_id: int
    extracted_args: dict | None
    tool_results: list[str]
    final_response: str | None