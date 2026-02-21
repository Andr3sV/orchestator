"""Calendar agent node: fetch events and summarize in natural language."""

from langchain_core.messages import SystemMessage, AIMessage, HumanMessage

from src.agents.llm import get_llm
from src.agents.prompts import CALENDAR_SYSTEM
from src.graph.state import GraphState
from src.graph.tools.calendar import get_events_today, get_events


def _format_events(events: list[dict]) -> str:
    if not events:
        return "No events found."
    lines = [f"- {e.get('start', '?')}–{e.get('end', '?')}: {e.get('summary', 'No title')}" for e in events]
    return "\n".join(lines)


def calendar_node(state: GraphState) -> dict:
    """Fetch calendar events (today or from context) and generate summary."""
    events: list[dict] = []
    # Prefer already-fetched events (e.g. from tools run elsewhere); otherwise fetch today
    if state.get("calendar_events") is not None:
        events = state["calendar_events"] or []
    else:
        events = get_events_today()
    events_text = _format_events(events)
    llm = get_llm()
    # Build context: user asked about calendar, here are the events
    user_content = (
        state["messages"][-1].content
        if state["messages"]
        else "What do I have today?"
    )
    if isinstance(user_content, list):
        user_content = str(user_content)
    prompt = f"User asked: {user_content}\n\nEvents:\n{events_text}"
    messages = [
        SystemMessage(content=CALENDAR_SYSTEM),
        HumanMessage(content=prompt),
    ]
    response = llm.invoke(messages)
    return {"messages": [AIMessage(content=response.content or "")], "calendar_events": events}
