"""Tests for Finnish public holiday calculation."""

from datetime import date

from salary.holidays import (
    _easter,
    _midsummer_eve,
    _midsummer_day,
    _all_saints_day,
    get_finnish_public_holidays,
    get_weekday_public_holidays,
    is_public_holiday,
    is_saturday_public_holiday,
)


# =============================================================================
# Easter computation — verified against known dates
# =============================================================================


class TestEaster:
    """Easter Sunday must match well-known astronomical dates."""

    def test_easter_2024(self):
        assert _easter(2024) == date(2024, 3, 31)

    def test_easter_2025(self):
        assert _easter(2025) == date(2025, 4, 20)

    def test_easter_2026(self):
        assert _easter(2026) == date(2026, 4, 5)

    def test_easter_2027(self):
        assert _easter(2027) == date(2027, 3, 28)

    def test_easter_2028(self):
        assert _easter(2028) == date(2028, 4, 16)

    def test_easter_2030(self):
        assert _easter(2030) == date(2030, 4, 21)

    def test_easter_always_sunday(self):
        """Easter must always fall on a Sunday."""
        for year in range(2020, 2040):
            assert _easter(year).weekday() == 6, f"Easter {year} is not Sunday"


# =============================================================================
# Midsummer Eve — always a Friday between June 19-25
# =============================================================================


class TestMidsummerEve:
    def test_always_friday(self):
        for year in range(2020, 2040):
            d = _midsummer_eve(year)
            assert d.weekday() == 4, f"Midsummer Eve {year} is not Friday"

    def test_always_june_19_to_25(self):
        for year in range(2020, 2040):
            d = _midsummer_eve(year)
            assert d.month == 6
            assert 19 <= d.day <= 25

    def test_2026(self):
        assert _midsummer_eve(2026) == date(2026, 6, 19)

    def test_2025(self):
        assert _midsummer_eve(2025) == date(2025, 6, 20)

    def test_2024(self):
        assert _midsummer_eve(2024) == date(2024, 6, 21)


class TestMidsummerDay:
    def test_always_saturday_after_eve(self):
        for year in range(2020, 2040):
            day = _midsummer_day(year)
            eve = _midsummer_eve(year)
            assert day.weekday() == 5, f"Midsummer Day {year} is not Saturday"
            assert day == date(eve.year, eve.month, eve.day + 1)


# =============================================================================
# All Saints' Day — always a Saturday between Oct 31 - Nov 6
# =============================================================================


class TestAllSaintsDay:
    def test_always_saturday(self):
        for year in range(2020, 2040):
            d = _all_saints_day(year)
            assert d.weekday() == 5, f"All Saints' Day {year} is not Saturday"

    def test_date_range(self):
        for year in range(2020, 2040):
            d = _all_saints_day(year)
            oct_31 = date(year, 10, 31)
            nov_6 = date(year, 11, 6)
            assert oct_31 <= d <= nov_6, f"All Saints' Day {year} out of range: {d}"

    def test_2026(self):
        assert _all_saints_day(2026) == date(2026, 10, 31)

    def test_2025(self):
        assert _all_saints_day(2025) == date(2025, 11, 1)

    def test_2024(self):
        assert _all_saints_day(2024) == date(2024, 11, 2)


# =============================================================================
# Full holiday list for known years
# =============================================================================


