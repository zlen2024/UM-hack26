# Plan: Fix JSONDecodeError in Gatekeeper Node

## Summary
Investigate and resolve the `JSONDecodeError` in the `gatekeeper_node` without modifying the user's `response_format` schemas or environment variable configurations in other files.

## Current State Analysis
The Gatekeeper node in `cs_agent.py` throws a `JSONDecodeError: Expecting value: line 1 column 1 (char 0)`. This occurs because the LLM (`ilmu-glm-5.1`) returns plain conversational text instead of the requested JSON schema.
Using the `bug-hunter` skill, the root cause was identified: `gatekeeper_node` directly appends `state.get("messages", [])` (the raw conversation history) into the API `messages` array. When the model sees previous `{"role": "assistant", "content": "..."}` messages, it assumes it is participating in an ongoing natural conversation and ignores the `Output: {...}` JSON structure defined in the system prompt's few-shot examples.

## Proposed Changes

### `backend/agents/cs_agent.py`
**What:** Modify how conversation history is passed to the Gatekeeper.
**Why:** To provide the Gatekeeper with conversation context (for resolving coreferences like "yes, do it") without breaking its JSON output format.
**How:**
1. Remove the loop that appends `state.get("messages", [])` directly to `messages_for_gatekeeper`.
2. Format the history into a structured text block (e.g., `Customer: ... \n Agent: ...`).
3. Append this text block to the `system_prompt` under a `=== RECENT CONVERSATION HISTORY ===` header.
4. Format the final user message to exactly match the few-shot examples (`Input: "{user_input}"`).

## Assumptions & Decisions
- The user specifically requested to undo my previous changes to `response_format` and `kg_nodes.py`. Those files/lines will remain strictly untouched.
- The `ilmu-glm-5.1` model correctly supports `{"type": "json_schema"}` as long as the prompt format isn't corrupted by conversational `assistant` messages.

## Verification Steps
- Trigger a multi-turn conversation with the Gatekeeper to ensure it successfully outputs JSON and routes to the agent loop without raising a `JSONDecodeError`.