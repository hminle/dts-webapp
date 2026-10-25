"""Week anchors: the weekday a weekly figure is read on."""

from datetime import date, timedelta
from typing import Literal

AnchorWeekday = Literal["thursday", "friday"]

# date.weekday(): Monday = 0.
WEEKDAY_NUMBER: dict[AnchorWeekday, int] = {"thursday": 3, "friday": 4}

# A holiday on the anchor day falls back to the closest earlier statement
# within this many days, the rule the weekly comparison has always used.
LOOK_BACK_DAYS = 5


def anchor_on_or_before(day: date, weekday: AnchorWeekday) -> date:
    """The latest ``weekday`` on or before ``day``."""
    return day - timedelta(days=(day.weekday() - WEEKDAY_NUMBER[weekday]) % 7)


def anchor_days(start: date, end: date, weekday: AnchorWeekday) -> list[date]:
    """Every ``weekday`` between ``start`` and ``end`` inclusive.

    Also accepts ``datetime`` (a subclass of ``date``); the days come back as
    the type given.
    """
    first = start + timedelta(days=(WEEKDAY_NUMBER[weekday] - start.weekday()) % 7)
    days: list[date] = []
    current = first
    while current <= end:
        days.append(current)
        current += timedelta(days=7)
    return days
