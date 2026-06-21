# UM CRM - Code Wiki

## 1. Executive Summary

**UM CRM** is a full-stack Customer Relationship Management (CRM) application designed for sales teams, account managers, and business development professionals. It facilitates the management of sales pipelines, contacts, tasks, and team collaboration.

A standout feature of UM CRM is its integrated **AI Customer Service Agent**, powered by LangGraph. This agent handles customer queries via multiple channels (WhatsApp, Telegram, Chatery) and can autonomously execute CRM tasks (like creating contacts or logging activities) by routing intents through an intelligent gatekeeper-manager-worker pipeline.

---

## 2. Architecture Overview

The project follows a decoupled client-server architecture:

- **Frontend (Client)**: Built with **Next.js 14** (App Router) and React. Uses **Tailwind CSS** for styling, **@dnd-kit** for Kanban board drag-and-drop interactions, and **next-pwa** for Progressive Web App capabilities.
- **Backend (Server)**: Built with **FastAPI** (Python 3.13). Exposes RESTful APIs for the frontend and webhook endpoints for third-party integrations.
- **Database**: Uses **SQLite** by default (a local file, zero-config), and can run on **PostgreSQL** by setting `DATABASE_URL`. Both are accessed through the SQLAlchemy ORM.
- **AI Agent Layer**: Uses **LangGraph** to build a stateful, multi-actor agent workflow. It leverages LLMs (via OpenRouter or Ilmu AI) to parse natural language into CRM tool executions.

### High-Level Data Flow
1. **User Interaction**: Users interact with the Next.js frontend (e.g., moving a deal on the Kanban board).
2. **API Request**: The frontend sends an authenticated HTTP request (JWT) to the FastAPI backend.
3. **Business Logic**: The backend processes the request using SQLAlchemy to query/update the relational database (SQLite by default, PostgreSQL optional).
4. **AI/Webhook Flow**: External messages (WhatsApp/Telegram) hit FastAPI webhook endpoints (`/api/whatsapp`, `/api/telegram`), which trigger the LangGraph AI workflow (`backend/agents/cs_agent.py`) to process intents, execute tools, and respond.

---

## 3. Core Modules & Responsibilities

### Backend (`/backend`)
- `main.py`: The FastAPI application entry point. Handles middleware configuration (CORS), database table creation, schema migrations, and router registration.
- `database.py`: Manages the SQLAlchemy database engine, session pooling (NullPool for compatibility), and programmatic migrations.
- `models.py`: Defines the SQLAlchemy ORM models representing the database schema.
- `routes/`: Contains all REST API endpoints.
  - `auth.py`, `users.py`: User authentication (JWT) and management.
  - `contacts.py`, `opportunities.py`, `tasks.py`, `activities.py`: CRUD operations for core CRM entities.
  - `whatsapp.py`, `telegram.py`, `chatery.py`: Webhook handlers for external messaging platforms.
  - `gmail.py`, `google_calendar.py`, `emails.py`: Google Workspace integrations.
- `agents/`: Contains the LangGraph-based AI agent logic.
  - `cs_agent.py`: Thin entry point / channel adapter. Loads context, runs the graph, persists the conversation, and triggers background KG extraction. Exposes `process_whatsapp_message` / `process_telegram_message` and the compiled `graph`.
  - `graph/`: The LangGraph workflow package:
    - `state.py` — `AgentState` with an append-messages reducer.
    - `llm.py` — centralized LLM client + structured-output helpers.
    - `prompts.py` — gatekeeper/manager system prompts.
    - `nodes.py` — `gatekeeper`, `manager`, `worker`, `force_response` nodes (tool-loop capped by `MAX_TOOL_ITERATIONS`).
    - `edges.py` — conditional routers.
    - `tools.py` — the CRM tool set (`CRM_TOOLS`).
    - `kg.py` — background knowledge-graph extraction.
  - `memory.py`: Conversation persistence and history compaction.

### Frontend (`/frontend`)
- `app/`: Next.js App Router pages.
  - `(auth)/register`, `/`: Authentication pages.
  - `dashboard/`: KPI metrics and charts.
  - `opportunities/`: Sales pipeline Kanban board.
  - `contacts/`, `tasks/`, `reports/`: Data tables and management views.
- `components/`: Reusable React components (e.g., `Sidebar.tsx`).
- `lib/`: Utility functions (`api.ts` for Axios configuration, `cache.ts`, etc.).
- `public/`: Static assets, PWA manifest, and service workers.

---

## 4. Data Models & Schema

The application uses SQLAlchemy ORM. Key tables include:

