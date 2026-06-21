"""Conditional routing for the customer-service agent graph."""

import logging

from langgraph.graph import END

from .nodes import MAX_TOOL_ITERATIONS
from .state import AgentState

logger = logging.getLogger("CS_Agent_Workflow")


def gatekeeper_router(state: AgentState) -> str:
    """Continue to the manager only when the gatekeeper asked for the agent loop."""
    if state.get("gatekeeper_response", {}).get("agent_loop", False):
        logger.info("[ROUTER] Gatekeeper -> manager")
        return "manager"
    logger.info("[ROUTER] Gatekeeper -> END")
    return END


def manager_router(state: AgentState) -> str:
    """Route the manager's output: run tools, force a final answer, or finish."""
    messages = state.get("messages", [])
    if not messages or not messages[-1].get("tool_calls"):
        logger.info("[ROUTER] Manager -> END")
        return END

    if state.get("tool_iterations", 0) >= MAX_TOOL_ITERATIONS:
        logger.info("[ROUTER] Manager -> force_response (tool-loop cap)")
        return "force_response"

    logger.info("[ROUTER] Manager -> worker")
    return "worker"
