from typing import TypedDict, List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END

# 1. State definition
class AgentState(TypedDict):
    user_input: str
    gatekeeper_response: dict
    manager_response: dict
    current_tasks: List[str]
    worker_error: str

# 2. Pydantic Models for structured output
class GatekeeperOutput(BaseModel):
    response: str = Field(description="Direct response to the user, if applicable")
    agent_loop: bool = Field(description="Whether to route to the manager/agent loop")
    query: str = Field(description="The user's core query or intent")

class ManagerOutput(BaseModel):
    task: List[str] = Field(description="List of tasks for the worker to execute")
    response: str = Field(description="Response to the user, if task execution is not needed")
    knowledge: bool = Field(description="Whether this is a pure knowledge query requiring no action")

# 3. LLM initialization
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# 4. Nodes

def gatekeeper_node(state: AgentState) -> dict:
    """
    Evaluates the user input.
    Routes simple greetings/out-of-scope queries to END.
    Routes actionable/complex queries to the manager.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a highly efficient Customer Service Intent Router for a business. Your ONLY job is to analyze the user's input, determine if it requires complex backend processing, and route it accordingly.\n\nRULES:\n1. You MUST respond in strictly valid JSON format matching the schema.\n2. If the user's input is a simple greeting, general chit-chat, or easily answerable without looking up systems, set \"agent_loop\" to false and provide a direct \"response\".\n3. If the user's input requires checking orders, retrieving business data, troubleshooting, or anything complex, set \"agent_loop\" to true, leave \"response\" blank (\" \"), and extract the core intent into \"query\"."),
        ("user", "{user_input}")
    ])
    chain = prompt | llm.with_structured_output(GatekeeperOutput)
    result = chain.invoke({"user_input": state["user_input"]})
    return {"gatekeeper_response": result.dict()}

def manager_node(state: AgentState) -> dict:
    """
    Plans tasks for the worker based on the query and any previous worker errors.
    If no action is needed or a final response is ready, it responds directly.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the Master Workflow Planner for a customer service business. You receive queries or system errors and must determine the exact sequence of tasks needed to resolve them.\n\nRULES:\n1. Output MUST be strictly valid JSON matching the schema.\n2. If the query requires checking company policy, FAQs, or general information, set \"knowledge\" to true, and \"task\" MUST be empty [].\n3. If the query requires executing actions, list the specific tools/steps in the \"task\" array. \"knowledge\" MUST be false. Available tasks: [\"verify_order\", \"check_payment_status\"].\n4. If you lack information from the user to proceed, OR if you receive an error from a previous task, set \"task\" to [], \"knowledge\" to false, and use \"response\" to ask the user for clarification or inform them of the issue."),
        ("user", "Query: {query}\nPrevious Tasks: {current_tasks}\nWorker Error: {worker_error}")
    ])
    chain = prompt | llm.with_structured_output(ManagerOutput)
    
    # Get query from gatekeeper if available, else user input
    gatekeeper_resp = state.get("gatekeeper_response", {})
    query = gatekeeper_resp.get("query", state.get("user_input", ""))
    worker_error = state.get("worker_error", "")
    current_tasks = state.get("current_tasks", [])
    
    result = chain.invoke({
        "query": query, 
        "current_tasks": current_tasks,
        "worker_error": worker_error
    })
    
    return {
        "manager_response": result.dict(),
        "current_tasks": result.task,
        "worker_error": ""
    }

def worker_node(state: AgentState) -> dict:
    """
    Executes tasks using mock tools.
    Captures errors if a task fails to route back to the manager.
    """
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
            # Simulate routing to mock tools based on keywords
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

# 5. Routing edges
def gatekeeper_router(state: AgentState) -> str:
    """
    Route to END if agent_loop == False, else route to manager.
    """
    agent_loop = state.get("gatekeeper_response", {}).get("agent_loop", False)
    if not agent_loop:
        return END
    return "manager"

def manager_router(state: AgentState) -> str:
    """
    Route to END if response != "" or knowledge == True, else route to worker.
    """
    response = state.get("manager_response", {}).get("response", "")
    knowledge = state.get("manager_response", {}).get("knowledge", False)
    
    if response != "" or knowledge:
        return END
    return "worker"

# 6. Graph Compilation
builder = StateGraph(AgentState)

# Add nodes
builder.add_node("gatekeeper", gatekeeper_node)
builder.add_node("manager", manager_node)
builder.add_node("worker", worker_node)

# Add edges
builder.add_edge(START, "gatekeeper")
builder.add_conditional_edges("gatekeeper", gatekeeper_router)
builder.add_conditional_edges("manager", manager_router)
builder.add_edge("worker", "manager") # Fallback loop: pass error back to manager

# Compile the graph
graph = builder.compile()
