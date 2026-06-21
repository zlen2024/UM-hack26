"""Customer-service agent graph package.

Public surface:
- ``build_graph()`` -> a freshly compiled LangGraph app
- ``graph``         -> a module-level compiled instance
- ``AgentState``    -> the graph state type
"""

from langgraph.graph import END, START, StateGraph

from .edges import gatekeeper_router, manager_router
from .nodes import (
    force_response_node,
    gatekeeper_node,
    manager_node,
    worker_node,
)
from .state import AgentState


def build_graph():
    """Build and compile the gatekeeper -> manager <-> worker graph."""
    builder = StateGraph(AgentState)

    builder.add_node("gatekeeper", gatekeeper_node)
    builder.add_node("manager", manager_node)
    builder.add_node("worker", worker_node)
    builder.add_node("force_response", force_response_node)

    builder.add_edge(START, "gatekeeper")
    builder.add_conditional_edges("gatekeeper", gatekeeper_router)
    builder.add_conditional_edges("manager", manager_router)
    builder.add_edge("worker", "manager")
    builder.add_edge("force_response", END)

    return builder.compile()


graph = build_graph()

__all__ = ["build_graph", "graph", "AgentState"]
