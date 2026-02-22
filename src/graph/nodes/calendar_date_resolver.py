"""Resolve natural language date expressions to a single day or a date range."""

import re
from datetime import date, datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

# Month names: Spanish (lower) and English (lower) for "D de M" / "D M" parsing
_MONTH_NAMES_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}
_MONTH_NAMES_EN = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}


def _normalize(s: str) -> str:
    """Lowercase, strip, and normalize some accents for matching."""
    s = (s or "").strip().lower()
    # Simple accent folding for common Spanish
    replacements = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n"}
    for a, b in replacements.items():
        s = s.replace(a, b)
    return s


def _today_in_tz(tz: ZoneInfo) -> date:
    return datetime.now(tz).date()


def _parse_concrete_date(text: str, tz: ZoneInfo) -> date | None:
    """Try to parse YYYY-MM-DD or 'D de M' / 'D M' (Spanish/English). Returns None if no match."""
    text = _normalize(text)
    # YYYY-MM-DD
    m = re.search(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b", text)
    if m:
        try:
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            return date(y, mo, d)
        except ValueError:
            pass
    # D de M or D M (Spanish)
    for name, num in _MONTH_NAMES_ES.items():
        pattern = rf"\b(\d{{1,2}})\s+de\s+{re.escape(name)}\b"
        m = re.search(pattern, text)
        if m:
            try:
                day = int(m.group(1))
                year = _today_in_tz(tz).year
                return date(year, num, day)
            except ValueError:
                pass
        pattern = rf"\b(\d{{1,2}})\s+{re.escape(name)}\b"
        m = re.search(pattern, text)
        if m:
            try:
                day = int(m.group(1))
                year = _today_in_tz(tz).year
                return date(year, num, day)
            except ValueError:
                pass
    # D M (English): "march 15", "15 march"
    for name, num in _MONTH_NAMES_EN.items():
        pattern = rf"\b(\d{{1,2}})\s+{re.escape(name)}\b"
        m = re.search(pattern, text)
        if m:
            try:
                day = int(m.group(1))
                year = _today_in_tz(tz).year
                return date(year, num, day)
            except ValueError:
                pass
        pattern = rf"\b{re.escape(name)}\s+(\d{{1,2}})\b"
        m = re.search(pattern, text)
        if m:
            try:
                day = int(m.group(1))
                year = _today_in_tz(tz).year
                return date(year, num, day)
            except ValueError:
                pass
    return None


def resolve_calendar_request(
    user_message: str,
    tz: ZoneInfo,
) -> tuple[Literal["single"], date] | tuple[Literal["range"], date, date]:
    """
    Resolve user message to a single day or a date range.
    Returns ("single", date) or ("range", start_date, end_date).
    Unrecognized input falls back to today ("single", today).
    """
    msg = _normalize(user_message or "")
    today = _today_in_tz(tz)

    # Single day: today
    if any(x in msg for x in ("hoy", "today", "today's")):
        return ("single", today)

    # Single day: tomorrow
    if any(x in msg for x in ("manana", "mañana", "tomorrow")):
        return ("single", today + timedelta(days=1))

    # Single day: day after tomorrow
    if any(x in msg for x in ("pasado manana", "pasado mañana", "day after tomorrow")):
        return ("single", today + timedelta(days=2))

    # Range: this week (today through end of week = Sunday)
    if any(x in msg for x in ("esta semana", "this week")):
        # Sunday = 6 in Python weekday()
        days_until_sunday = (6 - today.weekday()) % 7
        if days_until_sunday == 0:
            end = today
        else:
            end = today + timedelta(days=days_until_sunday)
        return ("range", today, end)

    # Range: next week (next 7 days from tomorrow)
    if any(x in msg for x in ("proxima semana", "próxima semana", "next week")):
        start = today + timedelta(days=1)
        end = today + timedelta(days=7)
        return ("range", start, end)

    # Concrete date
    concrete = _parse_concrete_date(user_message or "", tz)
    if concrete is not None:
        return ("single", concrete)

    # Fallback: today
    return ("single", today)


def format_period_label(
    result: tuple[Literal["single"], date] | tuple[Literal["range"], date, date],
    tz: ZoneInfo,
) -> str:
    """Build a human-readable period label for the LLM prompt."""
    today = _today_in_tz(tz)
    if result[0] == "single":
        d = result[1]
        if d == today:
            label = "hoy"
        elif d == today + timedelta(days=1):
            label = "mañana"
        elif d == today + timedelta(days=2):
            label = "pasado mañana"
        else:
            label = d.strftime("%Y-%m-%d")
        return f"{result[1].strftime('%Y-%m-%d')} ({label})"
    # range
    start_d, end_d = result[1], result[2]
    return f"desde {start_d.strftime('%Y-%m-%d')} hasta {end_d.strftime('%Y-%m-%d')}"
