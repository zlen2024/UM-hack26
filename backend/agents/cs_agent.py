import os
import json
from typing import Dict, Any, Optional, TypedDict, List
from openai import OpenAI
from langgraph.graph import StateGraph, START, END

def get_ilmu_client():
    api_key = os.getenv("ILMU_API_KEY", "")
    return OpenAI(
        base_url="https://api.ilmu.ai/v1",
        api_key=api_key,
    )

# --- LangGraph Setup ---

class AgentState(TypedDict, total=False):
    user_input: str
    user_id: int
    contact_name: str
    gatekeeper_response: dict
    manager_response: dict
    current_tasks: List[str]
    worker_error: str

def gatekeeper_node(state: AgentState) -> dict:
    client = get_ilmu_client()
    system_prompt = f"""You are a highly efficient Customer Service Intent Router for a business. Your ONLY job is to analyze the user's input, determine if it requires complex backend processing, and route it accordingly. The ID of the business user is {state.get('user_id')}. The customer's name is {state.get('contact_name')}.

RULES:
1. You MUST respond in strictly valid JSON format matching the schema: {{"response": "string", "agent_loop": boolean, "query": "string"}}.
2. If the user's input is a simple greeting, general chit-chat, or easily answerable without looking up systems, set "agent_loop" to false and provide a direct "response".
3. If the user's input requires checking orders, retrieving business data, troubleshooting, or anything complex, set "agent_loop" to true, leave "response" blank (""), and extract the core intent into "query"."""

    try:
        response = client.chat.completions.create(
            model="ilmu-glm-5.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": state.get("user_input", "")},
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        result = json.loads(content)
    except Exception as e:
        print(f"[Gatekeeper] Error: {e}")
        # Fallback to direct response if API fails or parsing fails
        result = {
            "response": "I'm sorry, I'm having trouble processing your request right now.",
            "agent_loop": False,
            "query": ""
        }

    return {"gatekeeper_response": result}

