# Quality Assurance Testing Documentation (QATD) Generation Plan

## Summary
Create a comprehensive Quality Assurance Testing Documentation (QATD) document based on the user's provided template. The document will be fully adapted to the current "UM CRM" application in the workspace, with a strong focus on testing the core AI Agent capabilities, its multi-node LangGraph workflow (Gatekeeper -> Manager -> Worker), and knowledge handling.

## Current State Analysis
- The workspace contains a full-stack CRM application (`UM CRM`) featuring a LangGraph-powered AI Customer Service Agent that operates via webhooks (WhatsApp/Telegram).
- The user has provided a QATD template specifically for "UMHackathon 2026".
- The user's feedback emphasizes that testing should heavily focus on the AI agent's capabilities, specifically task execution, triggering all graph nodes, and handling the knowledge graph.

## Proposed Changes

1. **Create `QATD.md`**: Generate the document in the root directory (`/workspace/QATD.md`).
2. **Document Control & Objective**: 
   - Define the system under test as "UM CRM".
   - Objective: Ensure UM CRM's AI Customer Service Agent can reliably process natural language queries, route intents through its multi-node graph (Gatekeeper, Manager, Worker), autonomously execute CRM tasks (Contacts, Opportunities, Activities), and handle knowledge retrieval accurately under load.
3. **1. Scope & Requirements Traceability**:
   - **In-Scope**: AI Agent intent parsing (Gatekeeper), Task decomposition and routing (Manager), Autonomous CRM task execution (Worker), Knowledge Graph retrieval, and Webhook Integration.
   - **Out-of-Scope**: Basic UI rendering checks, Advanced Billing features, Mock Email/Calendar integrations.
4. **2. Risk Assessment & Mitigation Strategy**:
   - **Risks**: AI Agent hallucinating node routing, Worker executing incorrect/destructive CRM tools, Infinite loops in the LangGraph state, and Knowledge Graph retrieval latency.
5. **3. Test Environment & Execution Strategy**:
   - Define PyTest for mocking LLM endpoints (OpenRouter/Ilmu AI) and validating the LangGraph state transitions.
   - Define CI/CD pipeline using GitHub Actions to run automated graph traversal tests.
6. **4. CI/CD Release Thresholds & Automation Gates**:
   - Enforce AI Output Pass Rate (>80% on documented prompts) and 100% pass rate for critical graph routing unit tests.
7. **5. Test Case Specifications (Drafts)**:
   - **TC-01 (Happy Case - Graph Traversal)**: Verify a complex natural language query successfully triggers the entire pipeline: Gatekeeper accurately parses intent -> Manager decomposes tasks -> Worker executes CRM database functions (e.g., create contact & log activity) -> AI returns coherent response.
   - **TC-02 (Negative Case - Knowledge Graph/Node Failure)**: Verify that ambiguous/out-of-scope prompts are safely handled. If missing context or requesting non-CRM actions, the Gatekeeper/Manager must safely reject or ask for clarification without executing arbitrary functions or triggering infinite loops.
   - **TC-03 (NFR - Graph Concurrency & Performance)**: Load test the multi-node graph execution via webhooks to ensure the agent resolves intents and maintains state persistence without database locking under concurrent load (< 1500ms response).
8. **6. AI Output & Boundary Testing**:
   - **Prompt/Response**: Test complex prompts requiring multi-tool execution (e.g., "Add John and schedule a meeting").
   - **Oversized Input**: Test handling of large text blocks exceeding context windows, ensuring the Gatekeeper correctly chunks or rejects.
   - **Adversarial**: Prompt injection designed to bypass the Gatekeeper and directly command the Worker node to delete records.
   - **Hallucination Handling**: Test the agent's ability to ground responses strictly within the provided knowledge graph and database context.

## Assumptions & Decisions
- The QATD document will be named `QATD.md` and placed in the project root.
- Testing focus is heavily skewed toward the backend AI Agent (LangGraph) rather than generic CRUD UI operations.
- The document will be written in Markdown format, preserving the tables and structure requested in the template.

## Verification Steps
- Read the generated `QATD.md` to ensure no `[e.g., ...]` placeholders remain.
- Ensure Sections 5 and 6 accurately reflect the LangGraph AI Agent's specific architecture (Gatekeeper -> Manager -> Worker).
