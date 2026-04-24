# Plan: Fix 403 Forbidden Error for `ilmu-mini-1.0`

## 1. Summary
The user encountered an `openai.PermissionDeniedError: Error code: 403 - model_not_allowed` when the gatekeeper node tried to use the `ilmu-mini-1.0` model. This indicates the API key/subscription does not have access to this specific model. We need to revert the model back to `ilmu-glm-5.1` (which is known to be authorized based on earlier successful runs) in both `gatekeeper_node` and `manager_node` while keeping the fast-path optimization intact.

## 2. Current State Analysis
- The `gatekeeper_node` fast-path for simple greetings works correctly, but queries that don't match the fast-path trigger a call to the LLM.
- Both `gatekeeper_node` and `manager_node` are currently configured to use `model="ilmu-mini-1.0"`.
- The `ilmu-mini-1.0` model is returning a 403 Forbidden error because it's not included in the user's subscription.

## 3. Proposed Changes

**File:** `/workspace/backend/agents/cs_agent.py`
- **What:** Change the `model` parameter in `client.chat.completions.create` calls.
- **Why:** To use a model that is authorized by the user's API subscription and avoid the 403 error.
- **How:**
  - In `gatekeeper_node` (around line 83):
    Change `model="ilmu-mini-1.0"` back to `model="ilmu-glm-5.1"`.
  - In `manager_node` (around line 133):
    Change `model="ilmu-mini-1.0"` back to `model="ilmu-glm-5.1"`.

## 4. Assumptions & Decisions
- **Assumption:** The `ilmu-glm-5.1` model is authorized because it was successfully executing and returning results prior to the performance optimization changes.
- **Decision:** Keep the fast-path logic for simple greetings as it significantly improves response time without making API calls. Only the fallback LLM calls will revert to the heavier `ilmu-glm-5.1` model.

## 5. Verification Steps
- Simulate an incoming message that skips the fast-path (e.g. "how are you") and verify that the `gatekeeper_node` correctly calls `ilmu-glm-5.1` without throwing a 403 error.