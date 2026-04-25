import json
import os
import operator
from typing import TypedDict, Annotated, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from database import get_graph_conn

router = APIRouter()

# Setup OpenRouter ChatOpenAI
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "sk-dummy")
llm = ChatOpenAI(
    model="openrouter/elephant-alpha",
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# 3.1 State Schema
class AgentState(TypedDict):
    input_text: str
    is_useful: bool
    extracted_json: Dict[str, Any]
    cypher_queries: List[str]
    execution_logs: Annotated[List[str], operator.add]

# Prompts
MANAGER_PROMPT = """
You are a Customer Service Manager. Your job is to analyze customer service interaction text and determine if it contains valuable customer information that should be stored in a CRM Knowledge Graph.
Valuable information includes:
- Customer preferences (e.g., likes, dislikes)
- Purchase intent or close sale strategies
- Complaints or specific product feedback
- Relationships between entities (e.g., John works for Acme Corp, Sarah bought Product X)

Return ONLY a JSON object with a single boolean field "is_useful": true or false.
Do not output anything else.
"""

EXTRACTOR_PROMPT = """
You are a World-Class Data Ontology Expert and Knowledge Graph Architect. Your primary task is to analyze user text and extract information into entities (Nodes) and relationships (Edges) in strict JSON format. You must utilize Dependency Syntactic Normal Forms (DSNFs) to accurately derive relation triples from complex syntax.
**INSTRUCTIONS AND STRICT CONSTRAINTS:**
1. **Entity Extraction (Nodes):** Identify primary subjects and objects. Each entity must have an id (unique lowercase name, snake_case) and a label (e.g., PERSON, DEVICE, CONCEPT, LOCATION).
2. **Coreference Resolution:** If the text uses pronouns (e.g., "he", "it", "the device", "this system") referring to previously mentioned entities, you MUST map them back to the original entity's id. DO NOT create new entities for pronouns.
3. **Dependency-Based Relation Extraction (Edges):** Extract relationships based on structural dependencies. The relationship type MUST be in UPPER_SNAKE_CASE. Follow these DSNF rules:
  * **Basic SVO (DSNF2):** Identify Subject-Verb-Object (SBV, VOB) dependencies to form (Entity1, PREDICATE, Entity2).
  * **Prepositional Modifiers (DSNF3/DSNF4):** When prepositions act as adverbials or complements (POB, ADV, CMP), combine the predicate and preposition to form the relation, e.g., (Entity1, PREDICATE_PREPOSITION, Entity2).
  * **Coordination (DSNF5/DSNF6/DSNF7):** When coordinate verbs or objects share subjects/objects (COO), unpack them into distinct triples. e.g., "X controls Y and Z" becomes (X, CONTROLS, Y) and (X, CONTROLS, Z).
4. **Output Structure:** ONLY output valid JSON. No conversational text, no markdown explanations outside the JSON block.
**EXAMPLE 1: Coordination and Complex Chains (DSNF5/6/7 Application)**
*Input:* "The Maya System is an AI-based smart home ecosystem that automatically controls the lights, air conditioning, and smart door locks. It is specifically designed to help Malaysian homeowners manage their daily energy consumption."
*Output:*
{
  "nodes": [
    {"id": "maya_system", "label": "TECHNOLOGY"},
    {"id": "smart_home_ecosystem", "label": "CONCEPT"},
    {"id": "lights", "label": "DEVICE"},
    {"id": "air_conditioning", "label": "DEVICE"},
    {"id": "smart_door_locks", "label": "DEVICE"},
    {"id": "malaysian_homeowners", "label": "PERSON"},
    {"id": "energy_consumption", "label": "CONCEPT"}
  ],
  "edges": [
    {"source": "maya_system", "target": "smart_home_ecosystem", "type": "IS_A"},
    {"source": "maya_system", "target": "lights", "type": "CONTROLS"},
    {"source": "maya_system", "target": "air_conditioning", "type": "CONTROLS"},
    {"source": "maya_system", "target": "smart_door_locks", "type": "CONTROLS"},
    {"source": "maya_system", "target": "malaysian_homeowners", "type": "DESIGNED_TO_HELP"},
    {"source": "malaysian_homeowners", "target": "energy_consumption", "type": "MANAGE"}
  ]
}
**EXAMPLE 2: Coreference Resolution & Prepositional Dependencies (DSNF3/4 Application)**
*Input:* "John bought a Xiaomi temperature sensor yesterday. John installed the sensor in the living room. Suddenly, he saw that the device disconnected from the WiFi, so he immediately restarted it."
*Output:*
{
  "nodes": [
    {"id": "john", "label": "PERSON"},
    {"id": "xiaomi_temperature_sensor", "label": "DEVICE"},
    {"id": "living_room", "label": "LOCATION"},
    {"id": "wifi", "label": "TECHNOLOGY"}
  ],
  "edges": [
    {"source": "john", "target": "xiaomi_temperature_sensor", "type": "BOUGHT"},
    {"source": "john", "target": "xiaomi_temperature_sensor", "type": "INSTALLED"},
    {"source": "xiaomi_temperature_sensor", "target": "living_room", "type": "INSTALLED_IN"},
    {"source": "xiaomi_temperature_sensor", "target": "wifi", "type": "DISCONNECTED_FROM"},
    {"source": "john", "target": "xiaomi_temperature_sensor", "type": "RESTARTED"}
  ]
}
"""

CYPHER_PROMPT = """
You are an Expert Neo4j Database Administrator. Your task is to receive JSON format data (nodes and edges) and convert it into ready-to-execute Cypher query language.
**STRICT INSTRUCTIONS AND CONSTRAINTS:**
1. **Anti-Duplication Rule:** You MUST use MERGE for every Node and Edge. DO NOT use CREATE. This prevents database duplication.
2. **MERGE Syntax:**
  * MERGE (n:Entity {id: 'id_value', label: 'LABEL_VALUE'}) for Nodes. Kuzu requires node MERGE to match primary key (id). Set label as a property or inline. Actually, our table is: Entity (id STRING PRIMARY KEY, label STRING, properties STRING) and RelatedTo (FROM Entity TO Entity, relationship_type STRING, properties STRING).
  * Example node MERGE:
    MERGE (n:Entity {id: 'id_value'}) ON MATCH SET n.label='LABEL_VALUE', n.properties='{}' ON CREATE SET n.label='LABEL_VALUE', n.properties='{}'
  * MERGE (a)-[r:RelatedTo {relationship_type: 'TYPE'}]->(b) for Edges, but only after ensuring (a) and (b) have been explicitly MATCHED.
  * Example edge MERGE:
    MATCH (a:Entity {id: 'source_id'}), (b:Entity {id: 'target_id'}) MERGE (a)-[r:RelatedTo {relationship_type: 'TYPE'}]->(b) ON MATCH SET r.properties='{}' ON CREATE SET r.properties='{}'
3. **Clean Output:** ONLY provide the Cypher code as a JSON array of strings. No markdown wrapping, no introductory or concluding text. Example: ["MERGE ...", "MATCH ... MERGE ..."]
"""

# 3.2 Manager Node
def manager_node(state: AgentState):
    messages = [
        SystemMessage(content=MANAGER_PROMPT),
        HumanMessage(content=state["input_text"])
    ]
    try:
        response = llm.invoke(messages)
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
        result = json.loads(content)
        is_useful = result.get("is_useful", False)
        logs = [f"Manager evaluated is_useful={is_useful}"]
    except Exception as e:
        is_useful = False
        logs = [f"Manager failed to evaluate: {e}"]
    
    return {
        "is_useful": is_useful,
        "execution_logs": logs
    }

# 3.3 Extractor Node
def extractor_node(state: AgentState):
    messages = [
        SystemMessage(content=EXTRACTOR_PROMPT),
        HumanMessage(content=state["input_text"])
    ]
    logs = []
    try:
        response = llm.invoke(messages)
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
        extracted_json = json.loads(content)
        logs.append("Extractor successfully generated JSON")
    except Exception as e:
        extracted_json = {"nodes": [], "edges": []}
        logs.append(f"Extractor failed to parse JSON: {e}")
        
    return {
        "extracted_json": extracted_json,
        "execution_logs": logs
    }

# 3.4 Cypher Generator Node
def cypher_generator_node(state: AgentState):
    json_str = json.dumps(state.get("extracted_json", {}), indent=2)
    messages = [
        SystemMessage(content=CYPHER_PROMPT),
        HumanMessage(content=json_str)
    ]
    logs = []
    try:
        response = llm.invoke(messages)
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
        cypher_queries = json.loads(content)
        if not isinstance(cypher_queries, list):
            cypher_queries = []
    except Exception as e:
        cypher_queries = []
        logs.append(f"Cypher Generator failed to parse JSON: {e}")
    
    # Execute queries
    conn = get_graph_conn()
    executed = 0
    for query in cypher_queries:
        try:
            conn.execute(query)
            executed += 1
        except Exception as e:
            logs.append(f"Failed to execute query '{query}': {e}")
            
    logs.append(f"Cypher Generator executed {executed}/{len(cypher_queries)} queries")
    
    return {
        "cypher_queries": cypher_queries,
        "execution_logs": logs
    }

# 3.5 Build Graph
def router_logic(state: AgentState):
    if state.get("is_useful", False):
        return "extractor"
    return END

workflow = StateGraph(AgentState)
workflow.add_node("manager", manager_node)
workflow.add_node("extractor", extractor_node)
workflow.add_node("cypher", cypher_generator_node)

workflow.set_entry_point("manager")
workflow.add_conditional_edges("manager", router_logic, {"extractor": "extractor", END: END})
workflow.add_edge("extractor", "cypher")
workflow.add_edge("cypher", END)

app_graph = workflow.compile()

# 4.1 FastAPI Routes
class AnalyzeRequest(BaseModel):
    text: str

@router.post("/analyze")
async def analyze_cs_text(req: AnalyzeRequest):
    initial_state = {
        "input_text": req.text,
        "is_useful": False,
        "extracted_json": {},
        "cypher_queries": [],
        "execution_logs": []
    }
    final_state = app_graph.invoke(initial_state)
    return {
        "is_useful": final_state.get("is_useful"),
        "extracted_json": final_state.get("extracted_json"),
        "cypher_queries": final_state.get("cypher_queries"),
        "execution_logs": final_state.get("execution_logs")
    }

@router.get("/graph")
async def get_cs_graph():
    conn = get_graph_conn()
    nodes = []
    edges = []
    
    try:
        # Fetch nodes
        res = conn.execute("MATCH (n:Entity) RETURN n.id, n.label, n.properties")
        while res.has_next():
            row = res.get_next()
            nodes.append({
                "id": row[0],
                "label": row[1],
                "properties": json.loads(row[2]) if row[2] else {}
            })
            
        # Fetch edges
        res = conn.execute("MATCH (a:Entity)-[r:RelatedTo]->(b:Entity) RETURN a.id, b.id, r.relationship_type, r.properties")
        while res.has_next():
            row = res.get_next()
            edges.append({
                "from": row[0],
                "to": row[1],
                "relationship_type": row[2],
                "properties": json.loads(row[3]) if row[3] else {}
            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    return {"nodes": nodes, "edges": edges}
