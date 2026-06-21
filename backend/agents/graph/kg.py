"""Background knowledge-graph extraction for the customer-service agent.

The user's latest message is turned into entities/relationships and persisted to
the per-user Ladybug graph database. This runs in a background thread so it never
blocks the customer-facing reply.
"""

import json
import logging
import os

from .llm import CHAT_MODEL, get_chat_client, parse_llm_json

logger = logging.getLogger("CS_Agent_Workflow")

_EXTRACT_MODEL = os.getenv("KG_MODEL_NAME", CHAT_MODEL)


def evaluate_kg_trigger(text: str) -> bool:
    """Return True if ``text`` contains customer details worth saving to the KG.

    Kept as a standalone helper; the live graph relies on the gatekeeper's
    ``contains_knowledge`` flag instead of calling this on the hot path.
    """
    if not text:
        return False

    prompt = f"""Analyze the following text and determine if it contains important customer details that should be extracted into a Knowledge Graph.

=== IMPORTANT DETAILS INCLUDE ===
- Personal preferences (e.g. likes, dislikes, favorite foods/colors)
- Identity facts (e.g. names, roles, relationships)
- Business strategies, goals, or objectives
- Significant personal or business facts (e.g. "I am the CEO", "We use AWS")

=== EXAMPLES ===
Text: "hello.. my name is Daniel... and i love ayam... but i hate sotong.."
Response: YES
Text: "can you check my order status?"
Response: NO

=== TASK ===
Text: "{text}"
Regardless of the language, output valid JSON with a single boolean field "trigger".
Output {{"trigger": true}} if the text contains important customer details, else {{"trigger": false}}."""

    try:
        client = get_chat_client()
        response = client.chat.completions.create(
            model=_EXTRACT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=2000,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        if not content:
            return False
        return bool(parse_llm_json(content).get("trigger", False))
    except Exception as e:
        logger.error(f"[KG Evaluator] Error: {e}")
        return False


def _latest_user_text(messages: list) -> str:
    """Pull the most recent user message content out of the message list."""
    for m in reversed(messages or []):
        role = m.get("role") if isinstance(m, dict) else getattr(m, "role", getattr(m, "type", ""))
        if role in ("user", "human"):
            return m.get("content") if isinstance(m, dict) else getattr(m, "content", "")
    return ""


def information_extractor_node(state: dict) -> dict:
    """Extract nodes and edges as structured JSON using DSNF rules."""
    contact_name = state.get("contact_name", "Unknown User")
    phone = state.get("phone", "Unknown Phone")

    user_text = _latest_user_text(state.get("messages", []))
    text_to_extract = ""
    if user_text:
        text_to_extract = (
            f"Context - Customer Name: {contact_name}, Phone: {phone}\n"
            f"User Message: {user_text}"
        )

    prompt = """You are a World-Class Data Ontology Expert and Knowledge Graph Architect. Your task is to analyze user text and extract information into entities (Nodes) and relationships (Edges) in strict JSON format. Utilize Dependency Syntactic Normal Forms (DSNFs) to derive relation triples from complex syntax.

**INSTRUCTIONS AND STRICT CONSTRAINTS:**
 1. **Entity Extraction (Nodes):** Identify primary subjects and objects. Each entity has an id (unique lowercase snake_case name) and a label (e.g. PERSON, DEVICE, CONCEPT, LOCATION).
 2. **Coreference Resolution:** Map pronouns ("he", "it", "the device") back to the original entity's id. DO NOT create new entities for pronouns.
 3. **Dependency-Based Relation Extraction (Edges):** Relationship type MUST be UPPER_SNAKE_CASE.
   * **Basic SVO (DSNF2):** Subject-Verb-Object -> (Entity1, PREDICATE, Entity2).
   * **Prepositional Modifiers (DSNF3/4):** Combine predicate + preposition -> (Entity1, PREDICATE_PREPOSITION, Entity2).
   * **Coordination (DSNF5/6/7):** Unpack shared subjects/objects into distinct triples. "X controls Y and Z" -> (X, CONTROLS, Y) and (X, CONTROLS, Z).
 4. **Output Structure:** ONLY output valid JSON. No prose, no markdown outside the JSON.

**EXAMPLE**
Input: "John bought a Xiaomi temperature sensor yesterday. He installed it in the living room."
Output:
{
  "nodes": [
    {"id": "john", "label": "PERSON"},
    {"id": "xiaomi_temperature_sensor", "label": "DEVICE"},
    {"id": "living_room", "label": "LOCATION"}
  ],
  "edges": [
    {"source": "john", "target": "xiaomi_temperature_sensor", "type": "BOUGHT"},
    {"source": "xiaomi_temperature_sensor", "target": "living_room", "type": "INSTALLED_IN"}
  ]
}
"""

    try:
        response = get_chat_client().chat.completions.create(
            model=_EXTRACT_MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text_to_extract},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        extracted_data = parse_llm_json(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"[KG Extractor] Error: {e}")
        extracted_data = {"nodes": [], "edges": []}

    return {"extracted_kg_data": extracted_data}


def cypher_generator_node(state: dict) -> dict:
    """Convert extracted JSON into Cypher MERGE queries and execute them."""
    extracted_data = state.get("extracted_kg_data", {"nodes": [], "edges": []})

    if not extracted_data.get("nodes") and not extracted_data.get("edges"):
        return {"executed_kg_queries": []}

    prompt = """You are an Expert Graph Database Administrator. Convert JSON (nodes and edges) into ready-to-execute Cypher.
**STRICT CONSTRAINTS:**
 1. Use MERGE for every Node and Edge (never CREATE) to prevent duplication.
 2. Syntax:
   * MERGE (n:Entity {id: 'id_value'}) for Nodes. Always use `Entity` as the node table.
   * MERGE (a)-[:RelatedTo {type: 'RELATIONSHIP_TYPE'}]->(b) for Edges. Always use `RelatedTo` as the edge table.
   * Only create edges after (a) and (b) are MATCHED/MERGED and carried with WITH.
 3. ONLY output valid JSON containing a "queries" array. No markdown outside the JSON.

**SCHEMA:** Nodes use the `Entity` table with properties id (STRING), label (STRING), properties (STRING). Relationships use `RelatedTo` with properties type (STRING) and properties (STRING).

**EXAMPLE**
Input JSON: {"nodes": [{"id": "john", "label": "Person"}, {"id": "sensor", "label": "Device"}], "edges": [{"source": "john", "target": "sensor", "type": "BOUGHT"}]}
Output:
{
  "queries": [
    "MERGE (n1:Entity {id: 'john'}) ON CREATE SET n1.label='Person', n1.properties='{}'",
    "MERGE (n2:Entity {id: 'sensor'}) ON CREATE SET n2.label='Device', n2.properties='{}'",
    "MATCH (n1:Entity {id: 'john'}), (n2:Entity {id: 'sensor'}) MERGE (n1)-[r1:RelatedTo]->(n2) ON CREATE SET r1.type='BOUGHT', r1.properties='{}'"
  ]
}
"""

    try:
        response = get_chat_client().chat.completions.create(
            model=_EXTRACT_MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(extracted_data)},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        queries = parse_llm_json(response.choices[0].message.content).get("queries", [])
    except Exception as e:
        logger.error(f"[KG Cypher] Generation error: {e}")
        queries = []

    from knowledge_db import KnowledgeDBFactory

    user_db = KnowledgeDBFactory.get_instance(state.get("user_id", "default"))

    executed_queries = []
    for query in queries:
        try:
            user_db.execute_cypher(query)
            executed_queries.append({"query": query, "status": "success"})
        except Exception as e:
            logger.error(f"[KG Cypher] Execution error: {e} for query: {query}")
            executed_queries.append({"query": query, "status": "error", "error": str(e)})

    return {"executed_kg_queries": executed_queries}


def run_kg_extraction_in_background(state: dict) -> None:
    """Run extraction + persistence end-to-end (intended for a worker thread)."""
    logger.info("--- [BACKGROUND] Running KG Extraction ---")
    try:
        state.update(information_extractor_node(state))
        cypher_generator_node(state)
        logger.info("[Background] KG Extraction complete")
    except Exception as e:
        logger.error(f"[Background] Error in KG Extraction: {e}", exc_info=True)
