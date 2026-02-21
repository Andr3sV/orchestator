"""LangGraph state for the marketing team orchestrator."""

from typing import Annotated, Literal, TypedDict

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


RouteKind = Literal["copy", "strategy", "calendar"]


class GraphState(TypedDict):
    """State passed through the graph."""

    messages: Annotated[list[BaseMessage], add_messages]
    route: RouteKind | None
    calendar_events: list[dict] | None


def create_initial_state(user_message: str) -> GraphState:
    """Build initial state from the user's text message."""
    from langchain_core.messages import HumanMessage

    return GraphState(
        messages=[HumanMessage(content=user_message)],
        route=None,
        calendar_events=None,
    )
