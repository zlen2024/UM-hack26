import os
import json
import logging
import re
from typing import Dict, Any, Optional, TypedDict, List, Callable
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

GATEKEEPER_SCHEMA = {
    "type": "object",
    "properties": {
        "response": {"type": "string"},
        "agent_loop": {"type": "boolean"},
        "query": {"type": "string"}
    },
    "required": ["response", "agent_loop", "query"],
    "additionalProperties": False
}

class AgentState(TypedDict, total=False):
    user_input: str
    user_id: int
    contact_name: str
    gatekeeper_response: dict
    messages: List[dict]
    worker_error: str
    extracted_kg_data: dict
    executed_kg_queries: list
    trigger_kg: bool

def format_tool_to_openai(tool) -> dict:
    if hasattr(tool, "args_schema") and tool.args_schema:
        if hasattr(tool.args_schema, "model_json_schema"):
            parameters = tool.args_schema.model_json_schema()
        else:
            parameters = tool.args_schema.schema()
    else:
        parameters = {"type": "object", "properties": {}}
        
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": parameters
        }
    }

openai_tools = [format_tool_to_openai(t) for t in CRM_TOOLS]

def gatekeeper_node(state: AgentState) -> dict:
    logger.info("--- [NODE: GATEKEEPER] Executing ---")
    user_input = state.get('user_input', '')
    logger.info(f"Input State User Input: '{user_input}'")
    
    # Fast-path for simple greetings to avoid slow LLM calls
    lower_input = re.sub(r'[^a-z\s]', '', user_input.lower()).strip()
    greetings = {"hi", "hello", "hey", "hye", "hye again", "greetings", "good morning", "good afternoon", "good evening", "thanks", "thank you", "ok", "okay"}
    
    if lower_input in greetings or len(lower_input) < 2:
        logger.info("[Gatekeeper] Fast-path triggered for simple greeting.")
        contact_name = state.get('contact_name', '').strip()
        greeting_name = f" {contact_name}" if contact_name else ""
        return {
            "gatekeeper_response": {
                "response": f"Hello{greeting_name}! How can I help you today?",
                "agent_loop": False,
                "query": ""
            }
        }
    
    client = get_ilmu_client()
    system_prompt = f"""You are an Intent Router and Context Detector for a customer service business.
Your job is to analyze the user's input and determine if it should be routed to the main agent loop.
Business User ID: {state.get('user_id')}
Customer Name: {state.get('contact_name')}

=== STRICT RULES ===
1. You MUST respond in strictly valid JSON format matching the schema: {{"response": "string", "agent_loop": boolean, "query": "string"}}.
2. SET `agent_loop` = false ONLY IF the input is a brief, simple greeting (e.g., "hi", "thanks") with NO other actionable information. Provide a direct "response".
3. SET `agent_loop` = true IF the input contains ANY of the following:
   - Requests requiring system checks, tool usage, or complex answers.
   - Personal details, preferences (e.g., likes/dislikes), or facts (e.g., "my name is...", "I love...").
   - Business strategies, goals, or context that should be remembered.
4. When `agent_loop` is true:
   - For complex tasks, provide a polite preliminary "response" (e.g., "Let me check that for you...").
   - For users sharing information/preferences, leave "response" empty ("") so the main agent can reply naturally.
   - Extract the core intent or shared facts into the "query" field.

=== FEW-SHOT EXAMPLES ===
Input: "hello.. my name is Daniel... and i love ayam... but i hate sotong.."
Output: {{"response": "", "agent_loop": true, "query": "User states their name is Daniel, they love ayam, and hate sotong."}}

Input: "thanks for the help"
Output: {{"response": "You're welcome! Let me know if you need anything else.", "agent_loop": false, "query": ""}}

Input: "can you check my order status?"
Output: {{"response": "Let me check that for you right away...", "agent_loop": true, "query": "check order status"}}"""

    try:
        messages_for_gatekeeper = [{"role": "system", "content": system_prompt}]
        for m in state.get("messages", []):
            messages_for_gatekeeper.append(m)
        messages_for_gatekeeper.append({"role": "user", "content": state.get("user_input", "")})

        response = client.chat.completions.create(
            model="ilmu-glm-5.1",
            messages=messages_for_gatekeeper,
            temperature=0,
            max_tokens=2000,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "gatekeeper_response",
                    "strict": True,
                    "schema": GATEKEEPER_SCHEMA
                }
            }
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

    # Append the current query to the conversation history so the manager has the full context
    query_to_add = result.get('query') or user_input
    new_messages = state.get("messages", []) + [{"role": "user", "content": query_to_add}]

    return {"gatekeeper_response": result, "messages": new_messages}

