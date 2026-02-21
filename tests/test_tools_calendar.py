"""Tests for calendar tools (mock and later real)."""

from src.graph.tools.calendar import get_events_today, get_events


def test_get_events_today_returns_list():
    """get_events_today returns a list of event dicts."""
    events = get_events_today()
    assert isinstance(events, list)
    for e in events:
        assert "start" in e
        assert "end" in e
        assert "summary" in e


def test_get_events_accepts_date():
    """get_events(date) returns list."""
    events = get_events("2025-02-21")
    assert isinstance(events, list)
