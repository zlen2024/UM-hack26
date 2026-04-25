# Plan to Fix Knowledge Graph Context Retrieval

## Summary
The user tested the updated chat flow: `"hey.. i love ikan.. and also i had a sister name farhana... by the way my name is hakimi.. so what is my full name,, take a guest.."`.
The logs show that the Manager successfully executed and provided a response, but it still couldn't guess the user's full name because it didn't have the context.
Furthermore, the `[KG Evaluator]` ran after the Manager, and its output was `Raw Output: None`, resulting in `[Manager] Evaluated KG trigger: False`. 

This means two things are failing:
1. The **Active Knowledge Graph Context Retrieval** (`get_relevant_context`) is not finding or returning the previously saved facts (like the user's full name) before the Manager runs.
2. The **KG Evaluator** (`ilmu-glm-5.1`) is still returning `None` instead of evaluating the new facts ("ikan", "farhana", "hakimi").

## Current State Analysis
- **Active Retrieval**: In `backend/knowledge_db.py`, `get_relevant_context` tries to find words longer than 3 characters (`\w{4,}`). It runs Cypher queries like `MATCH (n:Entity) WHERE lower(n.id) CONTAINS 'keyword'`. If the database is empty or the keywords don't match exactly, it returns an empty string. We need to log what it's searching for and finding.
- **KG Evaluator**: In `backend/agents/cs_agent.py`, the `ilmu-glm-5.1` model returns `None`. This often happens if the `max_tokens` is set too low (currently `10`). Some models fail completely if they calculate they can't fit their preamble and answer in 10 tokens.

## Proposed Changes

### 1. Fix KG Evaluator Token Limit
- **File**: `backend/agents/cs_agent.py`
- **What**: Increase `max_tokens` to allow the model breathing room.
- **How**: Change `max_tokens=10` to `max_tokens=100` in `evaluate_kg_trigger`. The model will still just output "YES" or "NO", but it won't crash/abort due to token constraints.

### 2. Improve Active Context Retrieval & Logging
- **File**: `backend/knowledge_db.py` and `backend/agents/cs_agent.py`
- **What**: Add logging to see what keywords are being searched, and improve the keyword extraction to catch names (even if they are 3 letters).
- **How**: 
  - Change regex to `\w{3,}` to catch 3-letter names (e.g., "Ali", "Abu").
  - Add `print()` or `logger.info()` statements inside `get_relevant_context` to log the keywords found and the number of facts retrieved.
  - Ensure the `kg_context` is properly formatted and logged in `cs_agent.py` before being passed to the Manager.

## Assumptions & Decisions
- The `ilmu-glm-5.1` model returning `None` is highly likely a token limitation issue or strict API constraint. Increasing `max_tokens` is a safe fix.
- The active retrieval might be failing simply because the data wasn't saved in the previous step (because the KG Evaluator failed). Once the evaluator is fixed, the data will save, and subsequent retrievals will succeed.

## Verification Steps
- Apply the fixes.
- Send the message again.
- Verify in the logs that `[KG Evaluator] Raw Output` now shows `YES`.
- Check the backend logs to see what keywords `get_relevant_context` searches for.