# Plan to Implement Active Knowledge Graph Querying

## Summary
The user asked: *"do we had an agent that will do query knowledge graph rn..?..we need to actively qerying knowledge graph to improve connection and context with customer..do you think we need it to be parse directly after get new message"*

Based on the logs and the current architecture in `backend/agents/cs_agent.py`:
- We do **not** have an agent that actively queries the Knowledge Graph before formulating a response.
- The `manager_node` currently only has access to general CRM tools (create contact, opportunity, etc.) via `CRM_TOOLS`.
- The Knowledge Graph tools (like `query_knowledge_graph` inside `backend/agents/graph/tools.py`) exist but are only exposed to the generic `/api/chat` router (in `backend/routes/kg.py`), not to the primary WhatsApp/Telegram chat flows (`cs_agent.py`).
- When the user asks "what belantik do..?", the Manager agent times out or fails to answer effectively because it lacks the specific context from the Knowledge Graph.

To fix this, we should **inject the Knowledge Graph context directly into the Manager node** before it decides how to respond. Instead of relying on the LLM to randomly guess when to use a "query" tool, it is much faster and more reliable to do a **semantic or direct Cypher search** on the Knowledge Graph based on the user's input, and inject those findings directly into the `Manager`'s prompt (similar to how we injected `business_context`).

## Current State Analysis
- The user's input triggers the `gatekeeper_node` which decides to loop to the `manager_node`.
- The `manager_node` receives the `user_id`, `contact_name`, `business_context`, and `business_rules`, but **no Knowledge Graph data**.
- We have a `KnowledgeDBFactory` in `backend/knowledge_db.py` that can access the user's graph database.

## Proposed Changes

### 1. Enhance `knowledge_db.py` for Context Retrieval
- Add a new method `get_relevant_context(self, text: str)` to the `KnowledgeDB` class.
- This method will use a simple, fast approach to find relevant nodes/edges:
  - Extract potential keywords from the `text` (e.g., using a simple regex or splitting by words, ignoring stop words).
  - Run a Cypher query like `MATCH (n:Entity) WHERE n.id CONTAINS 'keyword' OR n.label CONTAINS 'keyword' RETURN n.id, n.label, n.properties LIMIT 5`.
  - Also fetch related edges: `MATCH (a:Entity)-[r:RelatedTo]->(b:Entity) WHERE a.id CONTAINS 'keyword' RETURN a.id, type(r), b.id LIMIT 5`.
  - Format this into a readable string (e.g., "Known Fact: X is RELATED_TO Y").

### 2. Inject KG Context into `manager_node`
- In `backend/agents/cs_agent.py`, right before executing the `manager_node` LLM call:
  - Retrieve the user's Knowledge Graph instance via `KnowledgeDBFactory.get_instance(user_id)`.
  - Call `get_relevant_context(user_input)`.
  - Append the resulting text as `=== CUSTOMER KNOWLEDGE GRAPH ===` to the `system_prompt`.

## Assumptions & Decisions
- Injecting relevant KG data directly into the prompt is much more efficient than forcing the Manager LLM to figure out how to write and execute a Cypher query tool mid-conversation.
- We will use simple keyword matching in Cypher for now to ensure speed and reliability. If advanced vector search is needed later, it can be added to `get_relevant_context`.

## Verification Steps
- Ask a question related to an entity stored in the Knowledge Graph (e.g., "what belantik do?").
- Verify in the logs that `Manager Input Context` includes the extracted Knowledge Graph facts.
- Verify the AI responds correctly using that knowledge.