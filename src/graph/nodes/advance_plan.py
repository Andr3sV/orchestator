"""Advance plan node: increment plan_index for next conditional routing."""

from src.graph.state import GraphState


def advance_plan_node(state: GraphState) -> dict:
    """Increment plan_index so the next conditional routes to plan[plan_index] or synthesizer."""
    plan_index = state.get("plan_index", 0) + 1
    return {"plan_index": plan_index}
