"""Finnish public holiday calculation.

Handles fixed and moveable (Easter-based) public holidays.
"""

from datetime import date, timedelta


def _easter(year: int) -> date:
    """Compute Easter Sunday using the Anonymous Gregorian algorithm."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7  # noqa: E741
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def _midsummer_eve(year: int) -> date:
    """Midsummer Eve: Friday between June 19-25."""
    for day in range(19, 26):
        d = date(year, 6, day)
        if d.weekday() == 4:  # Friday
            return d
    raise ValueError(f"Could not find Midsummer Eve for {year}")


def _midsummer_day(year: int) -> date:
    """Midsummer Day: Saturday between June 20-26."""
    return _midsummer_eve(year) + timedelta(days=1)


def _all_saints_day(year: int) -> date:
    """All Saints' Day: Saturday between Oct 31 - Nov 6."""
    for day in range(31, 32):
        d = date(year, 10, day)
        if d.weekday() == 5:
            return d
    for day in range(1, 7):
        d = date(year, 11, day)
        if d.weekday() == 5:
            return d
    raise ValueError(f"Could not find All Saints' Day for {year}")


def get_finnish_public_holidays(year: int) -> dict[date, str]:
    """Return all Finnish public holidays for a given year.

    Returns a dict mapping date -> holiday name.
    """
    easter_sunday = _easter(year)

    holidays: dict[date, str] = {
        # Fixed holidays
        date(year, 1, 1): "New Year's Day",
        date(year, 1, 6): "Epiphany",
        date(year, 5, 1): "May Day",
        date(year, 12, 6): "Independence Day",
        date(year, 12, 24): "Christmas Eve",
        date(year, 12, 25): "Christmas Day",
        date(year, 12, 26): "St. Stephen's Day",
        # Easter-based moveable holidays
        easter_sunday + timedelta(days=-2): "Good Friday",
        easter_sunday: "Easter Sunday",
        easter_sunday + timedelta(days=1): "Easter Monday",
        easter_sunday + timedelta(days=39): "Ascension Day",
        # Other moveable holidays
        _midsummer_eve(year): "Midsummer Eve",
        _midsummer_day(year): "Midsummer Day",
        _all_saints_day(year): "All Saints' Day",
    }

    return holidays


def get_weekday_public_holidays(year: int, month: int) -> dict[date, str]:
    """Return public holidays that fall on weekdays (Mon-Fri) for a given month.

    These are the holidays that affect salary (replace a normal workday).
    """
    all_holidays = get_finnish_public_holidays(year)
    return {
        d: name
        for d, name in all_holidays.items()
        if d.month == month and d.weekday() < 5  # Mon-Fri only
    }


def is_public_holiday(d: date) -> bool:
    """Check if a date is a Finnish public holiday."""
    return d in get_finnish_public_holidays(d.year)


def is_saturday_public_holiday(d: date) -> bool:
    """Check if a Saturday is a public holiday (relevant for PTO Saturday exclusion)."""
    return d.weekday() == 5 and is_public_holiday(d)
