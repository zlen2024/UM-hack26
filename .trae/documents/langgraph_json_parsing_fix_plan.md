# Plan: Fix LangGraph LLM JSON Parsing Error

## 1. Summary
The `cs_agent.py` script fails to parse the LLM response in the `gatekeeper_node` when using `ilmu-glm-5.1` because the model occasionally wraps its JSON output in Markdown formatting (e.g., ````json ... ````) or prepends/appends text. This causes `json.loads(content)` to raise a `JSONDecodeError`. The plan is to add a robust JSON extraction and parsing helper function and use it for all LLM outputs in `cs_agent.py`.

## 2. Current State Analysis
- In `/workspace/backend/agents/cs_agent.py`, both `gatekeeper_node` and `manager_node` parse raw LLM output using `json.loads(content)`.
- The `ilmu-glm-5.1` model is being called with `response_format={"type": "json_object"}`, but occasionally returns content with markdown code blocks.
- A `JSONDecodeError: Expecting value: line 1 column 1 (char 0)` is raised when `content` contains non-JSON text at the beginning.

## 3. Proposed Changes

**File:** `/workspace/backend/agents/cs_agent.py`
- **What:** Add a `parse_llm_json` helper function to extract and parse JSON safely.
- **Why:** To handle markdown-wrapped JSON or JSON embedded within text, preventing `JSONDecodeError`.
- **How:**
  - Import the `re` module.
  - Create `parse_llm_json(content: str) -> dict`:
    ```python
    def parse_llm_json(content: str) -> dict:
        if not content:
            raise ValueError("LLM returned empty content")
        
        content = content.strip()
        
        # Extract from markdown block if present
        match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
        if match:
            content = match.group(1)
            
        # Fallback to finding the first { and last }
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
            content = content[start_idx:end_idx+1]
            
        return json.loads(content)
    ```
  - Update `gatekeeper_node` (around line 56):
    Replace `result = json.loads(content)` with `result = parse_llm_json(content)`.
  - Update `manager_node` (around line 106):
    Replace `result = json.loads(content)` with `result = parse_llm_json(content)`.

## 4. Assumptions & Decisions
- Assumption: The LLM output always contains a valid JSON object starting with `{` and ending with `}`.
- Decision: Use regex and string manipulation to isolate the JSON object before passing it to `json.loads`. This is safer than modifying the model or system prompt which may still occasionally fail.

## 5. Verification Steps
- Simulate an LLM response containing ````json { ... } ```` and ensure `parse_llm_json` successfully parses it.
- Verify that `gatekeeper_node` and `manager_node` process user inputs correctly without raising `JSONDecodeError`.