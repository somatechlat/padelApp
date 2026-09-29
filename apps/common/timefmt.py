"""Venue-local date/time formatting (America/Guayaquil wall clock)."""
from __future__ import annotations

from datetime import date, datetime, time

from django.utils import timezone


def fmt_time(value: time | datetime | str | None) -> str:
    """`20:00` (never `20:00:00`)."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value[:5]
    if isinstance(value, datetime):
        return value.strftime("%H:%M")
    return value.strftime("%H:%M")


def fmt_date(value: date | datetime | str | None) -> str:
    """`24/09/2026` — human format used in notifications and admin."""
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            parsed = date.fromisoformat(value[:10])
        except ValueError:
            return value
        return parsed.strftime("%d/%m/%Y")
    if isinstance(value, datetime):
        value = value.date()
    return value.strftime("%d/%m/%Y")


def fmt_date_time(d: date, t: time) -> str:
    return f"{fmt_date(d)} {fmt_time(t)}"


def venue_today() -> date:
    return timezone.localdate()


def venue_now() -> datetime:
    return timezone.localtime()


def is_past(day: date, start: time) -> bool:
    """True when `day` `start` is already in the past (venue local)."""
    now = timezone.localtime()
    start_dt = datetime.combine(day, start, tzinfo=timezone.get_current_timezone())
    return start_dt <= now
