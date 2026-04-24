import os
import json
import logging
import re
from typing import Dict, Any, Optional, TypedDict, List
from openai import OpenAI
from langgraph.graph import StateGraph, START, END
from .graph.tools import CRM_TOOLS

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("CS_Agent_Workflow")

def parse_llm_json(content: str) -> dict:
    if not content:
        raise ValueError("LLM returned empty content")
    
    content = content.strip()
    
    # Extract from markdown block if present
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
    if match:
        content = match.group(1)
        
    # Fallback to finding the first { and last }
    start_idx = content.find('{')
    end_idx = content.rfind('}')
    if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
        content = content[start_idx:end_idx+1]
        
    return json.loads(content)

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
    current_tasks: List[dict]
    worker_error: str
    task_results: List[str]

def gatekeeper_node(state: AgentState) -> dict:
    logger.info("--- [NODE: GATEKEEPER] Executing ---")
    logger.info(f"Input State User Input: '{state.get('user_input', '')}'")
    
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
        logger.debug(f"[Gatekeeper] Raw LLM Output: {content}")
        result = parse_llm_json(content)
        logger.info(f"[Gatekeeper] Parsed Result: agent_loop={result.get('agent_loop')}, query='{result.get('query')}'")
    except Exception as e:
        logger.error(f"[Gatekeeper] Error: {e}", exc_info=True)
        # Fallback to direct response if API fails or parsing fails
        result = {
            "response": "I'm sorry, I'm having trouble processing your request right now.",
            "agent_loop": False,
            "query": ""
        }

    return {"gatekeeper_response": result}

def manager_node(state: AgentState) -> dict:
    logger.info("--- [NODE: MANAGER] Executing ---")
    client = get_ilmu_client()
    
    tools_description = "\n".join([f"- {t.name}: {t.description}" for t in CRM_TOOLS])
    
    system_prompt = f"""You are the Master Workflow Planner for a customer service business. You receive queries or system errors and must determine the exact sequence of tasks needed to resolve them. The ID of the business user is {state.get('user_id')}. The customer's name is {state.get('contact_name')}.

RULES:
1. Output MUST be strictly valid JSON matching the schema: {{"task": [{{"name": "string", "args": {{}}}}], "response": "string", "knowledge": boolean}}.
2. If the query requires checking company policy, FAQs, or general information, set "knowledge" to true, and "task" MUST be empty [].
3. If the query requires executing actions, list the specific tools/steps in the "task" array. "knowledge" MUST be false. Available tasks:
{tools_description}
4. If you lack information from the user to proceed, OR if you receive an error from a previous task, set "task" to [], "knowledge" to false, and use "response" to ask the user for clarification or inform them of the issue.
5. If previous tasks were successful (check Task Results), provide the final "response" summarizing the outcome to the user and set "task" to [] and "knowledge" to false."""

    gatekeeper_resp = state.get("gatekeeper_response", {})
    query = gatekeeper_resp.get("query", state.get("user_input", ""))
    worker_error = state.get("worker_error", "")
    current_tasks = state.get("current_tasks", [])
    task_results = state.get("task_results", [])

    user_content = f"Query: {query}\nPrevious Tasks: {current_tasks}\nTask Results: {task_results}\nWorker Error: {worker_error}"
    logger.info(f"Manager Input Context -> Query: '{query}', Prev Tasks: {len(current_tasks)}, Has Error: {bool(worker_error)}")

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
        logger.debug(f"[Manager] Raw LLM Output: {content}")
        result = parse_llm_json(content)
        tasks_planned = result.get("task", [])
        logger.info(f"[Manager] Parsed Result: knowledge={result.get('knowledge')}, tasks planned={len(tasks_planned)}")
    except Exception as e:
        logger.error(f"[Manager] Error: {e}", exc_info=True)
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
    logger.info("--- [NODE: WORKER] Executing ---")
    tasks = state.get("current_tasks", [])
    logger.info(f"Worker received {len(tasks)} tasks to execute.")
    error = ""
    task_results = []
    
    tool_map = {t.name: t for t in CRM_TOOLS}
    
    for task in tasks:
        try:
            if not isinstance(task, dict):
                raise ValueError(f"Task format invalid, expected dict but got {type(task)}")
            
            tool_name = task.get("name")
            tool_args = task.get("args", {})
            logger.info(f"Worker executing tool: '{tool_name}' with args: {tool_args}")
            
            if "user_id" not in tool_args and state.get("user_id"):
                tool_args["user_id"] = state.get("user_id")
                
            if tool_name not in tool_map:
                raise ValueError(f"Tool '{tool_name}' not found.")
            
            tool = tool_map[tool_name]
            result = tool.invoke(tool_args)
            logger.debug(f"Tool '{tool_name}' returned: {result}")
            
            if isinstance(result, str):
                try:
                    res_dict = json.loads(result)
                    if not res_dict.get("success", True):
                        raise ValueError(f"Tool {tool_name} failed: {res_dict.get('error', 'Unknown error')} - {res_dict.get('message', '')}")
                    task_results.append(f"Tool {tool_name} success: {result}")
                except json.JSONDecodeError:
                    task_results.append(f"Tool {tool_name} output: {result}")
            else:
                task_results.append(f"Tool {tool_name} output: {result}")
            
        except Exception as e:
            error = str(e)
            logger.error(f"Worker failed on task '{task.get('name', 'Unknown')}': {error}", exc_info=True)
            break # Break loop on first failure
            
    logger.info(f"Worker execution finished. Errors: '{error}', Results Count: {len(task_results)}")
    return {"worker_error": error, "task_results": task_results}

def gatekeeper_router(state: AgentState) -> str:
    agent_loop = state.get("gatekeeper_response", {}).get("agent_loop", False)
    if not agent_loop:
        logger.info("[ROUTER] Gatekeeper -> END (No agent loop required)")
        return END
    logger.info("[ROUTER] Gatekeeper -> Manager (Agent loop triggered)")
    return "manager"

def manager_router(state: AgentState) -> str:
    response = state.get("manager_response", {}).get("response", "")
    knowledge = state.get("manager_response", {}).get("knowledge", False)
    if response != "" or knowledge:
        logger.info("[ROUTER] Manager -> END (Final response ready or knowledge query)")
        return END
    logger.info("[ROUTER] Manager -> Worker (Tasks need execution)")
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
