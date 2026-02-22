"""Router node: classify user intent into copy, strategy, or calendar."""

from src.agents.llm import get_llm
from src.agents.prompts import ROUTER_SYSTEM
from src.graph.state import GraphState, RouteKind
from langchain_core.messages import SystemMessage

ROUTE_VALUES: list[RouteKind] = ["copy", "strategy", "calendar", "email"]


def router_node(state: GraphState) -> dict:
    """Classify the last user message and set route."""
    messages = state["messages"]
    if not messages:
        return {"route": "strategy"}
    last = messages[-1]
    if not hasattr(last, "content") or not last.content:
        return {"route": "strategy"}
    user_text = last.content if isinstance(last.content, str) else str(last.content)
    llm = get_llm()
    response = llm.invoke([SystemMessage(content=ROUTER_SYSTEM), last])
    raw = (response.content or "").strip().lower()
    route: RouteKind = "strategy"
    for r in ROUTE_VALUES:
        if r in raw or raw == r:
            route = r
            break
    return {"route": route}
