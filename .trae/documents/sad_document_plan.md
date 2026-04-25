# System Analysis Documentation (SAD) Generation Plan

## Summary
Create a comprehensive System Analysis Documentation (SAD) for the "UM CRM" application, adhering exactly to the UMHackathon 2026 SAD template. The document will detail the client-server architecture, database schema, and explicitly focus on the LangGraph-based AI Customer Service Agent as a service layer (Gatekeeper, Manager, Worker flow).

## Current State Analysis
- **System**: UM CRM (Next.js Frontend, FastAPI Backend, PostgreSQL DB).
- **Core AI Feature**: A stateful LangGraph AI Agent integrated via webhooks (WhatsApp/Telegram) that autonomously executes CRM tasks (create contacts, log activities) using OpenRouter/Ilmu AI.
- **Deployment**: Deployed on Fly.io (Cloud-native) with Docker.
- **Goal**: Generate a detailed technical architecture document focusing on the system's structure, the AI dependency flow, data models, functional/non-functional requirements, and project evaluation metrics.

## Proposed Changes

1. **Create `SAD.md`**: Generate the document in the root directory (`/workspace/SAD.md`).
2. **Introduction & Background**:
   - Define the purpose of the SAD for UM CRM.
   - Describe the background: Transitioning from manual sales tracking to an AI-automated CRM.
   - Target Stakeholders: Sales Representatives, Customers (via Webhooks), Development Team, and QA Team.
3. **System Architecture & Design**:
   - **High-Level Architecture**: Describe the Client-Server model (Next.js, FastAPI) deployed on Fly.io.
   - **LLM as Service Layer**: 
     - *Dependency Diagram description*: Map the flow from Customer WhatsApp -> FastAPI Webhook -> LangGraph State -> Ilmu AI / OpenRouter -> PostgreSQL -> Webhook Reply.
     - *Token/Context Limits*: Explain the fast-path greeting mechanism in `cs_agent.py` to save tokens, and how the state dictionary manages context.
     - *Sequence Diagram description*: Walk through a specific flow: "Customer asks to log a meeting" -> Gatekeeper (Intent) -> Manager (Task List) -> Worker (DB execution) -> Response.
4. **Technological Stack**:
   - Frontend: Next.js 14 (React, Tailwind CSS).
   - Backend: FastAPI (Python), LangGraph (AI orchestration).
   - Database: PostgreSQL (SQLAlchemy ORM).
   - Cloud: Fly.io, AWS RDS (hypothetical production).
5. **Key Data Flows & Schema**:
   - Describe the Data Flow Diagram (DFD) across the 3 main CRM entities.
   - Describe the 3NF Database Schema: `users`, `contacts`, `opportunities`, and `activities`.
6. **Functional Requirements & Scope (MVP)**:
   - 1. AI Customer Service via Webhooks.
   - 2. Kanban Board for Opportunity Tracking.
   - 3. Contact & Activity Management.
7. **Non-Functional Requirements (NFRs)**:
   - **Scalability**: Fly.io auto-start/stop machines.
   - **Reliability**: Transactional DB rollbacks on failed AI tool executions.
   - **Token Latency**: Fast-path for greetings (skips LLM), < 1500ms response goal.
   - **Cost Efficiency**: Utilizing Ilmu AI/OpenRouter effectively, restricting context window size.
8. **Out of Scope / Future Enhancements**:
   - Native mobile app, advanced financial billing, Google Workspace deep sync.
9. **Monitor, Evaluation, Assumptions & Dependencies**:
   - *Technical Evaluation*: Grayscale rollout of new LangGraph nodes.
   - *Dependencies*: Ilmu AI / OpenRouter APIs (High Risk of rate limits).

## Assumptions & Decisions
- The document will be formatted strictly in Markdown, using tables where specified by the template (e.g., Stakeholders, Architecture, NFRs).
- Will explicitly detail the "Gatekeeper -> Manager -> Worker" Triad-node architecture as the core "LLM as Service Layer" design.

## Verification Steps
- Read the generated `SAD.md` to ensure all template sections (Introduction, Architecture, LLM Service Layer, Stack, Data Flow, MVP, NFRs, Monitoring) are fully populated with UM CRM context.
- Verify there are no generic `[e.g., ...]` placeholders left in the document.
