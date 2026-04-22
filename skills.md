---
name: um-crm-mcp
description: "Use the UM CRM MCP server and Zapier integration flow to store per-user keys, inspect CRM tools, and execute CRM actions safely."
category: development
risk: safe
source: custom
date_added: "2026-04-22"
tags: [mcp, crm, zapier, fastapi, nextjs, backend]
tools: [claude, cursor, gemini, codex]
---

# UM CRM MCP

## When to Use This Skill

- User asks to connect the CRM to MCP, Zapier, or an AI agent.
- User needs to store, read, or delete per-user integration keys.
- User asks the agent to call CRM actions like contacts, tasks, opportunities, activities, or reports.

## CRM Flow

1. Authenticate the user through the app.
2. Store the Zapier key in the DB-backed integration credential table.
3. Use backend MCP tools to inspect available CRM functions.
4. Call CRM functions via the MCP server or the `/api/agent` route.
5. Validate the result in the UI or via a direct tool call.

## What Exists in This Repo

- MCP server: `backend/mcp_server.py`
- Integration API: `backend/routes/integrations.py`
- DB table: `integration_credentials` in `backend/models.py`
- Frontend settings: `frontend/app/settings/page.tsx`

## Available MCP Tools

- `crm_list_functions`
- `crm_execute`
- `zapier_status`
- `zapier_save_key`
- `zapier_clear_key`

## Implementation Rules

- Never expose raw secrets in responses.
- Store Zapier keys per `user_id` and `provider`.
- Return connection status and metadata only.
- Reuse the existing CRM function registry rather than duplicating business logic.

## Validation

- Run `python mcp_server.py` from the `backend` directory.
- Confirm `crm_list_functions` returns the CRM catalog.
- Save a Zapier key from Settings.
- Query `zapier_status` to verify the DB row exists.
- Call `/api/agent/functions` to confirm the backend agent route still matches the same function catalog.

## Notes

- This skill follows the Antigravity Awesome Skills `SKILL.md` style.
- Keep it focused on CRM operations, not general-purpose AI agent behavior.