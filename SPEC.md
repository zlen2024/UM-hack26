# CRM Application Specification

## Project Overview
- **Project Name**: UM CRM
- **Type**: Full-stack Web Application
- **Core Functionality**: A comprehensive CRM system for managing sales pipelines, contacts, tasks, and team collaboration
- **Target Users**: Sales teams, account managers, and business development professionals

## Tech Stack
- **Backend**: FastAPI (Python)
- **Frontend**: Next.js 14 (React, TypeScript)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT tokens with password hashing
- **Styling**: Tailwind CSS

## UI/UX Specification

### Color Palette
- **Primary**: `#2563eb` (Blue 600)
- **Primary Dark**: `#1d4ed8` (Blue 700)
- **Secondary**: `#64748b` (Slate 500)
- **Accent**: `#10b981` (Emerald 500)
- **Background**: `#f8fafc` (Slate 50)
- **Surface**: `#ffffff` (White)
- **Text Primary**: `#1e293b` (Slate 800)
- **Text Secondary**: `#64748b` (Slate 500)
- **Border**: `#e2e8f0` (Slate 200)
- **Error**: `#ef4444` (Red 500)
- **Warning**: `#f59e0b` (Amber 500)
- **Success**: `#10b981` (Emerald 500)

### Typography
- **Font Family**: Inter (system fallback: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto)
- **Headings**:
  - H1: 32px, font-weight 700
  - H2: 24px, font-weight 600
  - H3: 20px, font-weight 600
- **Body**: 14px, font-weight 400
- **Small**: 12px, font-weight 400

### Layout Structure
- **Sidebar**: 240px fixed width, collapsible to 64px
- **Header**: 64px height with user menu
- **Main Content**: Fluid width with max-width 1400px
- **Cards**: 16px padding, 8px border-radius, subtle shadow

### Responsive Breakpoints
- Mobile: < 768px (sidebar hidden, hamburger menu)
- Tablet: 768px - 1024px (sidebar collapsed)
- Desktop: > 1024px (full sidebar)

## Database Schema

### Users Table
- id: INTEGER PRIMARY KEY
- email: VARCHAR UNIQUE
- password_hash: VARCHAR
- full_name: VARCHAR
- role: VARCHAR (admin, user)
- created_at: DATETIME
- updated_at: DATETIME

### Contacts Table
- id: INTEGER PRIMARY KEY
- user_id: INTEGER (FK to Users)
- name: VARCHAR
- email: VARCHAR
- phone: VARCHAR
- company: VARCHAR
- notes: TEXT
- created_at: DATETIME
- updated_at: DATETIME

### Opportunities Table
- id: INTEGER PRIMARY KEY
- user_id: INTEGER (FK to Users)
- title: VARCHAR
- value: DECIMAL
- stage: VARCHAR (lead, qualified, proposal, won, lost)
- contact_id: INTEGER (FK to Contacts)
- assigned_to: INTEGER (FK to Users)
- expected_close_date: DATE
- created_at: DATETIME
- updated_at: DATETIME

### Tasks Table
- id: INTEGER PRIMARY KEY
- user_id: INTEGER (FK to Users)
- title: VARCHAR
- description: TEXT
- status: VARCHAR (pending, in_progress, completed)
- priority: VARCHAR (low, medium, high)
- due_date: DATETIME
- assigned_to: INTEGER (FK to Users)
- contact_id: INTEGER (FK to Contacts, nullable)
- opportunity_id: INTEGER (FK to Opportunities, nullable)
- created_at: DATETIME
- updated_at: DATETIME

### Activities Table
- id: INTEGER PRIMARY KEY
- user_id: INTEGER (FK to Users)
- type: VARCHAR (call, email, meeting, note)
- description: TEXT
- contact_id: INTEGER (FK to Contacts)
- opportunity_id: INTEGER (FK to Opportunities, nullable)
- scheduled_at: DATETIME
- created_at: DATETIME

## API Endpoints

### Authentication
- POST /api/auth/register - Register new user
- POST /api/auth/login - Login user
- POST /api/auth/logout - Logout user
- POST /api/auth/refresh - Refresh token
- POST /api/auth/forgot-password - Request password reset
- POST /api/auth/reset-password - Reset password with token

