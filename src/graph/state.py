"""LangGraph state for the marketing team orchestrator."""

from typing import Annotated, Literal, TypedDict

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


RouteKind = Literal["copy", "strategy", "calendar", "email"]


class EmailDraft(TypedDict):
    """Structured draft for user confirmation before sending."""

    to: str
    subject: str
    body: str


class GraphState(TypedDict):
    """State passed through the graph."""

    messages: Annotated[list[BaseMessage], add_messages]
    route: RouteKind | None
    plan: list[RouteKind] | None
    plan_index: int | None
    calendar_events: list[dict] | None
    email_draft: EmailDraft | None


def create_initial_state(user_message: str) -> GraphState:
    """Build initial state from the user's text message."""
    from langchain_core.messages import HumanMessage

    return GraphState(
        messages=[HumanMessage(content=user_message)],
        route=None,
        plan=None,
        plan_index=None,
        calendar_events=None,
        email_draft=None,
    )