class TestFinnishPublicHolidays:
    def test_2026_count(self):
        """Finland has 14 public holidays."""
        holidays = get_finnish_public_holidays(2026)
        assert len(holidays) == 14

    def test_2026_fixed_holidays(self):
        holidays = get_finnish_public_holidays(2026)
        assert date(2026, 1, 1) in holidays  # New Year
        assert date(2026, 1, 6) in holidays  # Epiphany
        assert date(2026, 5, 1) in holidays  # May Day
        assert date(2026, 12, 6) in holidays  # Independence Day
        assert date(2026, 12, 24) in holidays  # Christmas Eve
        assert date(2026, 12, 25) in holidays  # Christmas Day
        assert date(2026, 12, 26) in holidays  # St. Stephen's Day

    def test_2026_easter_holidays(self):
        holidays = get_finnish_public_holidays(2026)
        assert date(2026, 4, 3) in holidays  # Good Friday
        assert date(2026, 4, 5) in holidays  # Easter Sunday
        assert date(2026, 4, 6) in holidays  # Easter Monday
        assert date(2026, 5, 14) in holidays  # Ascension Day (Easter+39)

    def test_ascension_always_thursday(self):
        """Ascension Day is always 39 days after Easter, which is a Thursday."""
        for year in range(2020, 2040):
            holidays = get_finnish_public_holidays(year)
            ascension_days = [d for d, n in holidays.items() if n == "Ascension Day"]
            assert len(ascension_days) == 1
            assert ascension_days[0].weekday() == 3, (
                f"Ascension Day {year} not Thursday"
            )

    def test_2026_midsummer(self):
        holidays = get_finnish_public_holidays(2026)
        assert date(2026, 6, 19) in holidays  # Midsummer Eve (Friday)
        assert date(2026, 6, 20) in holidays  # Midsummer Day (Saturday)

    def test_no_duplicate_dates(self):
        """No two holidays should share the same date."""
        for year in range(2020, 2040):
            holidays = get_finnish_public_holidays(year)
            # dict keys are unique by definition, but verify count is 14
            assert len(holidays) == 14, (
                f"Year {year}: expected 14 holidays, got {len(holidays)}"
            )

    def test_holiday_names_are_nonempty(self):
        holidays = get_finnish_public_holidays(2026)
        for d, name in holidays.items():
            assert isinstance(name, str) and len(name) > 0


# =============================================================================
# Weekday-only holidays (salary-affecting)
# =============================================================================


class TestWeekdayPublicHolidays:
    def test_april_2026_has_good_friday_and_easter_monday(self):
        """Good Friday (Apr 3) and Easter Monday (Apr 6) are weekdays."""
        holidays = get_weekday_public_holidays(2026, 4)
        assert date(2026, 4, 3) in holidays  # Good Friday
        assert date(2026, 4, 6) in holidays  # Easter Monday
        # Easter Sunday (Apr 5) is a Sunday — NOT in weekday holidays
        assert date(2026, 4, 5) not in holidays

    def test_june_2026_midsummer_eve_is_weekday(self):
        """Midsummer Eve is always a Friday → appears in weekday holidays."""
        holidays = get_weekday_public_holidays(2026, 6)
        assert date(2026, 6, 19) in holidays
        # Midsummer Day is Saturday → NOT in weekday holidays
        assert date(2026, 6, 20) not in holidays

    def test_december_2026_independence_day_is_sunday(self):
        """Dec 6, 2026 is a Sunday — should NOT appear in weekday holidays."""
        holidays = get_weekday_public_holidays(2026, 12)
        assert date(2026, 12, 6) not in holidays

    def test_month_with_no_holidays(self):
        """Most months have no public holidays (e.g., September)."""
        holidays = get_weekday_public_holidays(2026, 9)
        assert len(holidays) == 0

    def test_january_2026_has_two_weekday_holidays(self):
        """New Year (Thu) and Epiphany (Tue) are both weekdays."""
        holidays = get_weekday_public_holidays(2026, 1)
        assert len(holidays) == 2
        assert date(2026, 1, 1) in holidays
        assert date(2026, 1, 6) in holidays


# =============================================================================
# is_public_holiday / is_saturday_public_holiday helpers
# =============================================================================


class TestHolidayPredicates:
    def test_new_years_is_holiday(self):
        assert is_public_holiday(date(2026, 1, 1)) is True

    def test_random_workday_is_not_holiday(self):
        assert is_public_holiday(date(2026, 3, 18)) is False

    def test_midsummer_day_is_saturday_holiday(self):
        """Midsummer Day is always a Saturday and a public holiday."""
        assert is_saturday_public_holiday(date(2026, 6, 20)) is True

    def test_regular_saturday_is_not_saturday_holiday(self):
        assert is_saturday_public_holiday(date(2026, 3, 28)) is False

    def test_weekday_holiday_is_not_saturday_holiday(self):
        """New Year's Day 2026 is a Thursday — not a Saturday holiday."""
        assert is_saturday_public_holiday(date(2026, 1, 1)) is False