def evaluate_kg_trigger(text: str) -> bool:
    """Evaluate if the text contains important customer details (preferences, strategies, etc.)."""
    if not text:
        return False
    
    prompt = f"""Analyze the following text and determine if it contains important customer details that should be extracted into a Knowledge Graph.

=== IMPORTANT DETAILS INCLUDE ===
- Personal preferences (e.g., likes, dislikes, favorite foods, favorite colors)
- Identity facts (e.g., names, roles, relationships)
- Business strategies, goals, or objectives
- Significant personal or business facts (e.g., "I am the CEO", "We use AWS")

=== EXAMPLES ===
Text: "hello.. my name is Daniel... and i love ayam... but i hate sotong.."
Response: YES

Text: "can you check my order status?"
Response: NO

Text: "I prefer to be contacted via email."
Response: YES

Text: "thanks for your help"
Response: NO

=== TASK ===
Text: "{text}"
Respond with ONLY 'YES' or 'NO'."""

    try:
        client = get_ilmu_client()
        response = client.chat.completions.create(
            model="ilmu-glm-5.1", # Fast model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=10,
        )
        content = response.choices[0].message.content.strip().upper()
        return "YES" in content
    except Exception as e:
        logger.error(f"[KG Evaluator] Error: {e}")
        return False

def manager_node(state: AgentState) -> dict:
    logger.info("--- [NODE: MANAGER] Executing ---")
    client = get_ilmu_client()
    
    system_prompt = f"""You are the Master Workflow Planner and Conversational Agent for a customer service business.
Business User ID: {state.get('user_id')}
Customer Name: {state.get('contact_name')}

=== ROLE & OBJECTIVE ===
You handle user queries, execute necessary backend tasks using tools, and maintain a polite, helpful conversation.

=== TOOL USAGE RULES ===
1. **Contact Management**: Use `list_contacts` FIRST to find if a customer exists before creating a new profile. Use `update_contact` to modify email, phone, or add notes.
2. **Support Tasks**: Use `create_task` to assign follow-up actions to the team.
3. **Interaction Logging**: Use `create_activity` to log the support interaction after resolving requests.

=== CONVERSATION RULES ===
1. If the user shares personal details, preferences (likes/dislikes), or business strategies, acknowledge them politely and naturally in your response. (Note: A background Knowledge Graph agent will automatically extract and save this data, so you do NOT need to use any tools to save this specific knowledge).
2. If the query requires checking policy or general info, respond directly.
3. If the query requires actions, use the tools. Once successful, provide a final summary to the user.
4. Always maintain a helpful and professional tone."""

    messages = state.get("messages", [])
    if not messages:
        gatekeeper_resp = state.get("gatekeeper_response", {})
        query = gatekeeper_resp.get("query", state.get("user_input", ""))
        messages = [{"role": "user", "content": query}]

    api_messages = [{"role": "system", "content": system_prompt}] + messages
    logger.info(f"Manager Input Context -> Query: '{messages[0].get('content')}', Prev Messages: {len(messages)}")

    try:
        response = client.chat.completions.create(
            model="ilmu-glm-5.1",
            messages=api_messages,
            tools=openai_tools,
            temperature=0,
            max_tokens=2000,
        )
        msg = response.choices[0].message
        
        msg_dict = {"role": "assistant"}
        if msg.content is not None:
            msg_dict["content"] = msg.content
        if msg.tool_calls:
            msg_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in msg.tool_calls
            ]
        
        logger.info(f"[Manager] Output Tool Calls: {len(msg_dict.get('tool_calls', []))}")
        
        # If the manager is done (no tool calls), we evaluate if we need to extract knowledge
        trigger_kg = False
        if not msg_dict.get("tool_calls"):
            user_msg = next((m for m in reversed(messages) if m.get("role") == "user"), None)
            if user_msg:
                trigger_kg = evaluate_kg_trigger(user_msg.get("content", ""))
                logger.info(f"[Manager] Evaluated KG trigger: {trigger_kg}")
        
        return {
            "messages": messages + [msg_dict],
            "worker_error": "",
            "trigger_kg": trigger_kg
        }
    except Exception as e:
        logger.error(f"[Manager] Error: {e}", exc_info=True)
        fallback = {"role": "assistant", "content": "I'm sorry, I'm having trouble planning the tasks to resolve your query."}
        return {
            "messages": messages + [fallback],
            "worker_error": str(e),
            "trigger_kg": False
        }