### Contacts
- GET /api/contacts - List all contacts (with search/filter)
- GET /api/contacts/{id} - Get contact details
- POST /api/contacts - Create new contact
- PUT /api/contacts/{id} - Update contact
- DELETE /api/contacts/{id} - Delete contact

### Opportunities
- GET /api/opportunities - List all opportunities
- GET /api/opportunities/{id} - Get opportunity details
- POST /api/opportunities - Create new opportunity
- PUT /api/opportunities/{id} - Update opportunity
- PUT /api/opportunities/{id}/stage - Move to different stage
- DELETE /api/opportunities/{id} - Delete opportunity

### Tasks
- GET /api/tasks - List all tasks
- GET /api/tasks/{id} - Get task details
- POST /api/tasks - Create new task
- PUT /api/tasks/{id} - Update task
- PUT /api/tasks/{id}/status - Update task status
- DELETE /api/tasks/{id} - Delete task

### Activities
- GET /api/activities - List all activities
- GET /api/activities/{id} - Get activity details
- POST /api/activities - Create new activity
- PUT /api/activities/{id} - Update activity
- DELETE /api/activities/{id} - Delete activity

### Reports
- GET /api/reports/pipeline - Sales pipeline report
- GET /api/reports/contacts - Contact activity report
- GET /api/reports/dashboard - Dashboard metrics

### Users
- GET /api/users - List all team members
- GET /api/users/{id} - Get user details

## Pages Structure

### Frontend Pages
1. `/` - Landing/Login page
2. `/register` - Registration page
3. `/dashboard` - Main dashboard with KPIs
4. `/contacts` - Contact list and management
5. `/contacts/[id]` - Contact detail page
6. `/opportunities` - Sales pipeline view
7. `/opportunities/[id]` - Opportunity detail page
8. `/tasks` - Task list and management
9. `/tasks/[id]` - Task detail page
10. `/reports` - Reports and analytics
11. `/settings` - User settings
12. `/calendar` - Calendar view (optional integration)

## Features

### Authentication
- Email/password registration with validation
- JWT-based authentication
- Password hashing with bcrypt
- Token refresh mechanism
- Protected routes

### Sales Pipeline
- Kanban-style board view
- Drag-and-drop stage changes
- Filter by assignee, value range, date
- Pipeline metrics (total value, conversion rates)

### Contact Management
- CRUD operations
- Search by name, email, company
- Filter by tags/segments
- Activity timeline per contact
- Document attachment support (base64 storage for simplicity)

### Task Management
- Kanban and list views
- Filter by status, assignee, due date
- Priority indicators
- Deadline reminders
- Related to contacts/opportunities

### Reporting
- Pipeline overview chart
- Win/loss analysis
- Team performance metrics
- Revenue forecasting
- Activity summary

### Email/Calendar Integration (Mock)
- OAuth connection UI (placeholder)
- Sync status indicators
- Mock sync functionality

## Acceptance Criteria

### Authentication
- [ ] Users can register with email and password
- [ ] Users can login and receive JWT token
- [ ] Protected routes redirect to login
- [ ] Password is securely hashed

### Sales Pipeline
- [ ] Users can create, edit, delete opportunities
- [ ] Opportunities display in kanban board
- [ ] Stage changes persist to database
- [ ] Opportunities can be assigned to users

### Contacts
- [ ] Users can create, edit, delete contacts
- [ ] Search returns matching contacts
- [ ] Contact details show activity history

### Tasks
- [ ] Users can create, edit, delete tasks
- [ ] Task status can be updated
- [ ] Tasks can be filtered by status
- [ ] Due dates are displayed correctly

### Reports
- [ ] Dashboard shows key metrics
- [ ] Pipeline report shows stage distribution
- [ ] Activity report shows recent interactions

### UI/UX
- [ ] Responsive on mobile, tablet, desktop
- [ ] Consistent styling across pages
- [ ] Loading states for async operations
- [ ] Error handling with user feedback