- **Users (`users`)**: Stores authentication credentials, roles, and integration tokens (Google API, WhatsApp).
- **Contacts (`contacts`)**: Customer details (name, email, phone, company) linked to a User.
- **Opportunities (`opportunities`)**: Sales deals with values, stages (`lead`, `qualified`, `proposal`, `won`, `lost`), and expected close dates.
- **Tasks (`tasks`)**: Action items with statuses (`pending`, `in_progress`, `completed`), priorities, and due dates.
- **Activities (`activities`)**: Interaction logs (calls, emails, meetings).
- **Emails (`emails`)**: Synced Gmail threads and messages.
- **WhatsAppPhoneNumber (`whatsapp_phone_numbers`)** & **TelegramBot (`telegram_bots`)**: Integration credentials for messaging platforms.
- **AgentSession (`agent_sessions`)**: Stores conversational state and history for LangGraph.

---

## 5. Key Classes and Functions

### AI Agent Workflow (`backend/agents/graph/`)
The agent is a LangGraph workflow `gatekeeper -> (manager <-> worker)* -> END`, with a `force_response` fallback when the tool loop is capped:

- `gatekeeper_node(state)` (`nodes.py`): Intent router. Fast-paths simple greetings, otherwise calls the LLM to set `agent_loop` (route to the manager) and `contains_knowledge` (trigger background KG extraction).
- `manager_node(state)` (`nodes.py`): Planner + conversational agent. Either answers directly or emits OpenAI tool calls for the worker.
- `worker_node(state)` (`nodes.py`): Execution engine. Runs each tool call against `CRM_TOOLS`, appends tool results, and increments the loop counter.
- `force_response_node(state)` (`nodes.py`): Produces a final, tool-free answer once `MAX_TOOL_ITERATIONS` is reached — guaranteeing the loop terminates.
- `process_whatsapp_message(message_data)` / `process_telegram_message(message_data)` (`cs_agent.py`): Channel entry points that share one pipeline; they initialize the state, stream the graph (sending the gatekeeper's preliminary reply via an optional callback), persist the turn, and return the AI's response.

### Schema Management
- `Base.metadata.create_all()` (in `main.py`): Creates any missing tables from the ORM models on startup.
- `run_migrations()` (in `database.py`): Database-agnostic additive column migrations (via `sqlalchemy.inspect`) for databases that predate newer columns. A no-op on a freshly created database; works on both SQLite and PostgreSQL.

---

## 6. Dependency Relationships

### Backend Dependencies (`requirements.txt`)
- **FastAPI / Uvicorn**: Core web framework and ASGI server.
- **SQLAlchemy**: Database ORM (SQLite by default; `psycopg2-binary` can be enabled for PostgreSQL).
- **LangGraph / LangChain Core**: Orchestration framework for the multi-actor LLM agent.
- **OpenAI**: Client SDK used to interface with OpenRouter and Ilmu AI LLMs.
- **PyJWT / Passlib**: Authentication and password hashing.
- **python-dotenv**: Environment variable management.

### Frontend Dependencies (`package.json`)
- **Next.js 14 / React 18**: Core UI framework.
- **Tailwind CSS**: Utility-first CSS styling.
- **@dnd-kit/core**: Provides accessible drag-and-drop mechanics for the Opportunities Kanban board.
- **react-data-table-component**: Renders sortable, paginated tables for Contacts and Tasks.
- **Axios**: HTTP client for API communication.
- **next-pwa**: Generates service workers for offline caching and "Install App" capabilities.

---

## 7. Setup & Running Instructions

### Prerequisites
- Python 3.13
- Node.js 18+
- No database server required (SQLite by default; PostgreSQL optional)

### 1. Database Setup
No setup is needed for the default SQLite database — it is created automatically
on first run. Create a `.env` file in the `backend/` directory for API keys (and,
optionally, a PostgreSQL URL):
```env
# Optional — defaults to a local SQLite file when omitted
DATABASE_URL=sqlite:///./um_crm.db
ILMU_API_KEY=your_api_key
```

### 2. Running the Backend
```bash
cd backend
uv venv --python 3.13
source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
python -m uvicorn main:app --reload
```
*The API will run on http://localhost:8000. Tables are auto-created on the first run.*

**Demo Data Seeding:**
```bash
python seed_demo.py --email demo@example.com --password Passw0rd! --reset-all --force
```

### 3. Running the Frontend
```bash
cd frontend
npm install
npm run dev
```
*The UI will be accessible at http://localhost:3000.*

### 4. PWA Production Build (For offline/install testing)
```bash
cd frontend
npm run build
npm start
```
*Open in Chrome to access the "Install app" feature.*
