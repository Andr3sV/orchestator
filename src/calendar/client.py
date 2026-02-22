"""Google Calendar API client: list events for today or a given date."""

from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.calendar.auth import get_credentials
from src.config import get_settings


def _parse_event_time(ev: dict, key: str) -> str:
    """Extract time string from event start/end (dateTime or date)."""
    val = ev.get(key, {})
    if "dateTime" in val:
        # ISO format; we want HH:MM
        dt_str = val["dateTime"]
        if "T" in dt_str:
            return dt_str.split("T")[1][:5]  # HH:MM
        return "?"
    if "date" in val:
        return val["date"]
    return "?"


def get_calendar_client():
    """Build Calendar API service or None if not configured."""
    creds = get_credentials()
    if not creds:
        return None
    service = build("calendar", "v3", credentials=creds)
    return service


def get_events_today() -> list[dict]:
    """
    Return events for today in the configured timezone.
    Each event: {"start": "HH:MM", "end": "HH:MM", "summary": str}
    """
    s = get_settings()
    tz = ZoneInfo(s.google_timezone)
    now = datetime.now(tz)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return get_events_range(start, end, tz)


def get_events(date_str: str) -> list[dict]:
    """
    Return events for the given date (YYYY-MM-DD) in configured timezone.
    """
    s = get_settings()
    tz = ZoneInfo(s.google_timezone)
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return []
    start = datetime.combine(d, datetime.min.time(), tzinfo=tz)
    end = start + timedelta(days=1)
    return get_events_range(start, end, tz)


def get_events_for_range(start_date_str: str, end_date_str: str) -> list[dict]:
    """
    Return events between start_date and end_date (inclusive).
    Dates in YYYY-MM-DD format; uses configured timezone.
    """
    s = get_settings()
    tz = ZoneInfo(s.google_timezone)
    try:
        start_d = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_d = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        return []
    time_min = datetime.combine(start_d, datetime.min.time(), tzinfo=tz)
    time_max = datetime.combine(end_d, datetime.min.time(), tzinfo=tz) + timedelta(days=1)
    return get_events_range(time_min, time_max, tz)


def get_events_range(
    time_min: datetime,
    time_max: datetime,
    tz: ZoneInfo,
) -> list[dict]:
    """Fetch events between time_min and time_max; return list of dicts."""
    service = get_calendar_client()
    if not service:
        return []
    cal_id = get_settings().google_calendar_id
    try:
        events_result = (
            service.events()
            .list(
                calendarId=cal_id,
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
    except HttpError:
        return []
    events = events_result.get("items", [])
    out = []
    for ev in events:
        start_str = _parse_event_time(ev, "start")
        end_str = _parse_event_time(ev, "end")
        summary = ev.get("summary", "No title")
        out.append({"start": start_str, "end": end_str, "summary": summary})
    return out
