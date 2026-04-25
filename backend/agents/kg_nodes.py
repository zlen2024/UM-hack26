import json
import os
from knowledge_db import KnowledgeDBFactory

def _get_openai_client():
    from .cs_agent import get_ilmu_client
    return get_ilmu_client()

def information_extractor_node(state: dict) -> dict:
    """Extract nodes and edges as structured JSON using DSNF rules."""
    messages = state.get("messages", [])
    
    # We only care about the latest user message
    user_msg = next((m for m in reversed(messages) if isinstance(m, dict) and m.get("role") == "user" or getattr(m, "type", getattr(m, "role", "")) in ["human", "user"]), None)
    text_to_extract = ""
    if user_msg:
        text_to_extract = user_msg.get("content") if isinstance(user_msg, dict) else getattr(user_msg, "content", "")
    
    prompt = """You are a World-Class Data Ontology Expert and Knowledge Graph Architect. Your primary task is to analyze user text and extract information into entities (Nodes) and relationships (Edges) in strict JSON format. You must utilize Dependency Syntactic Normal Forms (DSNFs) to accurately derive relation triples from complex syntax.

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
    
    try:
        response = _get_openai_client().chat.completions.create(
            model=os.getenv("OPENAI_MODEL_NAME", "ilmu-glm-5.1"),
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text_to_extract}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        from .cs_agent import parse_llm_json
        extracted_data = parse_llm_json(content)
    except Exception as e:
        print(f"Extraction error: {e}")
        extracted_data = {"nodes": [], "edges": []}
        
    return {"extracted_kg_data": extracted_data}


def cypher_generator_node(state: dict) -> dict:
    """Convert structured JSON from the extractor into valid Cypher MERGE queries and execute them."""
    extracted_data = state.get("extracted_kg_data", {"nodes": [], "edges": []})
    
    if not extracted_data.get("nodes") and not extracted_data.get("edges"):
        return {"executed_kg_queries": []}
        
    prompt = """You are an Expert Neo4j Database Administrator. Your task is to receive JSON format data (nodes and edges) and convert it into ready-to-execute Cypher query language.
**STRICT INSTRUCTIONS AND CONSTRAINTS:**
 1. **Anti-Duplication Rule:** You MUST use MERGE for every Node and Edge. DO NOT use CREATE. This prevents database duplication.
 2. **MERGE Syntax:**
   * MERGE (n:Entity {id: 'id_value'}) for Nodes. We strictly use `Entity` as the table name for nodes.
   * MERGE (a)-[:RelatedTo {type: 'RELATIONSHIP_TYPE'}]->(b) for Edges. We strictly use `RelatedTo` as the table name for edges.
   * Only create edges after ensuring (a) and (b) have been explicitly MATCHED or MERGED beforehand and carried over using the WITH clause.
 3. **Clean Output:** ONLY provide valid JSON containing a "queries" array. No markdown wrapping outside the JSON block.

**DATABASE SCHEMA:**
- All nodes MUST use the `Entity` table/label. They have properties: `id` (STRING), `label` (STRING), and `properties` (STRING).
- All relationships MUST use the `RelatedTo` table/type. They have properties: `type` (STRING) and `properties` (STRING).

**EXAMPLE 1: Processing Coordination Chains (Multiple Edges from 1 Node)**
*Input JSON:*
{"nodes": [{"id": "maya_system", "label": "Technology"}, {"id": "lights", "label": "Device"}, {"id": "homeowner", "label": "Person"}], "edges": [{"source": "maya_system", "target": "lights", "type": "CONTROLS"}, {"source": "maya_system", "target": "homeowner", "type": "HELPS"}]}
*Output:*
{
  "queries": [
    "MERGE (n1:Entity {id: 'maya_system'}) ON CREATE SET n1.label='Technology', n1.properties='{}'",
    "MERGE (n2:Entity {id: 'lights'}) ON CREATE SET n2.label='Device', n2.properties='{}'",
    "MERGE (n3:Entity {id: 'homeowner'}) ON CREATE SET n3.label='Person', n3.properties='{}'",
    "MATCH (n1:Entity {id: 'maya_system'}), (n2:Entity {id: 'lights'}), (n3:Entity {id: 'homeowner'}) MERGE (n1)-[r1:RelatedTo]->(n2) ON CREATE SET r1.type='CONTROLS', r1.properties='{}' MERGE (n1)-[r2:RelatedTo]->(n3) ON CREATE SET r2.type='HELPS', r2.properties='{}'"
  ]
}

**EXAMPLE 2: Processing Reused Entities (Multiple relationships between the same nodes)**
*Input JSON:*
{"nodes": [{"id": "john", "label": "Person"}, {"id": "sensor", "label": "Device"}], "edges": [{"source": "john", "target": "sensor", "type": "BOUGHT"}, {"source": "john", "target": "sensor", "type": "INSTALLED"}, {"source": "john", "target": "sensor", "type": "RESTARTED"}]}
*Output:*
{
  "queries": [
    "MERGE (n1:Entity {id: 'john'}) ON CREATE SET n1.label='Person', n1.properties='{}'",
    "MERGE (n2:Entity {id: 'sensor'}) ON CREATE SET n2.label='Device', n2.properties='{}'",
    "MATCH (n1:Entity {id: 'john'}), (n2:Entity {id: 'sensor'}) MERGE (n1)-[r1:RelatedTo]->(n2) ON CREATE SET r1.type='BOUGHT', r1.properties='{}' MERGE (n1)-[r2:RelatedTo]->(n2) ON CREATE SET r2.type='INSTALLED', r2.properties='{}' MERGE (n1)-[r3:RelatedTo]->(n2) ON CREATE SET r3.type='RESTARTED', r3.properties='{}'"
  ]
}
"""

    try:
        response = _get_openai_client().chat.completions.create(
            model=os.getenv("OPENAI_MODEL_NAME", "ilmu-glm-5.1"),
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(extracted_data)}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        from .cs_agent import parse_llm_json
        query_data = parse_llm_json(content)
        queries = query_data.get("queries", [])
    except Exception as e:
        print(f"Cypher generation error: {e}")
        queries = []
        
    user_id = state.get("user_id", "default")
    user_db = KnowledgeDBFactory.get_instance(user_id)
    
    # Execute the queries
    executed_queries = []
    for query in queries:
        try:
            user_db.execute_cypher(query)
            executed_queries.append({"query": query, "status": "success"})
        except Exception as e:
            print(f"Cypher execution error: {e} for query: {query}")
            executed_queries.append({"query": query, "status": "error", "error": str(e)})
            
    return {"executed_kg_queries": executed_queries}
