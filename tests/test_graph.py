"""Tests for full graph invocation (with mocked LLM or live)."""

import pytest

from src.graph.state import create_initial_state
from src.graph.graph import _build_graph


def test_build_graph_compiles():
    """Graph compiles without Opik (no env needed)."""
    app = _build_graph()
    assert app is not None


@pytest.mark.skip(reason="Requires OPENAI_API_KEY and optional OPIK; run manually")
def test_graph_invoke_calendar():
    """Full invoke for calendar-style message (integration)."""
    from src.graph.graph import get_app
    app = get_app()
    state = create_initial_state("What do I have today?")
    config = {"configurable": {"thread_id": "test-graph-invoke-calendar"}}
    result = app.invoke(state, config=config)
    assert "messages" in result
    assert len(result["messages"]) >= 2  # user + assistant
    last = result["messages"][-1]
    assert hasattr(last, "content")
    assert len(last.content) > 0
