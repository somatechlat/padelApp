"""Venue-local date/time formatting (America/Guayaquil wall clock)."""

from __future__ import annotations

from datetime import date, datetime, time


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
