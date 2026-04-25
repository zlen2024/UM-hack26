# Add Knowledge Graph Agents Spec

## Why
The customer service (CS) system needs to extract structured information (like customer preferences, sales strategies, or key facts) from customer interactions to build a persistent knowledge graph. This enables the system to maintain long-term context and improve personalized responses. 

## What Changes
- Add an **Information Extractor Agent** node to parse user text into entities and relationships using Dependency Syntactic Normal Forms (DSNFs).
- Add a **Cypher Generator Agent** node to convert the extracted JSON data into valid Cypher queries (using `MERGE` statements).
- Integrate a Graph Database (e.g., LadybugDB or Neo4j) to store the extracted nodes and edges safely.
- Update the **Manager Node** in the LangGraph workflow to detect useful customer input and route it to the knowledge graph extraction pipeline.
- Implement FastAPI endpoints (`/api/chat`, `/api/graph`) to handle the knowledge extraction flow and visualize the graph.

## Impact
- Affected specs: Agent workflow (LangGraph topology), Context Management.
- Affected code: Manager/Router node logic, graph database module, API routes, LLM prompt templates.

## ADDED Requirements
### Requirement: Information Extractor Agent
The system SHALL extract entities and relationships from customer interactions using strict DSNF rules, returning structured JSON.
#### Scenario: Success case
- **WHEN** the manager node identifies a useful customer input and routes to the extractor
- **THEN** the Information Extractor Agent processes it and outputs structured JSON (nodes and edges) without duplication.

### Requirement: Cypher Generator Agent
The system SHALL convert structured JSON from the extractor into valid Cypher queries and execute them against the graph database.
#### Scenario: Success case
- **WHEN** the Cypher Generator Agent receives valid JSON nodes and edges
- **THEN** it generates Cypher `MERGE` statements and executes them, storing the entities and relationships safely in the database.

## MODIFIED Requirements
### Requirement: Manager Node Routing
The manager node SHALL evaluate customer input and trigger the knowledge graph pipeline when appropriate.
#### Scenario: Important Context Detected
- **WHEN** the customer shares preferences or a closing sales strategy
- **THEN** the manager node routes the input to the knowledge graph extraction nodes in addition to the standard response flow.
