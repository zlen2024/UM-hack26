# Add CS Knowledge Agents Spec

## Why
Customer service (CS) interactions often contain valuable information such as customer preferences, close sale strategies, and context that is lost if not captured systematically. By using a Manager node to detect this useful input, we can trigger an automated multi-agent system to extract this knowledge and store it in a Knowledge Graph database for future retrieval and CRM insights.

## What Changes
- Integrate `ladybug` (or similar graph database, e.g. Kùzu) to store knowledge graph entities and relationships.
- Add an `Information Extractor Agent` that uses Dependency Syntactic Normal Forms (DSNFs) to parse text and output nodes and edges in JSON.
- Add a `Cypher Generator Agent` that takes the JSON output and generates/executes Cypher `MERGE` queries to safely insert data without duplicates.
- Implement a `Manager Node` (using LangGraph) to analyze customer inputs, detect useful information, and orchestrate the two CS agents.
- Add a FastAPI route (e.g., `/api/cs/analyze`) to accept customer service text inputs and trigger the LangGraph workflow.
- Add a FastAPI route (e.g., `/api/cs/graph`) to fetch the stored knowledge graph nodes and edges.

## Impact
- Affected specs: Backend AI services, Database (adding graph DB component alongside SQLite).
- Affected code:
  - `backend/requirements.txt` (adding `langgraph`, `langchain-openai`, `ladybug`, etc.)
  - `backend/main.py` (adding new router)
  - `backend/routes/cs_agents.py` (new module for LangGraph workflows and routes)

## ADDED Requirements
### Requirement: Knowledge Extraction
The system SHALL provide a multi-agent workflow to extract entities and relationships from customer service texts and store them in a graph database.

#### Scenario: Success case
- **WHEN** user/manager submits text containing customer preferences (e.g., "John likes Xiaomi products").
- **THEN** the Extractor Agent extracts JSON, the Cypher Agent converts it to MERGE queries, and the data is stored in the `Entity` and `RelatedTo` tables in the graph database.

## MODIFIED Requirements
None

## REMOVED Requirements
None
