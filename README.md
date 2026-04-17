# UM CRM - Simple CRM Application

A full-stack CRM application built with FastAPI (backend) and Next.js (frontend).

## Prerequisites

- Python 3.9+
- Node.js 18+
- uv (Python package manager)

## Setup & Running

### Backend (FastAPI)

1. Navigate to the backend folder:
   ```powershell
   cd backend
   ```

2. Create a virtual environment and install dependencies:
   ```powershell
   uv venv
   .\venv\Scripts\Activate
   uv pip install -r requirements.txt
   ```

3. Run the backend server:
   ```powershell
   uvicorn main:app --reload
   ```

   The API will be available at http://localhost:8000

### Frontend (Next.js)

1. Navigate to the frontend folder:
   ```powershell
   cd frontend
   ```

2. Install dependencies:
   ```powershell
   npm install
   ```

3. Run the development server:
   ```powershell
   npm run dev
   ```

   The application will be available at http://localhost:3000

## Features

- **User Authentication**: Register, login with JWT tokens
- **Sales Pipeline**: Kanban-style board with stage management
- **Contact Management**: Create, search, and manage contacts
- **Task Management**: Track tasks with status and priorities
- **Reports**: Dashboard with key metrics and analytics
- **Integrations**: UI placeholders for email/calendar integration

## API Endpoints

- `/api/auth/*` - Authentication (register, login, me)
- `/api/contacts/*` - Contact management (CRUD)
- `/api/opportunities/*` - Sales pipeline (CRUD, stage update)
- `/api/tasks/*` - Task management (CRUD, status update)
- `/api/activities/*` - Activity tracking
- `/api/reports/*` - Reports and analytics (dashboard, pipeline, contacts)
- `/api/users/*` - User management