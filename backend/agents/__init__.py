# The CRUD/report logic now lives in the shared ``services`` package. These
# re-exports are kept for backwards compatibility.
from services.contacts import (
    create_contact,
    get_contact,
    list_contacts,
    update_contact,
    delete_contact,
)
from services.opportunities import (
    create_opportunity,
    get_opportunity,
    list_opportunities,
    update_opportunity,
    update_opportunity_stage,
    delete_opportunity,
)
from services.tasks import (
    create_task,
    get_task,
    list_tasks,
    update_task,
    update_task_status,
    delete_task,
)
from services.activities import (
    create_activity,
    get_activity,
    list_activities,
    update_activity,
    delete_activity,
)
from services.reports import (
    get_dashboard,
    get_pipeline_report,
    get_contact_activity_report,
)
from .registry import FUNCTION_REGISTRY

__all__ = [
    "create_contact",
    "get_contact",
    "list_contacts",
    "update_contact",
    "delete_contact",
    "create_opportunity",
    "get_opportunity",
    "list_opportunities",
    "update_opportunity",
    "update_opportunity_stage",
    "delete_opportunity",
    "create_task",
    "get_task",
    "list_tasks",
    "update_task",
    "update_task_status",
    "delete_task",
    "create_activity",
    "get_activity",
    "list_activities",
    "update_activity",
    "delete_activity",
    "get_dashboard",
    "get_pipeline_report",
    "get_contact_activity_report",
    "FUNCTION_REGISTRY",
]