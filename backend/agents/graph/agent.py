import os
import json
from typing import Optional
from openai import OpenAI
from langchain_core.messages import HumanMessage, AIMessage

from .state import AgentState
from .tools import CRM_TOOLS, UserContext


SYSTEM_PROMPT = """You are a helpful CRM customer service agent for a sales team.

You have access to these tools:
- create_contact, get_contact, list_contacts, update_contact: Manage customer contacts
- create_opportunity, get_opportunity, list_opportunities, update_opportunity_stage: Manage sales deals
- create_task, get_task, list_tasks, update_task_status: Manage follow-up tasks
- create_activity, list_activities: Log customer interactions
- get_dashboard: View sales metrics

Be concise and helpful. When you complete an action, confirm it to the user."""


def get_openrouter_client():
    """Get OpenRouter client."""
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY", ""),
    )


# Create OpenAI-compatible client (OpenRouter)
openai_client = get_openrouter_client()


def build_graph():
    """Build the LangGraph workflow."""
    from langgraph.graph import StateGraph, END
    
    workflow = StateGraph(AgentState)
    
    workflow.add_node("agent", lambda state: agent_node(state))
    workflow.add_node("tools", lambda state: execute_tools_node(state))
    
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_use_tools,
        {"tools": "tools", "respond": END}
    )
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()


def should_use_tools(state: AgentState) -> str:
    """Determine if tools should be called or if we should respond."""
    messages = state.get("messages", [])
    tool_results = state.get("tool_results", [])
    
    # If we just got tool results, respond to user
    if tool_results:
        return "respond"
    
    if not messages:
        return "respond"
    
    last_msg = messages[-1]
    
    # Check if LLM wants to call tools
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        if last_msg.tool_calls:
            return "tools"
    
    # Check if this is a tool result response (not a tool call)
    # If tool_results is empty and there's no tool_calls, respond
    return "respond"


def agent_node(state: AgentState) -> dict:
    """Main agent node using LLM."""
    messages = state.get("messages", [])
    user_id = state.get("user_id", 1)
    
    # Load business context
    from agents.business_context import get_active
    from database import SessionLocal
    db = SessionLocal()
    try:
        active_bgs = get_active(db, user_id)
        bg_text = ""
        if active_bgs:
            bg_text = "\n\nBusiness Context:\n" + "\n".join(
                [f"[{bg.category}] {bg.title}: {bg.content}" for bg in active_bgs]
            )
    finally:
        db.close()
    
    system_content = SYSTEM_PROMPT + bg_text
    api_messages = [{"role": "system", "content": system_content}]
    
    for msg in messages:
        if msg.type == "human":
            role = "user"
        elif msg.type == "system":
            role = "system"
        else:
            role = "assistant"
        api_messages.append({"role": role, "content": msg.content})
    
    # Get tool definitions
    tool_defs = []
    for t in CRM_TOOLS:
        try:
            tool_defs.append({
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.args_schema.schema() if hasattr(t, "args_schema") else {"type": "object", "properties": {}}
                }
            })
        except:
            tool_defs.append({
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": {"type": "object", "properties": {}}
                }
            })
    
    try:
        response = openai_client.chat.completions.create(
            model="openrouter/elephant-alpha",
            messages=api_messages,
            tools=tool_defs if tool_defs else None,
            temperature=0.7,
            max_tokens=1000,
        )
        
        choice = response.choices[0]
        message = choice.message
        
        return {
            "messages": [message],
            "tool_results": [],
        }
    except Exception as e:
        return {
            "messages": [AIMessage(content=f"I'm here to help with your CRM. What would you like to do?")],
            "tool_results": [],
        }


def execute_tools_node(state: AgentState) -> dict:
    """Execute tools called by the LLM."""
    messages = state.get("messages", [])
    user_id = state.get("user_id", 1)
    
    if not messages:
        return {"tool_results": [], "messages": []}
    
    last_message = messages[-1]
    results = []
    new_messages = []
    
    # Set user context for tools
    UserContext.set_user_id(user_id)
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tc in last_message.tool_calls:
            tool_name = tc.name if hasattr(tc, 'name') else tc.function.name
            tool_args = tc.arguments if isinstance(tc.arguments, dict) else {}
            
            # Add user_id to tool args
            tool_args["user_id"] = user_id
            
            try:
                for tool in CRM_TOOLS:
                    if tool.name == tool_name:
                        result = tool.invoke(tool_args)
                        results.append(str(result))
                        break
            except Exception as e:
                results.append(f'{{"error": "{str(e)}"}}')
    
    return {
        "tool_results": results,
        "messages": [],
    }


# Singleton compiled app
_app = None


def get_app():
    """Get or build the compiled graph."""
    global _app
    if _app is None:
        _app = build_graph()
    return _app


app = get_app()


def run_agent(message: str, user_id: int = 1, thread_id: Optional[str] = None) -> dict:
    """Run the CRM agent with a message."""
    import uuid
    from database import SessionLocal
    from agents.memory import save_message, get_history
    
    session_id = thread_id or str(uuid.uuid4())
    db = SessionLocal()
    
    try:
        # Load chat history
        db_history = get_history(db, session_id, limit=50)
        history_messages = []
        for msg in db_history:
            if msg.role == "user":
                history_messages.append(("user", msg.content))
            elif msg.role == "assistant":
                history_messages.append(("assistant", msg.content))
            elif msg.role == "system":
                history_messages.append(("system", msg.content))
        
        # Save user message
        save_message(db, session_id, "user", message, user_id=user_id)
        
        history_messages.append(("user", message))
        
        graph = get_app()
        result = graph.invoke({
            "messages": history_messages,
            "user_id": user_id,
            "extracted_args": None,
            "tool_results": [],
            "final_response": None,
        })
        
        tool_results = result.get("tool_results", [])
        
        if tool_results:
            responses = []
            for tr in tool_results:
                try:
                    data = json.loads(tr) if isinstance(tr, str) else tr
                    if isinstance(data, dict):
                        if data.get("success"):
                            responses.append(data.get("message", "Done"))
                        else:
                            responses.append(data.get("message", "Done"))
                except:
                    responses.append(str(tr))
            
            if responses:
                response_text = ". ".join(responses)
            else:
                response_text = "I've processed your request."
        else:
            messages = result.get("messages", [])
            if messages:
                last_msg = messages[-1]
                response_text = last_msg.content if hasattr(last_msg, "content") else "I'll help you with that."
            else:
                response_text = "I'll help you with that."
        
        # Save agent response
        save_message(db, session_id, "assistant", response_text, user_id=user_id)
        
        return {
            "success": True,
            "response": response_text,
            "user_id": user_id,
            "thread_id": session_id,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response": "I'm here to help! What would you like to do?",
            "user_id": user_id,
            "thread_id": session_id,
        }
    finally:
        db.close()


client = openai_client
__all__ = ["app", "client", "run_agent", "CRM_TOOLS"]