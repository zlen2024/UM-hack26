# Tasks

- [x] Task 1: Setup basic project structure and state definition
  - [x] SubTask 1.1: Install necessary dependencies (`langgraph`, `langchain`, `langchain-openai`, `pydantic`)
  - [x] SubTask 1.2: Define the LangGraph State (`AgentState`) using `TypedDict`, containing `user_input`, `gatekeeper_response`, `manager_response`, `current_tasks`, and `worker_error`
  - [x] SubTask 1.3: Define Pydantic models for structured LLM outputs (`GatekeeperOutput`, `ManagerOutput`)

- [x] Task 2: Implement Gatekeeper Node
  - [x] SubTask 2.1: Create the Gatekeeper system prompt
  - [x] SubTask 2.2: Implement the `gatekeeper_node` function using `with_structured_output` and a temperature of 0

- [x] Task 3: Implement Manager Node
  - [x] SubTask 3.1: Create the Manager system prompt
  - [x] SubTask 3.2: Implement the `manager_node` function handling both user queries and worker errors using `with_structured_output`

- [x] Task 4: Implement Worker Node and Tools
  - [x] SubTask 4.1: Create mock functions for tasks (e.g., `verify_order`, `check_payment_status`) to simulate success and failure
  - [x] SubTask 4.2: Implement the `worker_node` function that iterates through tasks and handles exceptions

- [x] Task 5: Build and Compile LangGraph
  - [x] SubTask 5.1: Initialize `StateGraph` and add Gatekeeper, Manager, and Worker nodes
  - [x] SubTask 5.2: Implement conditional edge routing (START -> Gatekeeper, Gatekeeper -> END/Manager, Manager -> END/Worker, Worker -> Manager)
  - [x] SubTask 5.3: Compile the graph and provide an execution entry point with comments explaining the logic

# Task Dependencies
- Task 2 and 3 depend on Task 1
- Task 4 depends on Task 3
- Task 5 depends on Tasks 2, 3, and 4
