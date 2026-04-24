# Tasks
- [x] Task 1: Update AgentState definition
  - [x] SubTask 1.1: Modify `AgentState` in `backend/agents/cs_agent.py` to include a `messages` list (to store the conversation history, including tool calls and tool results).
- [x] Task 2: Refactor tool definitions
  - [x] SubTask 2.1: Create a helper function in `cs_agent.py` to convert `CRM_TOOLS` into the OpenAI-compatible `tools` array format (extracting name, description, and parameters from the Langchain tools).
- [x] Task 3: Refactor Manager Node
  - [x] SubTask 3.1: Update the `manager_node` system prompt to remove instructions about outputting the custom JSON task array.
  - [x] SubTask 3.2: Modify the LLM call in `manager_node` to pass the `tools` parameter and handle the response. If `tool_calls` are present, store them in the state; if not, store the final text response.
- [x] Task 4: Refactor Worker Node
  - [x] SubTask 4.1: Update `worker_node` to iterate over `tool_calls` from the state instead of the custom `current_tasks` list.
  - [x] SubTask 4.2: Execute each tool and append the result as a dictionary with `role: "tool"`, `tool_call_id`, and `content` to the `messages` list in the state.
- [x] Task 5: Update Routing Logic
  - [x] SubTask 5.1: Update `manager_router` to route to `worker` if `tool_calls` are present, or `END` if a final text response is generated.

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 2
- Task 4 depends on Task 3
- Task 5 depends on Task 4