def manager_node(state: AgentState) -> dict:
    client = get_ilmu_client()
    system_prompt = f"""You are the Master Workflow Planner for a customer service business. You receive queries or system errors and must determine the exact sequence of tasks needed to resolve them. The ID of the business user is {state.get('user_id')}. The customer's name is {state.get('contact_name')}.

RULES:
1. Output MUST be strictly valid JSON matching the schema: {{"task": ["string"], "response": "string", "knowledge": boolean}}.
2. If the query requires checking company policy, FAQs, or general information, set "knowledge" to true, and "task" MUST be empty [].
3. If the query requires executing actions, list the specific tools/steps in the "task" array. "knowledge" MUST be false. Available tasks: ["verify_order", "check_payment_status"].
4. If you lack information from the user to proceed, OR if you receive an error from a previous task, set "task" to [], "knowledge" to false, and use "response" to ask the user for clarification or inform them of the issue."""

    gatekeeper_resp = state.get("gatekeeper_response", {})
    query = gatekeeper_resp.get("query", state.get("user_input", ""))
    worker_error = state.get("worker_error", "")
    current_tasks = state.get("current_tasks", [])

    user_content = f"Query: {query}\nPrevious Tasks: {current_tasks}\nWorker Error: {worker_error}"

    try:
        response = client.chat.completions.create(
            model="ilmu-glm-5.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        result = json.loads(content)
    except Exception as e:
        print(f"[Manager] Error: {e}")
        # Fallback response
        result = {
            "task": [],
            "response": "I'm sorry, I'm having trouble planning the tasks to resolve your query.",
            "knowledge": False
        }

    return {
        "manager_response": result,
        "current_tasks": result.get("task", []),
        "worker_error": ""
    }

def worker_node(state: AgentState) -> dict:
    tasks = state.get("current_tasks", [])
    error = ""
    
    # Mock Tools
    def verify_order(task: str) -> str:
        if "fail" in task.lower():
            raise ValueError("Order verification failed.")
        return "Order verified successfully."
        
    def check_payment_status(task: str) -> str:
        if "error" in task.lower():
            raise ValueError("Payment system is currently down.")
        return "Payment cleared."
        
    for task in tasks:
        try:
            if "order" in task.lower():
                verify_order(task)
            elif "payment" in task.lower():
                check_payment_status(task)
            else:
                # Mock generic success for unknown tasks
                pass
        except Exception as e:
            error = str(e)
            break # Break loop on first failure
            
    return {"worker_error": error}

def gatekeeper_router(state: AgentState) -> str:
    agent_loop = state.get("gatekeeper_response", {}).get("agent_loop", False)
    if not agent_loop:
        return END
    return "manager"

def manager_router(state: AgentState) -> str:
    response = state.get("manager_response", {}).get("response", "")
    knowledge = state.get("manager_response", {}).get("knowledge", False)
    if response != "" or knowledge:
        return END
    return "worker"

builder = StateGraph(AgentState)
builder.add_node("gatekeeper", gatekeeper_node)
builder.add_node("manager", manager_node)
builder.add_node("worker", worker_node)

builder.add_edge(START, "gatekeeper")
builder.add_conditional_edges("gatekeeper", gatekeeper_router)
builder.add_conditional_edges("manager", manager_router)
builder.add_edge("worker", "manager")

graph = builder.compile()


# --- Main Process Functions ---

def process_whatsapp_message(message_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process WhatsApp message and return AI response using LangGraph workflow.

    Args:
        message_data: Structured payload with:
            - user_id: int
            - contact_name: str
            - phone: str
            - message: str

    Returns:
        AI response from Ilmu AI model
    """
    user_id = message_data.get("user_id")
    contact_name = message_data.get("contact_name", "")
    phone = message_data.get("phone", "")
    message = message_data.get("message", "")

    try:
        initial_state = {
            "user_input": message,
            "user_id": user_id,
            "contact_name": contact_name
        }
        
        final_state = graph.invoke(initial_state)
        
        gatekeeper_resp = final_state.get("gatekeeper_response", {})
        if not gatekeeper_resp.get("agent_loop", False):
            ai_response = gatekeeper_resp.get("response", "")
        else:
            manager_resp = final_state.get("manager_response", {})
            ai_response = manager_resp.get("response", "")
            
    except Exception as e:
        print(f"[WhatsApp] Error calling LangGraph: {e}")
        ai_response = "I'm sorry, I'm having trouble processing your request right now."

    return {
        "response": ai_response,
        "user_id": user_id,
        "contact_name": contact_name,
        "phone": phone,
    }

def process_telegram_message(message_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process Telegram message and return AI response using LangGraph workflow.

    Args:
        message_data: Structured payload with:
            - user_id: int
            - contact_name: str
            - chat_id: str
            - message: str

    Returns:
        AI response from Ilmu AI model
    """
    user_id = message_data.get("user_id")
    contact_name = message_data.get("contact_name", "")
    chat_id = message_data.get("chat_id", "")
    message = message_data.get("message", "")

    try:
        initial_state = {
            "user_input": message,
            "user_id": user_id,
            "contact_name": contact_name
        }
        
        final_state = graph.invoke(initial_state)
        
        gatekeeper_resp = final_state.get("gatekeeper_response", {})
        if not gatekeeper_resp.get("agent_loop", False):
            ai_response = gatekeeper_resp.get("response", "")
        else:
            manager_resp = final_state.get("manager_response", {})
            ai_response = manager_resp.get("response", "")
            
    except Exception as e:
        print(f"[Telegram] Error calling LangGraph: {e}")
        ai_response = "I'm sorry, I'm having trouble processing your request right now."

    return {
        "response": ai_response,
        "user_id": user_id,
        "contact_name": contact_name,
        "chat_id": chat_id,
    }
