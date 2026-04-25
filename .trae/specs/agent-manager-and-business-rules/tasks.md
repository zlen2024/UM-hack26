# Tasks
- [x] Task 1: Check and Verify Business Rules Injection
  - [x] SubTask 1.1: Verify if `get_business_rule` is correctly injected in `cs_agent.py` and `manager_node` system prompt.
  - [x] SubTask 1.2: Check if endpoints for creating/updating Business Rules exist (if not, build them in `backend/routes/business_rules.py`).

- [x] Task 2: Implement Chat Messages Endpoint
  - [x] SubTask 2.1: Add an endpoint in FastAPI backend to fetch all customer messages from the DB (e.g. `GET /api/messages`).
  - [x] SubTask 2.2: Ensure the endpoint returns sender details (name, phone) and the message text.

- [x] Task 3: Update Message Webhook Context
  - [x] SubTask 3.1: Modify `chatery.py` and `whatsapp.py` webhook processing to explicitly include the sender's phone number and name in the agent payload.
  - [x] SubTask 3.2: Update `cs_agent.py`'s `AgentState` and the initial system prompt to ensure the name and phone number stick to the context.
  - [x] SubTask 3.3: Pass `contact_name` and `phone` to `information_extractor_node` to improve Knowledge Graph accuracy.

- [x] Task 4: Frontend - Update Sidebar Route
  - [x] SubTask 4.1: Find the `div` in the sidebar containing "Coming soon".
  - [x] SubTask 4.2: Replace it with a Link routing to `/agent-manager` (or equivalent framework routing).

- [x] Task 5: Frontend - Create Agent Manager Page
  - [x] SubTask 5.1: Create a new page component for `Agent Manager`.
  - [x] SubTask 5.2: Create tabs/sections for "Knowledge Graph", "Chat Messages", and "Business Rules".
  - [x] SubTask 5.3: Integrate the existing Knowledge Graph component into the tab.

- [x] Task 6: Frontend - Create Business Rules & Chat Messages Views
  - [x] SubTask 6.1: Build the UI to display and update Business Rules. Connect to the backend API.
  - [x] SubTask 6.2: Build the UI to fetch and display all customer messages. Connect to the backend API.

# Task Dependencies
- [Task 5] depends on [Task 4]
- [Task 6] depends on [Task 1] and [Task 2]
- [Task 3] is independent and can run parallel to frontend tasks.