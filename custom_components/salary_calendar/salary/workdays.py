"""Working day enumeration and classification.

Classifies each day in a month as: workday, public_holiday, pto, pto_saturday,
sick_leave, weekend, or non_working.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from enum import Enum

from .holidays import get_finnish_public_holidays, is_saturday_public_holiday


class DayType(Enum):
    """Classification of a day for salary purposes."""

    WORKDAY = "workday"
    PUBLIC_HOLIDAY = "public_holiday"
    PTO = "pto"
    PTO_SATURDAY = "pto_saturday"
    SICK_LEAVE = "sick_leave"
    WEEKEND = "weekend"


class DayInfo:
    """Information about a single day."""

    def __init__(self, d: date, day_type: DayType, note: str = "") -> None:
        self.date = d
        self.day_type = day_type
        self.note = note

    def __repr__(self) -> str:
        return f"DayInfo({self.date}, {self.day_type.value}, {self.note!r})"


def compute_pto_saturdays(pto_dates: set[date]) -> set[date]:
    """Compute which Saturdays are automatically PTO days.

    Finnish rule: if a Friday is a PTO day, the following Saturday is also
    counted as PTO — unless that Saturday is a public holiday.
    """
    saturdays: set[date] = set()
    for d in pto_dates:
        if d.weekday() == 4:  # Friday
            saturday = d + timedelta(days=1)
            if not is_saturday_public_holiday(saturday):
                saturdays.add(saturday)
    return saturdays


def classify_month(
    year: int,
    month: int,
    pto_dates: set[date] | None = None,
    sick_dates: set[date] | None = None,
) -> list[DayInfo]:
    """Classify every day in a month for salary calculation.

    Priority order:
    1. Public holiday (on weekday) — always takes precedence
    2. Sick leave (on weekday)
    3. PTO (on weekday)
    4. PTO Saturday (auto-computed)
    5. Normal workday (Mon-Fri)
    6. Weekend (Sat-Sun, not PTO Saturday)

    Returns a list of DayInfo for every day in the month.
    """
    pto_dates = pto_dates or set()
    sick_dates = sick_dates or set()

    public_holidays = get_finnish_public_holidays(year)
    pto_saturdays = compute_pto_saturdays(pto_dates)

    num_days = calendar.monthrange(year, month)[1]
    days: list[DayInfo] = []

    for day_num in range(1, num_days + 1):
        d = date(year, month, day_num)
        weekday = d.weekday()  # 0=Mon, 5=Sat, 6=Sun

        if d in public_holidays and weekday < 6:
            # Public holiday on a weekday (Mon-Sat) — takes precedence
            # Note: Saturdays that are public holidays are not workdays anyway
            if weekday < 5:
                days.append(DayInfo(d, DayType.PUBLIC_HOLIDAY, public_holidays[d]))
            else:
                # Saturday public holiday — just a weekend
                days.append(DayInfo(d, DayType.WEEKEND, public_holidays[d]))
        elif weekday < 5 and d in sick_dates:
            days.append(DayInfo(d, DayType.SICK_LEAVE))
        elif weekday < 5 and d in pto_dates:
            days.append(DayInfo(d, DayType.PTO))
        elif weekday == 5 and d in pto_saturdays:
            days.append(DayInfo(d, DayType.PTO_SATURDAY))
        elif weekday < 5:
            days.append(DayInfo(d, DayType.WORKDAY))
        else:
            days.append(DayInfo(d, DayType.WEEKEND))

    return days


def count_by_type(days: list[DayInfo]) -> dict[DayType, int]:
    """Count days by type."""
    counts: dict[DayType, int] = {dt: 0 for dt in DayType}
    for day in days:
        counts[day.day_type] += 1
    return counts


def get_workdays_in_month(
    year: int,
    month: int,
    pto_dates: set[date] | None = None,
    sick_dates: set[date] | None = None,
) -> dict[DayType, int]:
    """Get day type counts for a month."""
    days = classify_month(year, month, pto_dates, sick_dates)
    return count_by_type(days)


def get_workdays_up_to(
    year: int,
    month: int,
    up_to_date: date,
    pto_dates: set[date] | None = None,
    sick_dates: set[date] | None = None,
) -> dict[DayType, int]:
    """Get day type counts for a month up to (and including) a specific date.

    Used for current month accrual calculation.
    """
    days = classify_month(year, month, pto_dates, sick_dates)
    filtered = [d for d in days if d.date <= up_to_date]
    return count_by_type(filtered)
