"""LangGraph orchestrator: planner → agents (as nodes) → advance_plan → synthesizer, with Opik tracing."""

from langgraph.graph import StateGraph, START, END
from opik.integrations.langchain import OpikTracer, track_langgraph

from src.graph.state import GraphState
from src.graph.nodes.router import planner_node
from src.graph.nodes.copy import copy_node
from src.graph.nodes.strategy import strategy_node
from src.graph.nodes.calendar import calendar_node
from src.graph.nodes.email import email_node
from src.graph.nodes.advance_plan import advance_plan_node
from src.graph.nodes.synthesizer import synthesizer_node

AGENT_PATH_MAP: dict[str, str] = {
    "copy": "copy",
    "strategy": "strategy",
    "calendar": "calendar",
    "email": "email",
    "synthesizer": "synthesizer",
}


def _route_after_planner(state: GraphState) -> str:
    """Route to first agent in plan or to synthesizer if plan empty."""
    plan = state.get("plan") or []
    if plan and len(plan) > 0:
        return plan[0]
    return "synthesizer"


def _route_after_advance_plan(state: GraphState) -> str:
    """Route to next agent in plan or to synthesizer if plan done."""
    plan = state.get("plan") or []
    idx = state.get("plan_index", 0)
    if idx < len(plan):
        return plan[idx]
    return "synthesizer"


def _build_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("planner", planner_node)
    workflow.add_node("copy", copy_node)
    workflow.add_node("strategy", strategy_node)
    workflow.add_node("calendar", calendar_node)
    workflow.add_node("email", email_node)
    workflow.add_node("advance_plan", advance_plan_node)
    workflow.add_node("synthesizer", synthesizer_node)

    workflow.add_edge(START, "planner")
    workflow.add_conditional_edges("planner", _route_after_planner, AGENT_PATH_MAP)
    workflow.add_edge("copy", "advance_plan")
    workflow.add_edge("strategy", "advance_plan")
    workflow.add_edge("calendar", "advance_plan")
    workflow.add_edge("email", "advance_plan")
    workflow.add_conditional_edges("advance_plan", _route_after_advance_plan, AGENT_PATH_MAP)
    workflow.add_edge("synthesizer", END)

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
