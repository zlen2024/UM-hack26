# Plan to Add Business Information and Rules to Agent Prompts

## Summary
The user requested that the "business information" (which maps to the existing `BusinessBackground` table) and a new "business rules" table be injected directly into the system prompts of the `gatekeeper` and `manager` nodes. This ensures that both nodes have the complete business context and operational rules to process customer queries accurately.

## Current State Analysis
- The `BusinessBackground` table exists in `backend/models.py` but is currently only injected into `agent_node` in `backend/agents/graph/agent.py`. It is completely missing from the `gatekeeper` and `manager` nodes in `backend/agents/cs_agent.py`.
- There is no table or model for "Business Rules".
- The `gatekeeper` and `manager` prompts are currently static and only take `user_id` and `contact_name` as context.

## Proposed Changes

### 1. Add `BusinessRule` Model (`backend/models.py`)
- Define a new SQLAlchemy model `BusinessRule` with columns: `id`, `user_id` (unique), `rules_text` (Text), `created_at`, `updated_at`.
- Link it to the `User` model. This will store all business rules as a single prompt/text block per user.

### 2. Create Data Access Layer (`backend/agents/business_context.py`)
- Add helper functions `get_business_rule(db, user_id)` and `update_business_rule(db, user_id, text)` to manage the single business rule record.

### 3. Create API Routes for Business Rules (`backend/routes/business_rules.py` & `backend/main.py`)
- Create endpoints (`GET /api/business-rules`, `PUT /api/business-rules`) so users can view and edit their single block of business rules from the frontend.
- Register the new router in `backend/main.py`.

### 4. Inject Context into Agent Prompts (`backend/agents/cs_agent.py`)
- Update `gatekeeper_node` and `manager_node`:
  - Open a database session using `SessionLocal()`.
  - Fetch active `BusinessBackground` entries using `get_active()`.
  - Fetch the single `BusinessRule` entry using `get_business_rule()`.
  - Handle cases where there is no data in the DB gracefully (e.g., if `get_active()` or `get_business_rule()` return empty/None, simply do not append that block to the prompt).
  - Format the data into text blocks (e.g., `=== BUSINESS INFORMATION ===` and `=== BUSINESS RULES ===`).
  - Append these text blocks to the `system_prompt` strings of both the Gatekeeper and Manager LLMs.
  - Close the database session safely using a `try...finally` block.

## Assumptions & Decisions
- The `BusinessBackground` data will only include active entries (`is_active == True`).
- The Business Rules will be a single text column per user so they can free-form type their closing deals and policies.
- The `Base.metadata.create_all(bind=engine)` in `main.py` will automatically create the new `business_rules` table when the app restarts.

## Verification Steps
- Start the backend server and ensure no database errors occur (table is created).
- Test adding a Business Rule via the new API endpoint.
- Trigger a chat message and verify in the logs that the `gatekeeper` and `manager` nodes successfully receive the business context and rules in their system prompts.