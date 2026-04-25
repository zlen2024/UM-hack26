import json
import os
from knowledge_db import knowledge_db

def _get_openai_client():
    from openai import OpenAI
    return OpenAI(
        base_url=os.getenv("OPENAI_API_BASE", "https://stg-api.ilmu.ai/v1"),
        api_key=os.getenv("OPENAI_API_KEY", "demo-key"),
    )

def information_extractor_node(state: dict) -> dict:
    """Extract nodes and edges as structured JSON using DSNF rules."""
    messages = state.get("messages", [])
    
    # We only care about the latest user message
    user_msg = next((m for m in reversed(messages) if isinstance(m, dict) and m.get("role") == "user" or getattr(m, "type", getattr(m, "role", "")) in ["human", "user"]), None)
    text_to_extract = ""
    if user_msg:
        text_to_extract = user_msg.get("content") if isinstance(user_msg, dict) else getattr(user_msg, "content", "")
    
    prompt = """You are an Information Extraction Agent. 
Extract entities and relationships from the user's text using strict DSNF (Dependency Syntactic Normal Forms) rules.
Return a structured JSON object with two lists: 'nodes' and 'edges'.

A 'node' should have:
- id: A unique string identifier (e.g., "customer_john_doe", "product_x")
- label: The type of entity (e.g., "Person", "Organization", "Preference", "Product")
- properties: A dictionary of key-value pairs (e.g., {"name": "John Doe"})

An 'edge' should have:
- source: The id of the source node
- target: The id of the target node
- type: The relationship type (e.g., "LIKES", "WORKS_AT", "INTERESTED_IN")
- properties: A dictionary of key-value pairs (e.g., {"since": "2023"})

IMPORTANT: Output ONLY valid JSON, with no markdown formatting or other text.
"""
    
    try:
        response = _get_openai_client().chat.completions.create(
            model=os.getenv("OPENAI_MODEL_NAME", "ilmu-mini-1.0"),
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text_to_extract}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        extracted_data = json.loads(content)
    except Exception as e:
        print(f"Extraction error: {e}")
        extracted_data = {"nodes": [], "edges": []}
        
    return {"extracted_kg_data": extracted_data}


def cypher_generator_node(state: dict) -> dict:
    """Convert structured JSON from the extractor into valid Cypher MERGE queries and execute them."""
    extracted_data = state.get("extracted_kg_data", {"nodes": [], "edges": []})
    
    if not extracted_data.get("nodes") and not extracted_data.get("edges"):
        return {"executed_kg_queries": []}
        
    prompt = """You are a Cypher Generator Agent.
Given a JSON object containing nodes and edges, generate a list of valid Cypher MERGE statements to insert them into a graph database.

IMPORTANT DATABASE SCHEMA:
- All nodes MUST use the `Entity` table/label. They have properties: `id` (STRING), `label` (STRING), and `properties` (STRING).
- All relationships MUST use the `RelatedTo` table/type. They have properties: `type` (STRING) and `properties` (STRING).

Example output format for a JSON object containing nodes and edges:
{
  "queries": [
    "MERGE (e:Entity {id: 'john'}) ON CREATE SET e.label='Person', e.properties='{\\"name\\": \\"John Doe\\"}' ON MATCH SET e.label='Person', e.properties='{\\"name\\": \\"John Doe\\"}'",
    "MERGE (e:Entity {id: 'prod1'}) ON CREATE SET e.label='Product', e.properties='{\\"name\\": \\"Product 1\\"}'",
    "MATCH (a:Entity {id: 'john'}), (b:Entity {id: 'prod1'}) MERGE (a)-[r:RelatedTo]->(b) ON CREATE SET r.type='LIKES', r.properties='{}' ON MATCH SET r.type='LIKES', r.properties='{}'"
  ]
}

Ensure all inner JSON quotes in `properties` are properly escaped.
Output ONLY valid JSON containing the "queries" list, with no markdown formatting.
"""

    try:
        response = _get_openai_client().chat.completions.create(
            model=os.getenv("OPENAI_MODEL_NAME", "ilmu-mini-1.0"),
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(extracted_data)}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        query_data = json.loads(content)
        queries = query_data.get("queries", [])
    except Exception as e:
        print(f"Cypher generation error: {e}")
        queries = []
        
    # Execute the queries
    executed_queries = []
    for query in queries:
        try:
            knowledge_db.execute_cypher(query)
            executed_queries.append({"query": query, "status": "success"})
        except Exception as e:
            print(f"Cypher execution error: {e} for query: {query}")
            executed_queries.append({"query": query, "status": "error", "error": str(e)})
            
    return {"executed_kg_queries": executed_queries}
