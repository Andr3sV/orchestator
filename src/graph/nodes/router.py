"""Planner node: decide sequence of agents (plan). Replaces single-route router."""

from src.agents.llm import get_llm
from src.agents.prompts import PLANNER_SYSTEM
from src.graph.state import GraphState, RouteKind, get_recent_messages
from langchain_core.messages import SystemMessage

ROUTE_VALUES: list[RouteKind] = ["copy", "strategy", "calendar", "email"]


def _parse_plan(raw: str) -> list[RouteKind]:
    """Parse LLM response into list of RouteKind. Fallback to strategy if invalid."""
    raw = (raw or "").strip().lower().replace(" ", "")
    if not raw:
        return ["strategy"]
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    plan: list[RouteKind] = []
    for p in parts:
        if p in ROUTE_VALUES and p not in plan:
            plan.append(p)
    if not plan:
        return ["strategy"]
    return plan


def planner_node(state: GraphState) -> dict:
    """Decide which agents to run and in what order; set state['plan']."""
    messages = state.get("messages") or []
    if not messages:
        return {"plan": ["strategy"], "plan_index": 0}
    last = messages[-1]
    if not hasattr(last, "content") or not last.content:
        return {"plan": ["strategy"], "plan_index": 0}
    llm = get_llm()
    response = llm.invoke(
        [SystemMessage(content=PLANNER_SYSTEM)] + get_recent_messages(messages)
    )
    raw = (response.content or "").strip()
    plan = _parse_plan(raw)
    return {"plan": plan, "plan_index": 0}
