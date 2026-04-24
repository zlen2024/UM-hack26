# Plan: Reduce max_tokens to Mitigate API Timeout

## 1. Summary
The `cs_agent.py` LangGraph workflow is currently experiencing `504 Gateway Timeout` errors from the `api.ilmu.ai` endpoint. As per the provider's documentation, one of the recommended resolutions for this error is to reduce `max_tokens`. We will explicitly set `max_tokens=2000` on all LLM calls within the workflow to constrain output size and potentially speed up processing on the provider's end.

## 2. Current State Analysis
- The `gatekeeper_node` and `manager_node` in `/workspace/backend/agents/cs_agent.py` both call `client.chat.completions.create` using the `ilmu-glm-5.1` model.
- Neither of these calls currently specifies a `max_tokens` parameter, meaning they default to the model's maximum allowed output length.
- The absence of this constraint may be contributing to the upstream model taking too long to generate responses, resulting in a 504 timeout.

## 3. Proposed Changes

**File:** `/workspace/backend/agents/cs_agent.py`
- **What:** Add `max_tokens=2000` to the `client.chat.completions.create` calls.
- **Why:** To explicitly limit the output size, forcing the model to complete generation faster and mitigating the 504 timeout issue as suggested by the API documentation.
- **How:**
  1. In `gatekeeper_node` (around line 115), add `max_tokens=2000` as a keyword argument to `client.chat.completions.create`.
  2. In `manager_node` (around line 172), add `max_tokens=2000` as a keyword argument to `client.chat.completions.create`.

## 4. Assumptions & Decisions
- **Assumption:** 2000 tokens is sufficient for both the Gatekeeper's intent routing JSON response and the Manager's task planning JSON response. Given that these are structured JSON outputs, 2000 tokens should be more than enough.
- **Decision:** Applying the token limit to both nodes ensures that neither step in the workflow causes an unexpected timeout due to runaway generation.

## 5. Verification Steps
- Apply the changes to `cs_agent.py`.
- Ensure there are no syntax errors introduced.
- The LangGraph nodes should successfully pass the `max_tokens` parameter to the API.