# Plan to Fix Knowledge Graph Trigger Evaluation Bug

## Summary
The user provided a log trace showing a failure during the execution of the Customer Service Agent workflow:
```
[KG Evaluator] Error: 'NoneType' object has no attribute 'strip'
[Manager] Evaluated KG trigger: False
```
This error occurred right after the `manager_node` finished executing and attempted to evaluate whether to trigger the Knowledge Graph (KG) extraction via `evaluate_kg_trigger`. 

## Current State Analysis
In `backend/agents/cs_agent.py`, the `evaluate_kg_trigger` function calls the LLM to determine if the text contains important customer details. It expects the LLM to return `'YES'` or `'NO'`. 
The code currently does this:
```python
        response = client.chat.completions.create(
            model="ilmu-glm-5.1", # Fast model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=10,
        )
        content = response.choices[0].message.content.strip().upper()
```
If the LLM returns an empty message or the API response doesn't properly format the `content` field, `response.choices[0].message.content` is `None`. Calling `.strip()` on `None` throws the `'NoneType' object has no attribute 'strip'` error.

## Proposed Changes

### 1. Fix `evaluate_kg_trigger` Error Handling
- **File**: `backend/agents/cs_agent.py`
- **What**: Update the parsing logic in `evaluate_kg_trigger` to safely handle `None` content.
- **How**: 
  ```python
        content = response.choices[0].message.content
        if not content:
            return False
        content = content.strip().upper()
        return "YES" in content
  ```

## Assumptions & Decisions
- The `ilmu-glm-5.1` API might occasionally return an empty response (`content = None`) for very short max_tokens or edge cases, so safe extraction is necessary.

## Verification Steps
- Deploy or run the backend.
- Send a message that shouldn't trigger the KG or might cause an empty response.
- Verify in the logs that the `[KG Evaluator] Error` no longer appears and it safely evaluates to `False`.