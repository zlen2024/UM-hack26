from typing import Dict, Callable, Any, List
from . import contacts, opportunities, tasks, activities, reports


FUNCTION_REGISTRY: Dict[str, Dict[str, Any]] = {
    "create_contact": {
        "handler": contacts.create_contact,
        "required_args": ["name"],
        "optional_args": ["email", "phone", "company", "notes"],
        "description": "Create a new contact",
    },
    "get_contact": {
        "handler": contacts.get_contact,
        "required_args": ["id"],
        "optional_args": [],
        "description": "Get a contact by ID",
    },
    "list_contacts": {
        "handler": contacts.list_contacts,
        "required_args": [],
        "optional_args": ["search"],
        "description": "List all contacts with optional search",
    },
    "update_contact": {
        "handler": contacts.update_contact,
        "required_args": ["id"],
        "optional_args": ["name", "email", "phone", "company", "notes"],
        "description": "Update a contact",
    },
    "delete_contact": {
        "handler": contacts.delete_contact,
        "required_args": ["id"],
        "optional_args": [],
        "description": "Delete a contact",
    },
    "create_opportunity": {
        "handler": opportunities.create_opportunity,
        "required_args": ["title", "value"],
        "optional_args": ["stage", "contact_id", "assigned_to", "expected_close_date"],
        "description": "Create a new opportunity/deal",
    },
    "get_opportunity": {
        "handler": opportunities.get_opportunity,
        "required_args": ["id"],
        "optional_args": [],
        "description": "Get an opportunity by ID",
    },
    "list_opportunities": {
        "handler": opportunities.list_opportunities,
        "required_args": [],
        "optional_args": ["stage", "assigned_to"],
        "description": "List all opportunities with optional filters",
    },
    "update_opportunity": {
        "handler": opportunities.update_opportunity,
        "required_args": ["id"],
        "optional_args": ["title", "value", "stage", "contact_id", "assigned_to", "expected_close_date"],
        "description": "Update an opportunity",
    },
    "update_opportunity_stage": {
        "handler": opportunities.update_opportunity_stage,
        "required_args": ["id", "stage"],
        "optional_args": [],
        "description": "Update opportunity stage (lead, qualified, proposal, won, lost)",
    },
    "delete_opportunity": {
        "handler": opportunities.delete_opportunity,
        "required_args": ["id"],
        "optional_args": [],
        "description": "Delete an opportunity",
    },
    "create_task": {
        "handler": tasks.create_task,
        "required_args": ["title"],
        "optional_args": ["description", "status", "priority", "due_date", "assigned_to", "contact_id", "opportunity_id"],
        "description": "Create a new task",
    },
    "get_task": {
        "handler": tasks.get_task,
        "required_args": ["id"],
        "optional_args": [],
        "description": "Get a task by ID",
    },
    "list_tasks": {
        "handler": tasks.list_tasks,
        "required_args": [],
        "optional_args": ["status", "assigned_to"],
        "description": "List all tasks with optional filters",
    },
    "update_task": {
        "handler": tasks.update_task,
        "required_args": ["id"],
        "optional_args": ["title", "description", "status", "priority", "due_date", "assigned_to", "contact_id", "opportunity_id"],
        "description": "Update a task",
    },
    "update_task_status": {
        "handler": tasks.update_task_status,
        "required_args": ["id", "status"],
        "optional_args": [],
        "description": "Update task status (pending, in_progress, completed)",
    },
    "delete_task": {
        "handler": tasks.delete_task,
        "required_args": ["id"],
        "optional_args": [],
        "description": "Delete a task",
    },
    "create_activity": {
        "handler": activities.create_activity,
        "required_args": ["type"],
        "optional_args": ["description", "contact_id", "opportunity_id", "scheduled_at"],
        "description": "Create a new activity",
    },
    "get_activity": {
        "handler": activities.get_activity,
        "required_args": ["id"],
        "optional_args": [],
        "description": "Get an activity by ID",
    },
    "list_activities": {
        "handler": activities.list_activities,
        "required_args": [],
        "optional_args": ["contact_id", "opportunity_id"],
        "description": "List all activities with optional filters",
    },
    "update_activity": {
        "handler": activities.update_activity,
        "required_args": ["id"],
        "optional_args": ["type", "description", "contact_id", "opportunity_id", "scheduled_at"],
        "description": "Update an activity",
    },
    "delete_activity": {
        "handler": activities.delete_activity,
        "required_args": ["id"],
        "optional_args": [],
        "description": "Delete an activity",
    },
    "get_dashboard": {
        "handler": reports.get_dashboard,
        "required_args": [],
        "optional_args": [],
        "description": "Get dashboard metrics",
    },
    "get_pipeline_report": {
        "handler": reports.get_pipeline_report,
        "required_args": [],
        "optional_args": [],
        "description": "Get pipeline breakdown by stage",
    },
    "get_contact_activity_report": {
        "handler": reports.get_contact_activity_report,
        "required_args": [],
        "optional_args": [],
        "description": "Get contacts with activity counts",
    },
}


def get_function_signature(function_name: str) -> Dict[str, Any]:
    return FUNCTION_REGISTRY.get(function_name, {})


def validate_args(function_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    error = None
    func_info = FUNCTION_REGISTRY.get(function_name)
    if not func_info:
        return {"valid": False, "error": f"Unknown function: {function_name}"}
    for required_arg in func_info["required_args"]:
        if required_arg not in args:
            error = f"Missing required argument: {required_arg}"
            break
    return {"valid": error is None, "error": error}


def list_available_functions() -> List[Dict[str, Any]]:
    return [
        {
            "name": name,
            "required_args": info["required_args"],
            "optional_args": info["optional_args"],
            "description": info["description"],
        }
        for name, info in FUNCTION_REGISTRY.items()
    ]