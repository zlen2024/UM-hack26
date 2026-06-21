"""Shared CRM service layer.

Single source of truth for create/read/update/delete and reporting logic. Every
function takes an explicit ``db`` session and ``user_id`` and returns plain JSON-
serializable values, so it can be reused by the REST routes, the LangGraph agent
tools, and the `/api/agent/execute` registry alike.
"""

from . import activities, contacts, opportunities, reports, tasks

__all__ = ["activities", "contacts", "opportunities", "reports", "tasks"]
