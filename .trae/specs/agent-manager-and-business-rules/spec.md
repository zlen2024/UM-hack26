# Agent Manager and Business Rules Spec

## Why
Users need a centralized interface ("Agent Manager") to manage how the AI agent behaves, including setting Business Rules and viewing all incoming customer messages across channels. Additionally, the AI agent needs to have proper context of the sender (name and phone number) persistently available in its state to improve Knowledge Graph extraction.

## What Changes
- Update the backend to expose API endpoints for setting/getting Business Rules and retrieving all customer messages.
- Update the frontend sidebar navigation to route the "Coming soon" button to a new `/agent-manager` page.
- Create the "Agent Manager" page with tabs/sections for "Knowledge Graph", "Business Rules", and "Chat Messages".
- Update the LangGraph agent state and initial prompt to explicitly carry the user's name and phone number throughout the execution flow (especially during KG extraction).

## Impact
- Affected specs: Knowledge Graph Extraction, Agent Routing, Webhook Processing.
- Affected code:
  - `backend/routes/whatsapp.py`, `backend/routes/chatery.py`
  - `backend/agents/cs_agent.py`, `backend/agents/kg_nodes.py`
  - `backend/routes/business_rules.py` (New or Updated)
  - `backend/routes/messages.py` (New or Updated)
  - `frontend/components/Sidebar.tsx` (or equivalent layout component)
  - `frontend/pages/agent-manager.tsx` (or equivalent routing)

## ADDED Requirements
### Requirement: Agent Manager UI
The system SHALL provide an Agent Manager page accessible from the sidebar.
- **Scenario: Success case**
  - **WHEN** user clicks the Agent Manager button on the sidebar
  - **THEN** they are routed to the Agent Manager interface which displays Business Rules, Chat Messages, and Knowledge Graph sections.

### Requirement: Business Rules Management
The system SHALL allow users to view, create, and update business rules.
- **Scenario: Success case**
  - **WHEN** user submits a new business rule in the UI
  - **THEN** it is saved to the database and injected into the agent's `system_prompt` on subsequent messages.

### Requirement: Global Chat Messages Viewer
The system SHALL display all incoming customer messages.
- **Scenario: Success case**
  - **WHEN** user views the Chat Messages section
  - **THEN** a list of messages fetched from the database is displayed.

## MODIFIED Requirements
### Requirement: Message Context Persistence
The agent's state MUST explicitly persist the sender's phone number and name.
- **Scenario: Success case**
  - **WHEN** a message is received via the webhook
  - **THEN** `contact_name` and `phone` are added to the agent's prompt context and remain accessible to the `information_extractor_node` to improve entity extraction.
