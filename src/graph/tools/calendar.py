"""Calendar tools: fetch events from Google Calendar or mock when not configured."""

from src.calendar.client import get_calendar_client, get_events_today as _real_today, get_events as _real_events

_MOCK_EVENTS = [
    {"start": "09:00", "end": "09:30", "summary": "Daily standup"},
    {"start": "14:00", "end": "15:00", "summary": "Client call"},
]


def get_events_today() -> list[dict]:
    """Return events for today from Google Calendar, or mock list if not configured."""
    if get_calendar_client() is not None:
        return _real_today()
    return _MOCK_EVENTS.copy()


def get_events(date: str) -> list[dict]:
    """Return events for the given date (YYYY-MM-DD) from Google Calendar or mock."""
    if get_calendar_client() is not None:
        return _real_events(date)
    return _MOCK_EVENTS.copy()
