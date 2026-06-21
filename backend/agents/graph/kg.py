"""Background knowledge-graph extraction for the customer-service agent.

The customer's latest message is parsed into entities/relationships (one LLM
call, grounded in Dependency Syntactic Normal Forms) and then written to the
per-user Ladybug graph **deterministically in Python** -- no second "generate
Cypher" LLM call. The graph uses a fixed schema (all nodes are ``Entity`` with a
``label`` property, all edges are ``RelatedTo`` with a ``type`` property), so
``knowledge_db.add_node`` / ``add_edge`` can persist the extracted JSON directly,
which is cheaper and cannot produce invalid queries.

Runs in a background thread so it never blocks the customer-facing reply.
"""

import json
import logging

from .llm import complete_json

logger = logging.getLogger("CS_Agent_Workflow")


def evaluate_kg_trigger(text: str) -> bool:
    """Return True if ``text`` contains customer details worth saving to the KG.

    Kept as a standalone helper; the live graph relies on the gatekeeper instead
    of calling this on the hot path.
    """
    if not text:
        return False

    prompt = f"""Analyze the following customer message and decide if it contains durable facts worth saving to a sales CRM knowledge graph.

=== WORTH SAVING ===
- Identity / role / where they work (e.g. "I run a restaurant", "I'm a reseller")
- Preferences (likes/dislikes, spicy/sweet, contact method)
- Needs / quantity / budget / timeline (e.g. "I cook for 50 people", "budget RM200")
- Relationships, goals, or business context

=== NOT WORTH SAVING ===
- Pure questions ("how much is it?"), greetings, thanks, order-status checks

Text: "{text}"
Regardless of language, output valid JSON: {{"trigger": true}} if it contains durable facts, else {{"trigger": false}}."""

    try:
        result = complete_json(messages=[{"role": "user", "content": prompt}], max_tokens=500)
        return bool(result.get("trigger", False))
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


_EXTRACTOR_PROMPT = """You are a world-class data ontology expert building a CUSTOMER knowledge graph for a sales / CRM business. Extract entities (Nodes) and relationships (Edges) from the customer's message into strict JSON. Use Dependency Syntactic Normal Forms (DSNFs) so relations come from the sentence's grammar, not guessing.

=== ANCHOR ===
The current customer is the central PERSON node. Use their name in lowercase snake_case as its id (given in the context line). If the name is unknown, use "customer_<phone>". Attach every fact the customer reveals to this customer node.

=== ONTOLOGY (node labels) ===
PERSON, ORGANIZATION, PRODUCT, PREFERENCE, LOCATION, QUANTITY, BUDGET, EVENT, CONCEPT.

=== COMMON RELATIONS (UPPER_SNAKE_CASE) ===
WORKS_AT, RUNS, OWNS, INTERESTED_IN, WANTS_TO_BUY, ORDERED, PREFERS, DISLIKES, NEEDS, HAS_BUDGET, LOCATED_IN, ASKED_ABOUT. Create new types when the grammar implies them.

=== RULES ===
1. Nodes: id = unique lowercase snake_case; label from the ontology.
2. Coreference resolution: map pronouns ("he", "it", "them", "the paste") back to the original entity id. NEVER create a new node for a pronoun.
3. Derive edges with DSNF:
   - SVO (DSNF2): Subject-Verb-Object -> (E1, PREDICATE, E2).
   - Prepositional (DSNF3/4): combine predicate + preposition -> (E1, PREDICATE_PREPOSITION, E2). e.g. "works AT a restaurant" -> WORKS_AT.
   - Coordination (DSNF5/6/7): split shared subjects/objects into separate triples. "I love the spicy and hate the sweet" -> (cust, PREFERS, spicy) and (cust, DISLIKES, sweet).
4. Extract ONLY facts explicitly stated. Do NOT infer or invent. If the message has no durable customer facts (a price question, "ok thanks", a greeting), return {"nodes": [], "edges": []}.
5. Output ONLY valid JSON with "nodes" and "edges". No prose, no markdown.

=== EXAMPLE ===
Context - Customer Name: Nel, Phone: 60123
User Message: "btw im works on restaurant... so probably i will cook for a large amount, and i love the spicy one but hate the sweet"
Output:
{
  "nodes": [
    {"id": "nel", "label": "PERSON"},
    {"id": "restaurant", "label": "ORGANIZATION"},
    {"id": "large_quantity", "label": "QUANTITY"},
    {"id": "spicy", "label": "PREFERENCE"},
    {"id": "sweet", "label": "PREFERENCE"}
  ],
  "edges": [
    {"source": "nel", "target": "restaurant", "type": "WORKS_AT"},
    {"source": "nel", "target": "large_quantity", "type": "NEEDS"},
    {"source": "nel", "target": "spicy", "type": "PREFERS"},
    {"source": "nel", "target": "sweet", "type": "DISLIKES"}
  ]
}
"""


