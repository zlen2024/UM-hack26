from .state import AgentState


def should_continue(state: AgentState) -> str:
    """Route based on whether tools were called."""
    last_message = state.get("messages", [])[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "end"


def route_intent(state: AgentState) -> str:
    """Route to tools based on intent."""
    messages = state.get("messages", [])
    if not messages:
        return "respond"
    
    last_msg = messages[-1]
    msg_text = last_msg.content.lower() if hasattr(last_msg, "content") else str(last_msg)
    
    # Simple keyword-based routing
    contact_keywords = ["contact", "customer", "client", "who is", "look up", "search"]
    task_keywords = ["task", "todo", "remind", "follow up", "do this"]
    opportunity_keywords = ["deal", "opportunity", "sale", "pipeline", "value"]
    activity_keywords = ["call", "meeting", "log", "interaction", "activity"]
    dashboard_keywords = ["dashboard", "overview", "summary", "report", "metrics"]
    
    text = msg_text.lower()
    
    for kw in contact_keywords:
        if kw in text:
            return "tools"
    for kw in task_keywords:
        if kw in text:
            return "tools"
    for kw in opportunity_keywords:
        if kw in text:
            return "tools"
    for kw in activity_keywords:
        if kw in text:
            return "tools"
    for kw in dashboard_keywords:
        if kw in text:
            return "tools"
    
    return "tools"