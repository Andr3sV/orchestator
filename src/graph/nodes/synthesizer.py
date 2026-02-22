"""Synthesizer node: turn agent outputs into one reply with personality (alma)."""

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from src.agents.llm import get_llm
from src.agents.prompt_loader import get_system_prompt
from src.graph.state import GraphState


def _build_synthesis_input(state: GraphState) -> str:
    """Build a single text summary of agent outputs for the synthesizer LLM (current turn only)."""
    messages = state.get("messages") or []

    # Last user message index: so we use current request and only current-turn agent outputs
    last_user_idx = -1
    for i in range(len(messages) - 1, -1, -1):
        m = messages[i]
        if hasattr(m, "content") and m.content and not isinstance(m, AIMessage):
            last_user_idx = i
            break
    user_msg = (
        str(messages[last_user_idx].content).strip()
        if last_user_idx >= 0 and hasattr(messages[last_user_idx], "content")
        else ""
    )

    # Only AIMessages after the last user message (current turn outputs)
    parts = [
        str(m.content).strip()
        for m in messages[last_user_idx + 1 :]
        if isinstance(m, AIMessage) and m.content
    ]
    if state.get("calendar_events"):
        events = state["calendar_events"]
        lines = [f"- {e.get('start', '?')}–{e.get('end', '?')}: {e.get('summary', 'No title')}" for e in events]
        parts.append("Calendar events:\n" + "\n".join(lines))
    draft = state.get("email_draft")
    if draft and isinstance(draft, dict) and draft.get("to"):
        parts.append(
            f"Email draft to confirm: To={draft.get('to')}, Subject={draft.get('subject')}, Body={draft.get('body', '')}"
        )
    base = "User asked: " + (user_msg or "(no message)")
    if not parts:
        return base
    return base + "\n\nExpert team outputs:\n" + "\n---\n".join(parts)


def synthesizer_node(state: GraphState) -> dict:
    """Produce one AIMessage that synthesizes all agent outputs with personality."""
    synthesis_input = _build_synthesis_input(state)
    llm = get_llm()
    response = llm.invoke([
        SystemMessage(content=get_system_prompt("synthesizer")),
        HumanMessage(content=synthesis_input),
    ])
    content = (response.content or "").strip() or "No pude generar una respuesta. Intenta de nuevo."
    return {"messages": [AIMessage(content=content)]}
