# Tasks
- [x] Task 1: Initialize Graph Database Connection
  - [x] SubTask 1.1: Setup graph database connection (e.g., LadybugDB).
  - [x] SubTask 1.2: Create schema initialization function for `Entity` and `RelatedTo` tables.
- [x] Task 2: Implement Information Extractor Agent (LangGraph Node)
  - [x] SubTask 2.1: Create the prompt template using the provided DSNF rules.
  - [x] SubTask 2.2: Implement the LLM invocation to extract nodes and edges as structured JSON.
- [x] Task 3: Implement Cypher Generator Agent (LangGraph Node)
  - [x] SubTask 3.1: Create the prompt template for converting JSON to Cypher `MERGE` queries.
  - [x] SubTask 3.2: Implement the Cypher extraction and database execution logic.
- [x] Task 4: Update Manager Node (LangGraph Router)
  - [x] SubTask 4.1: Add evaluation logic to detect important customer details (preferences, strategies).
  - [x] SubTask 4.2: Add conditional routing to trigger the extraction pipeline when necessary.
- [x] Task 5: Implement API Endpoints
  - [x] SubTask 5.1: Create `/api/chat` endpoint to test the extraction and conversational flow.
  - [x] SubTask 5.2: Create `/api/graph` endpoint to fetch graph data for frontend visualization.

# Task Dependencies
- Task 2 and Task 3 depend on Task 1.
- Task 4 depends on Task 2 and Task 3.
- Task 5 depends on Task 2, Task 3, and Task 1.
