"""LangGraph orchestrator: router + copy, strategy, calendar nodes, with Opik tracing."""

from langgraph.graph import StateGraph, START, END
from opik.integrations.langchain import OpikTracer, track_langgraph

from src.graph.state import GraphState
from src.graph.nodes.router import router_node
from src.graph.nodes.copy import copy_node
from src.graph.nodes.strategy import strategy_node
from src.graph.nodes.calendar import calendar_node
from src.graph.nodes.email import email_node


def _build_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("router", router_node)
    workflow.add_node("copy", copy_node)
    workflow.add_node("strategy", strategy_node)
    workflow.add_node("calendar", calendar_node)
    workflow.add_node("email", email_node)

    workflow.add_edge(START, "router")

    def route_after_router(state: GraphState):
        r = state.get("route") or "strategy"
        return r

    workflow.add_conditional_edges(
        "router",
        route_after_router,
        {"copy": "copy", "strategy": "strategy", "calendar": "calendar", "email": "email"},
    )
    workflow.add_edge("copy", END)
    workflow.add_edge("strategy", END)
    workflow.add_edge("calendar", END)
    workflow.add_edge("email", END)

    return workflow.compile()


def get_app():
    """Return the compiled LangGraph app with Opik tracing enabled."""
    app = _build_graph()
    opik_tracer = OpikTracer(
        project_name="orchestator-telegram",
        metadata={"version": "0.1.0"},
    )
    app = track_langgraph(app, opik_tracer)
    return app
