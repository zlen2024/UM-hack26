# UM CRM - Code Wiki

## 1. Executive Summary

**UM CRM** is a full-stack Customer Relationship Management (CRM) application designed for sales teams, account managers, and business development professionals. It facilitates the management of sales pipelines, contacts, tasks, and team collaboration.

A standout feature of UM CRM is its integrated **AI Customer Service Agent**, powered by LangGraph. This agent handles customer queries via multiple channels (WhatsApp, Telegram, Chatery) and can autonomously execute CRM tasks (like creating contacts or logging activities) by routing intents through an intelligent gatekeeper-manager-worker pipeline.

---

## 2. Architecture Overview

The project follows a decoupled client-server architecture:

- **Frontend (Client)**: Built with **Next.js 14** (App Router) and React. Uses **Tailwind CSS** for styling, **@dnd-kit** for Kanban board drag-and-drop interactions, and **next-pwa** for Progressive Web App capabilities.
- **Backend (Server)**: Built with **FastAPI** (Python 3.13). Exposes RESTful APIs for the frontend and webhook endpoints for third-party integrations.
- **Database**: Uses **PostgreSQL** (configured via SQLAlchemy ORM).
- **AI Agent Layer**: Uses **LangGraph** to build a stateful, multi-actor agent workflow. It leverages LLMs (via OpenRouter or Ilmu AI) to parse natural language into CRM tool executions.

### High-Level Data Flow
1. **User Interaction**: Users interact with the Next.js frontend (e.g., moving a deal on the Kanban board).
2. **API Request**: The frontend sends an authenticated HTTP request (JWT) to the FastAPI backend.
3. **Business Logic**: The backend processes the request using SQLAlchemy to query/update the PostgreSQL database.
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
  - `cs_agent.py`: The primary Customer Service AI agent workflow (Gatekeeper -> Manager -> Worker).
  - `graph/`: Contains tools and graph state definitions for LangGraph.

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

### AI Agent Workflow (`backend/agents/cs_agent.py`)
The AI agent uses a triad-node LangGraph structure to prevent infinite loops and improve tool execution reliability:

- `gatekeeper_node(state)`: An intent router. Checks if the user's message is a simple greeting (fast-path) or requires complex backend processing. Sets an `agent_loop` flag.
- `manager_node(state)`: The workflow planner. Analyzes the intent and determines the exact sequence of CRM tools (e.g., `create_contact`, `list_opportunities`) needed. Outputs a structured JSON list of tasks.
- `worker_node(state)`: The execution engine. Iterates through the tasks provided by the manager, invoking the corresponding Python tools (`CRM_TOOLS`) and returning the results to the state.
- `process_whatsapp_message(message_data)` / `process_telegram_message(message_data)`: Entry functions that take incoming webhook payloads, initialize the LangGraph state, invoke the graph, and return the AI's response string.

### Backend Routing
- `ensure_whatsapp_table()`, `ensure_user_columns()` (in `main.py`): Lightweight programmatic schema migrations executed on startup to ensure new features have required database columns without needing a full migration tool like Alembic.

---

## 6. Dependency Relationships

### Backend Dependencies (`requirements.txt`)
- **FastAPI / Uvicorn**: Core web framework and ASGI server.
- **SQLAlchemy / psycopg2-binary**: Database ORM and PostgreSQL adapter.
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
- PostgreSQL 16+

### 1. Database Setup
Ensure PostgreSQL is running. Create a `.env` file in the `backend/` directory:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/um_crm
OPENROUTER_API_KEY=your_api_key
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