def information_extractor_node(state: dict) -> dict:
    """Extract nodes and edges as structured JSON using DSNF rules."""
    contact_name = state.get("contact_name") or "Unknown User"
    phone = state.get("phone") or "Unknown Phone"

    user_text = _latest_user_text(state.get("messages", []))
    if not user_text:
        return {"extracted_kg_data": {"nodes": [], "edges": []}}

    text_to_extract = (
        f"Context - Customer Name: {contact_name}, Phone: {phone}\n"
        f"User Message: {user_text}"
    )

    try:
        extracted_data = complete_json(
            messages=[
                {"role": "system", "content": _EXTRACTOR_PROMPT},
                {"role": "user", "content": text_to_extract},
            ],
            temperature=0.0,
            max_tokens=2000,
        )
    except Exception as e:
        logger.error(f"[KG Extractor] Error: {e}")
        extracted_data = {"nodes": [], "edges": []}

    if not isinstance(extracted_data, dict):
        extracted_data = {"nodes": [], "edges": []}
    return {"extracted_kg_data": extracted_data}


def _norm_id(value) -> str:
    return (str(value or "")).strip().lower().replace(" ", "_")


def persist_extracted_data(state: dict) -> dict:
    """Write the extracted nodes/edges to the graph DB deterministically.

    No LLM is involved: we use the graph's parameterized add_node / add_edge,
    so writes are always schema-correct. Nodes are written before edges, and any
    edge endpoint missing from the node list is created as a stub so the edge's
    MATCH never fails.
    """
    data = state.get("extracted_kg_data") or {}
    nodes = data.get("nodes") or []
    edges = data.get("edges") or []
    if not nodes and not edges:
        return {"executed_kg_queries": []}

    # Index declared nodes, then ensure every edge endpoint has a node too.
    declared: dict[str, dict] = {}
    for n in nodes:
        nid = _norm_id(n.get("id"))
        if nid:
            declared[nid] = {"label": n.get("label") or "ENTITY", "properties": n.get("properties") or {}}
    for e in edges:
        for endpoint in (_norm_id(e.get("source")), _norm_id(e.get("target"))):
            if endpoint and endpoint not in declared:
                declared[endpoint] = {"label": "ENTITY", "properties": {}}

    from knowledge_db import KnowledgeDBFactory

    db = KnowledgeDBFactory.get_instance(state.get("user_id", "default"))

    def _props(value) -> str:
        return value if isinstance(value, str) else json.dumps(value or {})

    results = []
    # 1) Nodes first so edge MATCHes always resolve.
    for nid, node in declared.items():
        try:
            db.add_node(nid, str(node["label"]), _props(node["properties"]))
            results.append({"type": "node", "id": nid, "status": "success"})
        except Exception as e:
            logger.error(f"[KG Persist] node '{nid}' failed: {e}")
            results.append({"type": "node", "id": nid, "status": "error", "error": str(e)})

    # 2) Edges.
    for e in edges:
        source = _norm_id(e.get("source"))
        target = _norm_id(e.get("target"))
        rel = (str(e.get("type") or "RELATED_TO")).strip().upper().replace(" ", "_")
        if not source or not target:
            continue
        try:
            db.add_edge(source, target, rel, _props(e.get("properties")))
            results.append({"type": "edge", "source": source, "rel": rel, "target": target, "status": "success"})
        except Exception as ex:
            logger.error(f"[KG Persist] edge {source}-{rel}->{target} failed: {ex}")
            results.append({"type": "edge", "source": source, "rel": rel, "target": target, "status": "error", "error": str(ex)})

    n_nodes = sum(1 for r in results if r["type"] == "node" and r["status"] == "success")
    n_edges = sum(1 for r in results if r["type"] == "edge" and r["status"] == "success")
    logger.info(f"[KG Persist] wrote {n_nodes} node(s) and {n_edges} edge(s)")
    return {"executed_kg_queries": results}


# Backwards-compatible name (the old pipeline called this "cypher_generator_node").
cypher_generator_node = persist_extracted_data


def run_kg_extraction_in_background(state: dict) -> None:
    """Extract facts and persist them to the graph (intended for a worker thread)."""
    logger.info("--- [BACKGROUND] Running KG Extraction ---")
    try:
        state.update(information_extractor_node(state))
        persist_extracted_data(state)
        logger.info("[Background] KG Extraction complete")
    except Exception as e:
        logger.error(f"[Background] Error in KG Extraction: {e}", exc_info=True)
