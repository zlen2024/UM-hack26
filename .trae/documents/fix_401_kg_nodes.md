# Plan: Fix 401 Unauthorized Error in Knowledge Graph Agents

## Summary
The `information_extractor_node` and `cypher_generator_node` in `kg_nodes.py` are throwing a `401 Unauthorized` error when called, because they are attempting to use the incorrect `OPENAI_API_BASE` (`https://stg-api.ilmu.ai/v1`) and a fallback `OPENAI_API_KEY` (`demo-key`) instead of the working `ILMU_API_KEY` configuration that the rest of the application uses.

## Current State Analysis
When the Manager triggers the Knowledge Graph extraction loop, the application routes to `information_extractor_node`. Inside `kg_nodes.py`, the `_get_openai_client` function was previously patched to use `api_key = os.getenv("ILMU_API_KEY", os.getenv("OPENAI_API_KEY", ""))`, but the user reverted this patch during the last interaction due to a hallucination incident. Therefore, `kg_nodes.py` currently looks like this:
```python
def _get_openai_client():
    from openai import OpenAI
    return OpenAI(
        base_url=os.getenv("OPENAI_API_BASE", "https://stg-api.ilmu.ai/v1"),
        api_key=os.getenv("OPENAI_API_KEY", "demo-key"),
    )
```
This fails to authenticate because `OPENAI_API_KEY` is missing in the production environment, causing it to fall back to `"demo-key"`, while `cs_agent.py` successfully authenticates using `ILMU_API_KEY`.

## Proposed Changes

### `backend/agents/kg_nodes.py`
**What:** Import and reuse the `get_ilmu_client()` function from `cs_agent.py` instead of redefining `_get_openai_client()`.
**Why:** To enforce a single source of truth for LLM API authentication and avoid environment variable mismatch bugs entirely.
**How:**
1. In `kg_nodes.py`, replace `def _get_openai_client(): ...` with `from .cs_agent import get_ilmu_client`.
2. In `information_extractor_node`, change `_get_openai_client().chat.completions.create` to `get_ilmu_client().chat.completions.create`.
3. In `cypher_generator_node`, change `_get_openai_client().chat.completions.create` to `get_ilmu_client().chat.completions.create`.

## Assumptions & Decisions
- Reusing `get_ilmu_client` ensures that if the base URL or API key environment variables ever change in the future, both files will automatically use the updated configuration.
- The `ilmu-mini-1.0` model hardcoded in `kg_nodes.py` will remain unchanged as per the user's explicit request to undo previous modifications to it.

## Verification Steps
- Run `python3 -m py_compile backend/agents/kg_nodes.py` to ensure syntax is valid.
- Send a message that triggers the KG to ensure the `401 Unauthorized` error no longer occurs.