def worker_node(state: AgentState) -> dict:
    logger.info("--- [NODE: WORKER] Executing ---")
    messages = state.get("messages", [])
    if not messages:
        return {}
        
    last_message = messages[-1]
    tool_calls = last_message.get("tool_calls", [])
    logger.info(f"Worker received {len(tool_calls)} tool calls to execute.")
    
    error = ""
    tool_map = {t.name: t for t in CRM_TOOLS}
    new_messages = []
    
    for tc in tool_calls:
        try:
            tool_name = tc["function"]["name"]
            tool_args_str = tc["function"]["arguments"]
            tool_args = json.loads(tool_args_str) if tool_args_str else {}
            logger.info(f"Worker executing tool: '{tool_name}' with args: {tool_args}")
            
            if "user_id" not in tool_args and state.get("user_id"):
                tool_args["user_id"] = state.get("user_id")
                
            if tool_name not in tool_map:
                raise ValueError(f"Tool '{tool_name}' not found.")
            
            tool = tool_map[tool_name]
            result = tool.invoke(tool_args)
            logger.debug(f"Tool '{tool_name}' returned: {result}")
            
            new_messages.append({
                "tool_call_id": tc["id"],
                "role": "tool",
                "name": tool_name,
                "content": str(result)
            })
            
        except Exception as e:
            error = str(e)
            logger.error(f"Worker failed on tool call '{tc.get('function', {}).get('name', 'Unknown')}': {error}", exc_info=True)
            new_messages.append({
                "tool_call_id": tc["id"],
                "role": "tool",
                "name": tc.get("function", {}).get("name", "unknown"),
                "content": f"Error: {error}"
            })
            
    logger.info(f"Worker execution finished. Errors: '{error}', Results Count: {len(new_messages)}")
    return {"messages": messages + new_messages, "worker_error": error}

def gatekeeper_router(state: AgentState) -> str:
    agent_loop = state.get("gatekeeper_response", {}).get("agent_loop", False)
    if not agent_loop:
        logger.info("[ROUTER] Gatekeeper -> END (No agent loop required)")
        return END
    logger.info("[ROUTER] Gatekeeper -> Manager (Agent loop triggered)")
    return "manager"

def manager_router(state: AgentState) -> str:
    messages = state.get("messages", [])
    if not messages:
        return END
        
    last_message = messages[-1]
    if last_message.get("tool_calls"):
        logger.info("[ROUTER] Manager -> Worker (Tasks need execution)")
        return "worker"
        
    if state.get("trigger_kg"):
        logger.info("[ROUTER] Manager -> Information Extractor (KG Triggered)")
        return "information_extractor"
        
    logger.info("[ROUTER] Manager -> END (Final response ready)")
    return END

from agents.kg_nodes import information_extractor_node, cypher_generator_node

builder = StateGraph(AgentState)
builder.add_node("gatekeeper", gatekeeper_node)
builder.add_node("manager", manager_node)
builder.add_node("worker", worker_node)
builder.add_node("information_extractor", information_extractor_node)
builder.add_node("cypher_generator", cypher_generator_node)

builder.add_edge(START, "gatekeeper")
builder.add_conditional_edges("gatekeeper", gatekeeper_router)
builder.add_conditional_edges("manager", manager_router)
builder.add_edge("worker", "manager")
builder.add_edge("information_extractor", "cypher_generator")
builder.add_edge("cypher_generator", END)

graph = builder.compile()


# --- Main Process Functions ---

