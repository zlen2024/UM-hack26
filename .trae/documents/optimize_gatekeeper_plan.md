# Plan: Optimize Gatekeeper Response Time

## 1. Summary
The `gatekeeper_node` currently calls the heavy `ilmu-glm-5.1` LLM for every incoming message, which takes ~47 seconds even for simple greetings like "hye again". To drastically improve response times, we will implement a fast-path heuristic check for common greetings before invoking the LLM, bypassing the network call entirely for these cases. We will also switch the fallback model to a faster alternative (`ilmu-mini-1.0`) for other queries.

## 2. Current State Analysis
- In `/workspace/backend/agents/cs_agent.py`, the `gatekeeper_node` receives the user's message and immediately makes a blocking API call to `api.ilmu.ai` using `ilmu-glm-5.1`.
- The webhook logs show that simple messages trigger this heavy intent routing, resulting in significant and unnecessary delays.

## 3. Proposed Changes

**File:** `/workspace/backend/agents/cs_agent.py`
- **What:** Add a fast-path bypass in `gatekeeper_node` for simple greetings and switch the LLM to a faster model.
- **Why:** To provide instant responses for basic chit-chat without incurring the latency of an LLM call, and to speed up intent routing for actual queries.
- **How:**
  - Inside `gatekeeper_node`, right after extracting `user_input`, clean and normalize the text (lowercase, remove punctuation).
  - Create a set of common greetings (e.g., "hi", "hello", "hey", "hye", "hye again", "good morning", "thanks", "ok").
  - If the normalized input matches a greeting, immediately return a hardcoded `gatekeeper_response` with `agent_loop: False` and a friendly response.
  - Update the `model` parameter in the `client.chat.completions.create` call from `"ilmu-glm-5.1"` to `"ilmu-mini-1.0"` (a faster model already used in `backend/agents/graph/nodes.py`) for queries that do need LLM routing.

## 4. Assumptions & Decisions
- **Assumption:** Simple greetings and acknowledgments do not require complex backend processing or context lookup.
- **Decision:** Implementing the fast-path directly inside `gatekeeper_node` avoids changing the overall LangGraph topology while achieving the desired performance gain.
- **Decision:** Switching to `ilmu-mini-1.0` will reduce latency for non-greeting queries without sacrificing the simple intent routing capability.

## 5. Verification Steps
- Simulate a request with "hye again" and verify it hits the fast-path and returns instantly.
- Simulate a complex request (e.g., "check my order status") and verify it falls back to the `ilmu-mini-1.0` model correctly and sets `agent_loop: True`.