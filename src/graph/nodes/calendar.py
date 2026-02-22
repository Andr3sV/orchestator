"""Calendar agent node: fetch events and summarize in natural language."""

from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_core.messages import SystemMessage, AIMessage, HumanMessage

from src.agents.llm import get_llm
from src.agents.prompts import CALENDAR_SYSTEM
from src.config import get_settings
from src.graph.state import GraphState
from src.graph.nodes.calendar_date_resolver import (
    resolve_calendar_request,
    format_period_label,
)
from src.graph.tools.calendar import get_events_today, get_events, get_events_for_range


def _format_events(events: list[dict]) -> str:
    if not events:
        return "No events found."
    lines = [f"- {e.get('start', '?')}–{e.get('end', '?')}: {e.get('summary', 'No title')}" for e in events]
    return "\n".join(lines)


def calendar_node(state: GraphState) -> dict:
    """Fetch calendar events for the resolved period (today, tomorrow, range, etc.) and generate summary."""
    user_content = (
        state["messages"][-1].content
        if state["messages"]
        else "What do I have today?"
    )
    if isinstance(user_content, list):
        user_content = str(user_content)

    tz = ZoneInfo(get_settings().google_timezone)
    result = resolve_calendar_request(user_content, tz)

    if result[0] == "single":
        single_date = result[1]
        today = datetime.now(tz).date()
        if single_date == today:
            events = get_events_today()
        else:
            events = get_events(single_date.strftime("%Y-%m-%d"))
    else:
        start_d, end_d = result[1], result[2]
        events = get_events_for_range(
            start_d.strftime("%Y-%m-%d"),
            end_d.strftime("%Y-%m-%d"),
        )

    period_label = format_period_label(result, tz)
    events_text = _format_events(events)
    llm = get_llm()
    prompt = f"User asked: {user_content}\n\nRequested period: {period_label}\n\nEvents:\n{events_text}"
    messages = [
        SystemMessage(content=CALENDAR_SYSTEM),
        HumanMessage(content=prompt),
    ]
    response = llm.invoke(messages)
    return {"messages": [AIMessage(content=response.content or "")], "calendar_events": events}
