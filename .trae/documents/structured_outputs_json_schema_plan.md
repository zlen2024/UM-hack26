# Plan: Implement Structured Outputs (json_schema)

## 1. Summary
Upgrade the LangGraph LLM nodes in `cs_agent.py` to use the explicit `json_schema` mode instead of the basic `json_object` mode. This will force the LLM to strictly conform to the expected JSON structure for the Gatekeeper and Manager nodes, improving reliability and eliminating missing fields or incorrect data types.

## 2. Current State Analysis
- In `/workspace/backend/agents/cs_agent.py`, both `gatekeeper_node` and `manager_node` currently use `response_format={"type": "json_object"}`.
- The expected schema is only described in plain text within the system prompt `RULES` section. While this works most of the time, `json_schema` mode provides a stronger, API-level constraint.

## 3. Proposed Changes

**File:** `/workspace/backend/agents/cs_agent.py`
- **What:** Define explicit JSON Schemas and update the `response_format` parameters.
- **Why:** To utilize the API's native structured output constraints as specified in the provided documentation.
- **How:**
  1. Define a `GATEKEEPER_SCHEMA` dictionary:
     ```python
     GATEKEEPER_SCHEMA = {
         "type": "object",
         "properties": {
             "response": {"type": "string"},
             "agent_loop": {"type": "boolean"},
             "query": {"type": "string"}
         },
         "required": ["response", "agent_loop", "query"],
         "additionalProperties": False
     }
     ```
  2. Define a `MANAGER_SCHEMA` dictionary:
     ```python
     MANAGER_SCHEMA = {
         "type": "object",
         "properties": {
             "task": {
                 "type": "array",
                 "items": {
                     "type": "object",
                     "properties": {
                         "name": {"type": "string"},
                         "args": {"type": "object"}
                     },
                     "required": ["name", "args"],
                     "additionalProperties": False
                 }
             },
             "response": {"type": "string"},
             "knowledge": {"type": "boolean"}
         },
         "required": ["task", "response", "knowledge"],
         "additionalProperties": False
     }
     ```
  3. In `gatekeeper_node`, update the `response_format`:
     ```python
     response_format={
         "type": "json_schema", 
         "json_schema": {
             "name": "gatekeeper_response", 
             "strict": True, 
             "schema": GATEKEEPER_SCHEMA
         }
     }
     ```
  4. In `manager_node`, update the `response_format`:
     ```python
     response_format={
         "type": "json_schema", 
         "json_schema": {
             "name": "manager_response", 
             "strict": True, 
             "schema": MANAGER_SCHEMA
         }
     }
     ```

## 4. Assumptions & Decisions
- **Assumption:** The `api.ilmu.ai` provider correctly supports the standard OpenAI `json_schema` spec as documented.
- **Decision:** The plain text schema descriptions in the system prompts (e.g., `RULES: 1. You MUST respond in strictly valid JSON...`) will be kept as a best practice to provide additional context to the model, but the `response_format` will act as the hard constraint.

## 5. Verification Steps
- Apply the changes to `cs_agent.py`.
- Run a syntax check to ensure dictionaries are properly formatted.
- The LLM should continue to output valid JSON without raising validation or parsing errors.