def process_whatsapp_message(message_data: Dict[str, Any], send_callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
    """Process WhatsApp message and return AI response using LangGraph workflow.

    Args:
        message_data: Structured payload with:
            - user_id: int
            - contact_name: str
            - phone: str
            - message: str
        send_callback: Optional callback function to send intermediate messages back to the user.

    Returns:
        AI response from Ilmu AI model
    """
    user_id = message_data.get("user_id")
    contact_name = message_data.get("contact_name", "")
    phone = message_data.get("phone", "")
    message = message_data.get("message", "")

    try:
        from database import SessionLocal
        from agents.memory import save_message, get_history
        
        session_id = f"wa_{phone}"
        db = SessionLocal()
        
        try:
            # Save user message
            save_message(db, session_id, "user", message, user_id=user_id)
            
            # Load history (up to 20 messages for context)
            db_history = get_history(db, session_id, limit=20, user_id=user_id)
            
            # Format history for the agent
            history_messages = []
            for msg in db_history[:-1]:  # Exclude the current message we just saved
                if msg.role in ["user", "assistant", "system"]:
                    history_messages.append({"role": msg.role, "content": msg.content})
            
            initial_state = {
                "user_input": message,
                "user_id": user_id,
                "contact_name": contact_name,
                "messages": history_messages
            }
            
            # Execute the graph and capture intermediate outputs via stream()
            current_state = initial_state.copy()
            for event in graph.stream(initial_state):
                for node_name, node_state in event.items():
                    current_state.update(node_state)
                    
                    # If Gatekeeper just finished and it decided to loop, send the preliminary response!
                    if node_name == "gatekeeper":
                        gatekeeper_resp = node_state.get("gatekeeper_response", {})
                        if gatekeeper_resp.get("agent_loop", False):
                            preliminary_msg = gatekeeper_resp.get("response", "")
                            if preliminary_msg and send_callback:
                                logger.info(f"[WhatsApp] Sending preliminary response: {preliminary_msg}")
                                send_callback(preliminary_msg)
            
            final_state = current_state

            gatekeeper_resp = final_state.get("gatekeeper_response", {})
            if not gatekeeper_resp.get("agent_loop", False):
                ai_response = gatekeeper_resp.get("response", "")
            else:
                messages = final_state.get("messages", [])
                if messages:
                    last_message = messages[-1]
                    ai_response = last_message.get("content", "")
                else:
                    ai_response = "I'm sorry, I'm having trouble processing your request right now."
            
            # Save assistant response
            if ai_response:
                save_message(db, session_id, "assistant", ai_response, user_id=user_id)
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"[WhatsApp] Error calling LangGraph: {e}", exc_info=True)
        ai_response = "I'm sorry, I'm having trouble processing your request right now."

    return {
        "response": ai_response,
        "user_id": user_id,
        "contact_name": contact_name,
        "phone": phone,
    }

def process_telegram_message(message_data: Dict[str, Any], send_callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
    """Process Telegram message and return AI response using LangGraph workflow.

    Args:
        message_data: Structured payload with:
            - user_id: int
            - contact_name: str
            - chat_id: str
            - message: str
        send_callback: Optional callback function to send intermediate messages back to the user.

    Returns:
        AI response from Ilmu AI model
    """
    user_id = message_data.get("user_id")
    contact_name = message_data.get("contact_name", "")
    chat_id = message_data.get("chat_id", "")
    message = message_data.get("message", "")

    try:
        from database import SessionLocal
        from agents.memory import save_message, get_history
        
        session_id = f"tg_{chat_id}"
        db = SessionLocal()
        
        try:
            # Save user message
            save_message(db, session_id, "user", message, user_id=user_id)
            
            # Load history (up to 20 messages for context)
            db_history = get_history(db, session_id, limit=20, user_id=user_id)
            
            history_messages = []
            for msg in db_history[:-1]:  # Exclude the current message we just saved
                if msg.role in ["user", "assistant", "system"]:
                    history_messages.append({"role": msg.role, "content": msg.content})
            
            initial_state = {
                "user_input": message,
                "user_id": user_id,
                "contact_name": contact_name,
                "messages": history_messages
            }
            
            # Execute the graph and capture intermediate outputs via stream()
            current_state = initial_state.copy()
            for event in graph.stream(initial_state):
                for node_name, node_state in event.items():
                    current_state.update(node_state)
                    
                    if node_name == "gatekeeper":
                        gatekeeper_resp = node_state.get("gatekeeper_response", {})
                        if gatekeeper_resp.get("agent_loop", False):
                            preliminary_msg = gatekeeper_resp.get("response", "")
                            if preliminary_msg and send_callback:
                                logger.info(f"[Telegram] Sending preliminary response: {preliminary_msg}")
                                send_callback(preliminary_msg)
            
            final_state = current_state

            gatekeeper_resp = final_state.get("gatekeeper_response", {})
            if not gatekeeper_resp.get("agent_loop", False):
                ai_response = gatekeeper_resp.get("response", "")
            else:
                messages = final_state.get("messages", [])
                if messages:
                    last_message = messages[-1]
                    ai_response = last_message.get("content", "")
                else:
                    ai_response = "I'm sorry, I'm having trouble processing your request right now."
            
            # Save assistant response
            if ai_response:
                save_message(db, session_id, "assistant", ai_response, user_id=user_id)
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"[Telegram] Error calling LangGraph: {e}", exc_info=True)
        ai_response = "I'm sorry, I'm having trouble processing your request right now."

    return {
        "response": ai_response,
        "user_id": user_id,
        "contact_name": contact_name,
        "chat_id": chat_id,
    }
