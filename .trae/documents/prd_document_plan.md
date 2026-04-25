# Product Requirement Document (PRD) Generation Plan

## Summary
Create a comprehensive Product Requirement Document (PRD) for the "UM CRM" application, adhering exactly to the UMHackathon 2026 PRD template provided by the user. The document will replace the "Stitch" template examples with actual product details of UM CRM, highlighting its AI Customer Service Agent capabilities and Kanban-based CRM features.

## Current State Analysis
- **System**: UM CRM (Next.js Frontend, FastAPI Backend).
- **Core Product Value**: Automating and streamlining sales pipelines and customer relationship management through an autonomous AI agent (via WhatsApp/Telegram) and a visual web dashboard.
- **Goal**: Generate a PRD that defines the project overview, background, user stories, system functionalities (specifically the LLM model and prompt design), included/excluded features, and project risks.

## Proposed Changes

1. **Create `PRD.md`**: Generate the document in the root directory (`/workspace/PRD.md`).
2. **Project Overview**:
   - **Problem Statement**: Traditional CRMs require manual data entry, constant context switching, and high friction for sales reps, leading to outdated pipelines.
   - **Target Domain**: Sales enablement, customer relationship management, and conversational AI automation.
   - **Proposed Solution**: UM CRM provides a unified Kanban dashboard combined with an autonomous AI Customer Service Agent that logs activities, creates contacts, and updates deals directly from natural language chats (WhatsApp/Telegram).
3. **Background & Business Objective**:
   - Detail the transition from scattered spreadsheets and manual chat logs to an AI-native CRM ecosystem.
   - Strategic Fit: Aligns with AI-driven automation, reducing manual administrative tasks for sales teams.
4. **Product Purpose & Target Audience**:
   - **Goal**: To provide an AI-enabled partner in sales and customer relationship management.
   - **Users**: Sales Representatives, Account Managers, Business Development Professionals, and Customers (via chat).
5. **System Functionalities**:
   - **Key Functionalities**: Conversational CRM Updates (AI), Visual Pipeline Management (Kanban), Activity Tracking, and Multi-channel Webhooks.
   - **AI Model & Prompt Design**:
     - *Model Selection*: Z AI GLM / OpenRouter / Ilmu AI. Chosen for high reasoning capabilities required for tool execution and intent parsing.
     - *Prompting Strategy*: Multi-step agentic prompting via LangGraph (Gatekeeper -> Manager -> Worker). Ensures safe, isolated, and deterministic CRM task execution.
     - *Context Handling*: Context windows are managed by truncating chat history. Oversized inputs (>2000 tokens) are chunked or rejected with a graceful error message.
     - *Fallback/Failure*: Gatekeeper rejects off-topic requests. Manager handles hallucinated tools by catching Pydantic validation errors and asking the user for clarification.
6. **User Stories & Use Cases**:
   - *User Story*: "As a sales rep, I want the AI to automatically log a meeting when a client confirms it on WhatsApp, so I don't have to manually enter it."
   - *Prompt to CRM Flow*: User messages -> Webhook -> Gatekeeper parses intent -> Manager assigns tasks -> Worker executes DB changes -> Response sent.
7. **Scope Definition & Control**:
   - **Included**: Conversational AI updates via webhooks, 2D Kanban board, Contact/Activity management.
   - **Not Included**: Advanced financial billing, native mobile apps, mass marketing email campaigns.
8. **Assumptions & Constraints**:
   - **LLM Cost**: Controlled by caching repeated queries and using a "fast-path" for simple greetings to bypass the LLM entirely.
   - **Technical/Performance**: Async webhook processing required to prevent timeouts.
9. **Risks & Questions**:
   - **Data Privacy**: Ensuring AI does not leak cross-client data.
   - **Intent Misinterpretation**: Handling scenarios where the AI creates duplicate contacts or misunderstands the deal stage.

## Assumptions & Decisions
- The document will be named `PRD.md` and placed in the project root.
- The document will strictly follow the provided template's numbering and section headers.
- The "Stitch" examples will be entirely replaced by UM CRM features.

## Verification Steps
- Read the generated `PRD.md` to ensure all 9 template sections are fully populated.
- Verify no `[e.g., ...]` placeholders remain.
- Ensure the AI capabilities (LangGraph, webhooks) are accurately reflected in section 4.3.