# Plan to Investigate and Fix Manager Logic (Language and KG Extraction)

## Summary
The user tested the chat flow with a message combining English and Malay (`"hey.. i love ikan.. and also i had a sister name farhana... by the way my name is hakimi.. so what is my full name,, take a guest.."`).
The logs show:
1. The Gatekeeper correctly parsed the input, triggering the agent loop.
2. The Manager executed, outputted 0 tool calls.
3. The `evaluate_kg_trigger` ran and correctly resolved the bug we fixed earlier. However, it evaluated to `False`, meaning the Knowledge Graph (KG) extraction was skipped.
4. The user also questioned why the system responds in Malay (`"hye.. apa khabar"`).

### Issues to Fix:
1. **KG Evaluator Logic**: The `evaluate_kg_trigger` relies on the fast model (`ilmu-glm-5.1`) with a strict prompt expecting a `YES` or `NO`. The prompt is currently entirely in English. If the user input contains Malay words ("ikan"), the fast model might fail to recognize the intent or format its output strictly, leading to a `False` evaluation.
2. **Language Handling**: The Manager LLM is responding in Malay because the prompt doesn't strictly dictate the response language, and the `ilmu-glm-5.1` model might be adapting to the user's language ("hye.. apa khabar" in previous tests).
3. **Observability**: The user requested extra logs to understand the system's reasoning.

## Current State Analysis
- In `backend/agents/cs_agent.py`, `evaluate_kg_trigger` sends the prompt and checks if `"YES"` is in the output. If the model responds in Malay ("YA"), it fails.
- There is minimal logging of what the LLM actually returns in `evaluate_kg_trigger` before we check for `"YES"`.
- The `manager_node` system prompt does not specify a language rule.

## Proposed Changes

### 1. Enhance Logging (Observability)
- **File**: `backend/agents/cs_agent.py`
- **What**: Add detailed `logger.info` statements.
- **How**: 
  - Inside `evaluate_kg_trigger`: Log the exact text sent to the evaluator and the exact raw output from the LLM before stripping it.
  - Inside `manager_node`: Log the raw content of the assistant's response.

### 2. Fix `evaluate_kg_trigger` Language and Logic
- **File**: `backend/agents/cs_agent.py`
- **What**: Make the prompt robust against mixed languages and log its output.
- **How**: Update the prompt to explicitly state: "Regardless of the language of the text, you MUST respond with ONLY the English word 'YES' or 'NO'." Also, log the `content` variable so we can see what the model actually decided.

### 3. Enforce Response Language in Manager
- **File**: `backend/agents/cs_agent.py`
- **What**: Update the `manager_node` system prompt.
- **How**: Add a Conversation Rule: "Always respond in the same language the user is speaking. If they use mixed languages (e.g., English and Malay), respond in English by default unless they explicitly request otherwise."

## Assumptions & Decisions
- The `ilmu-glm-5.1` model is highly capable but might get confused by mixed-language prompts if not given strict constraints.
- Adding `logger.info` statements will not impact performance but will greatly aid debugging.

## Verification Steps
- Start the backend server.
- Send the exact same test message ("hey.. i love ikan..").
- Verify in the console logs that `[KG Evaluator] Raw Output:` is printed and shows `YES`.
- Verify the AI responds appropriately in the desired language.