# Rebuild Agent Workflow Spec

## Why
The current agent architecture needs to be rebuilt to use a robust, stateful multi-agent workflow based on LangGraph. This architecture will support a Supervisor-Worker (Outer/Inner Loop) pattern specifically tailored for customer service, ensuring reliable task execution, clear decision boundaries, and built-in error fallback mechanisms.

## What Changes
- Implement a LangGraph-based customer service agent workflow.
- Define a structured state (`TypedDict` or Pydantic) containing `user_input`, `gatekeeper_response`, `manager_response`, `current_tasks`, and `worker_error`.
- Create a **Gatekeeper (Intent Router)** node to evaluate user inputs and decide if they need complex backend processing or immediate responses.
- Create a **Manager (Outer Loop)** node to act as the business rules engine, deciding which tasks need to be executed or if clarification is needed.
- Create a **Worker (Inner Loop)** node to sequentially execute a queue of tasks and handle errors/fallbacks.
- Implement conditional routing logic between the nodes.
- Utilize structured outputs (JSON) for LLM interactions.

## Impact
- Affected specs: Customer service agent routing and task execution capabilities.
- Affected code: `/agent` directory (new graph definitions, node implementations, state definitions).

## ADDED Requirements
### Requirement: LangGraph Architecture
The system SHALL provide a multi-node LangGraph workflow containing Gatekeeper, Manager, and Worker nodes.

#### Scenario: Simple Inquiry
- **WHEN** user inputs a simple greeting or general question.
- **THEN** Gatekeeper sets `agent_loop` to false, provides a direct `response`, and the graph terminates (END).

#### Scenario: Actionable Request
- **WHEN** user requests an action (e.g., checking an order).
- **THEN** Gatekeeper sets `agent_loop` to true and extracts the `query`. The Manager evaluates the query and outputs a list of tasks. The Worker executes the tasks.

#### Scenario: Worker Fallback
- **WHEN** a task executed by the Worker fails.
- **THEN** the Worker immediately breaks the loop, captures the error in `worker_error`, and routes back to the Manager to decide the next step.

## MODIFIED Requirements
### Requirement: LLM Responses
The LLM responses MUST strictly follow JSON schemas utilizing `with_structured_output` and a temperature of 0.

## REMOVED Requirements
### Requirement: Old Agent Logic
**Reason**: Replaced with the new LangGraph Supervisor-Worker architecture.
**Migration**: The `/agent` endpoints will now trigger the compiled LangGraph execution.
