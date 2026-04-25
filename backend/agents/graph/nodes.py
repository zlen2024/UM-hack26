import json
from typing import Literal
from .state import AgentState
from .tools import CRM_TOOLS


SYSTEM_PROMPT = """You are a helpful CRM customer service agent for a sales team. 

You have access to the following tools to help customers:
- create_contact, get_contact, list_contacts, update_contact: Manage customer contacts
- create_opportunity, get_opportunity, list_opportunities, update_opportunity_stage: Manage sales deals
- create_task, get_task, list_tasks, update_task_status: Manage follow-up tasks
- create_activity, list_activities: Log customer interactions
- get_dashboard: View sales metrics

When a customer asks about contacts, deals, tasks, or activities, use the appropriate tools to help them.
Be concise and helpful in your responses. Always confirm when you've completed an action.

If you need to create a contact, ask for their name at minimum. For opportunities, ask for title and value.
For tasks, ask for the task title and what needs to be done."""


def classify_and_respond(state: AgentState) -> dict:
    """LLM node that decides to use tools or respond."""
    from openai import OpenAI
    import os
    
    client = OpenAI(
        base_url="https://stg-api.ilmu.ai/v1",
        api_key=os.getenv("OPENAI_API_KEY", "demo-key"),
    )
    
    messages = state.get("messages", [])
    
    # Build messages for API
    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in messages:
        role = "user" if msg.type == "human" else "assistant"
        content = msg.content if hasattr(msg, "content") else str(msg)
        api_messages.append({"role": role, "content": content})
    
    # Get tool definitions
    tool_defs = []
    for t in CRM_TOOLS:
        tool_defs.append({
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.args_schema.schema() if hasattr(t, "args_schema") else {"type": "object", "properties": {}}
            }
        })
    
    try:
        response = client.chat.completions.create(
            model="ilmu-mini-1.0",
            messages=api_messages,
            tools=tool_defs if tool_defs else None,
            temperature=0.7,
            max_tokens=1000,
        )
        
        choice = response.choices[0]
        message = choice.message
        
        # Check if tool calls
        if message.tool_calls:
            return {
                "messages": [message],
                "extracted_args": {},
                "tool_results": [],
            }
        else:
            # Just respond
            return {
                "messages": [message],
                "extracted_args": None,
                "tool_results": [],
                "final_response": message.content or "I'll help you with that. What would you like to do?",
            }
    except Exception as e:
        # Fallback response
        from langchain_core.messages import AIMessage
        return {
            "messages": [AIMessage(content=f"I'm here to help with your CRM. What would you like to do?")],
            "extracted_args": None,
            "tool_results": [],
            "final_response": "I'm here to help with your CRM. What would you like to do?",
        }


def execute_tools(state: AgentState) -> dict:
    """Execute tools called by the LLM."""
    from langgraph.prebuilt import ToolNode
    
    tool_node = ToolNode(CRM_TOOLS)
    
    messages = state.get("messages", [])
    last_message = messages[-1]
    
    results = []
    response_text = ""
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tc in last_message.tool_calls:
            tool_name = tc.name
            tool_args = tc.arguments if isinstance(tc.arguments, dict) else {}
            
            try:
                result = tool_node.invoke(tool_args)
                results.append(str(result))
            except Exception as e:
                results.append(json.dumps({"error": str(e)}))
    
    return {
        "tool_results": results,
        "extracted_args": {},
    }


def format_response(state: AgentState) -> dict:
    """Format the final response from tool results."""
    tool_results = state.get("tool_results", [])
    
    if tool_results:
        # Parse tool results and format a response
        all_results = []
        for tr in tool_results:
            try:
                data = json.loads(tr) if isinstance(tr, str) else tr
                if isinstance(data, dict):
                    if data.get("success"):
                        all_results.append(data.get("message", "Done"))
                    else:
                        all_results.append(data.get("message", "Error"))
            except:
                all_results.append(str(tr))
        
        if all_results:
            response = ". ".join(all_results)
        else:
            response = "Done"
    else:
        # No tools called, use the last message
        messages = state.get("messages", [])
        if messages:
            last_msg = messages[-1]
            response = last_msg.content if hasattr(last_msg, "content") else "How can I help you?"
        else:
            response = "How can I help you?"
    
    return {"final_response": response}