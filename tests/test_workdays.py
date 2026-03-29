"""Tests for working day classification and PTO Saturday logic."""

from datetime import date

from salary.workdays import (
    DayType,
    compute_pto_saturdays,
    classify_month,
    get_workdays_in_month,
    get_workdays_up_to,
)


# =============================================================================
# PTO Saturday auto-computation
# =============================================================================


class TestComputePTOSaturdays:
    def test_friday_pto_triggers_saturday(self):
        """If Friday is PTO, the following Saturday should be PTO."""
        pto = {date(2026, 7, 10)}  # Friday
        saturdays = compute_pto_saturdays(pto)
        assert date(2026, 7, 11) in saturdays

    def test_thursday_pto_does_not_trigger_saturday(self):
        """Only Friday triggers Saturday, not Thursday."""
        pto = {date(2026, 7, 9)}  # Thursday
        saturdays = compute_pto_saturdays(pto)
        assert len(saturdays) == 0

    def test_monday_through_thursday_no_saturday(self):
        """PTO Mon-Thu should produce zero PTO Saturdays."""
        pto = {date(2026, 7, 6), date(2026, 7, 7), date(2026, 7, 8), date(2026, 7, 9)}
        saturdays = compute_pto_saturdays(pto)
        assert len(saturdays) == 0

    def test_full_week_pto_one_saturday(self):
        """PTO Mon-Fri should yield exactly one PTO Saturday."""
        pto = {
            date(2026, 7, 6),
            date(2026, 7, 7),
            date(2026, 7, 8),
            date(2026, 7, 9),
            date(2026, 7, 10),  # Mon-Fri
        }
        saturdays = compute_pto_saturdays(pto)
        assert saturdays == {date(2026, 7, 11)}

    def test_two_weeks_pto_two_saturdays(self):
        """Two full weeks of PTO should yield two PTO Saturdays."""
        pto = set()
        # Week 1: Jul 6-10
        for d in range(6, 11):
            pto.add(date(2026, 7, d))
        # Week 2: Jul 13-17
        for d in range(13, 18):
            pto.add(date(2026, 7, d))
        saturdays = compute_pto_saturdays(pto)
        assert saturdays == {date(2026, 7, 11), date(2026, 7, 18)}

    def test_midsummer_saturday_excluded(self):
        """If the Saturday after a PTO Friday is Midsummer Day, it's not PTO."""
        # Midsummer Eve 2026 = Jun 19 (Fri), Midsummer Day = Jun 20 (Sat)
        pto = {date(2026, 6, 19)}  # Midsummer Eve Friday
        saturdays = compute_pto_saturdays(pto)
        # Jun 20 is Midsummer Day (a Saturday public holiday) — excluded
        assert date(2026, 6, 20) not in saturdays

    def test_empty_pto_returns_empty(self):
        assert compute_pto_saturdays(set()) == set()


# =============================================================================
# Month classification — day counts must add up
# =============================================================================


class TestClassifyMonth:
    def test_total_days_equal_calendar_days(self):
        """Every day in the month must be classified exactly once."""
        for month in range(1, 13):
            days = classify_month(2026, month)
            import calendar

            expected = calendar.monthrange(2026, month)[1]
            assert len(days) == expected, f"Month {month}: {len(days)} != {expected}"

    def test_january_2026_no_pto_no_sick(self):
        """Jan 2026: 22 weekdays - 2 holidays = 20 workdays, 9 weekends."""
        counts = get_workdays_in_month(2026, 1)
        assert counts[DayType.WORKDAY] == 20
        assert counts[DayType.PUBLIC_HOLIDAY] == 2  # New Year's + Epiphany
        assert counts[DayType.WEEKEND] == 9
        assert counts[DayType.PTO] == 0
        assert counts[DayType.PTO_SATURDAY] == 0
        assert counts[DayType.SICK_LEAVE] == 0

    def test_april_2026_easter(self):
        """April 2026: Good Friday (3rd) and Easter Monday (6th) are holidays."""
        counts = get_workdays_in_month(2026, 4)
        assert counts[DayType.PUBLIC_HOLIDAY] == 2
        assert counts[DayType.WORKDAY] == 20  # 22 weekdays - 2 holidays
        assert counts[DayType.WEEKEND] == 8

    def test_june_2026_midsummer(self):
        """June 2026: Midsummer Eve (19th, Fri) is a weekday holiday.
        Midsummer Day (20th, Sat) is a weekend."""
        counts = get_workdays_in_month(2026, 6)
        assert counts[DayType.PUBLIC_HOLIDAY] == 1  # Only Midsummer Eve (Fri)
        # June 2026: 22 weekdays, 1 holiday -> 21 workdays
        assert counts[DayType.WORKDAY] == 21

    def test_february_2026_no_holidays(self):
        """Feb 2026 has no public holidays. 28 days, 20 weekdays."""
        counts = get_workdays_in_month(2026, 2)
        assert counts[DayType.PUBLIC_HOLIDAY] == 0
        assert counts[DayType.WORKDAY] == 20
        assert counts[DayType.WEEKEND] == 8

    def test_may_2026_may_day_and_ascension(self):
        """May 2026: May Day (1st, Fri) and Ascension Day (14th, Thu)."""
        counts = get_workdays_in_month(2026, 5)
        assert counts[DayType.PUBLIC_HOLIDAY] == 2
        # May 2026: 21 weekdays - 2 holidays = 19 workdays
        assert counts[DayType.WORKDAY] == 19

    def test_december_2026_independence_day_sunday(self):
        """Dec 6, 2026 is a Sunday — not a weekday holiday.
        Dec 24 (Thu), 25 (Fri) are weekday holidays. Dec 26 (Sat) is weekend."""
        counts = get_workdays_in_month(2026, 12)
        assert counts[DayType.PUBLIC_HOLIDAY] == 2  # Dec 24 (Thu), Dec 25 (Fri)
        # Dec 2026: 23 weekdays - 2 holidays = 21 workdays
        assert counts[DayType.WORKDAY] == 21


# =============================================================================
# PTO and sick leave classification
# =============================================================================


class TestClassifyWithPTOAndSick:
    def test_pto_replaces_workday(self):
        """A PTO day on a weekday should be classified as PTO, not WORKDAY."""
        pto = {date(2026, 3, 2)}  # Monday
        counts = get_workdays_in_month(2026, 3, pto_dates=pto)
        assert counts[DayType.PTO] == 1
        # March 2026: 22 weekdays, 0 holidays, 1 PTO = 21 workdays
        assert counts[DayType.WORKDAY] == 21

    def test_sick_replaces_workday(self):
        """A sick day on a weekday should be classified as SICK_LEAVE."""
        sick = {date(2026, 3, 2)}  # Monday
        counts = get_workdays_in_month(2026, 3, sick_dates=sick)
        assert counts[DayType.SICK_LEAVE] == 1
        assert counts[DayType.WORKDAY] == 21

    def test_public_holiday_takes_precedence_over_pto(self):
        """If a date is both PTO and a public holiday, it's a PUBLIC_HOLIDAY."""
        # Good Friday Apr 3, 2026
        pto = {date(2026, 4, 3)}
        counts = get_workdays_in_month(2026, 4, pto_dates=pto)
        assert counts[DayType.PUBLIC_HOLIDAY] == 2  # Still 2 (Good Fri + Easter Mon)
        assert counts[DayType.PTO] == 0  # Not counted as PTO

    def test_public_holiday_takes_precedence_over_sick(self):
        """If a date is both sick and a public holiday, it's a PUBLIC_HOLIDAY."""
        sick = {date(2026, 4, 3)}  # Good Friday
        counts = get_workdays_in_month(2026, 4, sick_dates=sick)
        assert counts[DayType.PUBLIC_HOLIDAY] == 2
        assert counts[DayType.SICK_LEAVE] == 0

    def test_sick_takes_precedence_over_pto(self):
        """If a date is both PTO and sick, SICK_LEAVE wins."""
        d = date(2026, 3, 2)  # Monday
        counts = get_workdays_in_month(2026, 3, pto_dates={d}, sick_dates={d})
        assert counts[DayType.SICK_LEAVE] == 1
        assert counts[DayType.PTO] == 0

    def test_full_week_pto_creates_pto_saturday(self):
        """Mon-Fri PTO should auto-create a PTO Saturday."""
        pto = {date(2026, 7, 6 + i) for i in range(5)}  # Mon Jul 6 - Fri Jul 10
        counts = get_workdays_in_month(2026, 7, pto_dates=pto)
        assert counts[DayType.PTO] == 5
        assert counts[DayType.PTO_SATURDAY] == 1
        # Jul 11 should be PTO_SATURDAY, not WEEKEND
        days = classify_month(2026, 7, pto_dates=pto)
        jul_11 = [d for d in days if d.date == date(2026, 7, 11)][0]
        assert jul_11.day_type == DayType.PTO_SATURDAY

    def test_pto_monday_to_thursday_no_saturday(self):
        """Mon-Thu PTO should NOT trigger a PTO Saturday."""
        pto = {date(2026, 7, 6 + i) for i in range(4)}  # Mon-Thu
        counts = get_workdays_in_month(2026, 7, pto_dates=pto)
        assert counts[DayType.PTO_SATURDAY] == 0

    def test_weekend_pto_ignored(self):
        """Adding a weekend date to PTO shouldn't affect anything
        (weekends are filtered when adding via service, but test the calc too)."""
        pto = {date(2026, 3, 7)}  # Saturday
        counts = get_workdays_in_month(2026, 3, pto_dates=pto)
        assert counts[DayType.PTO] == 0
        # The Saturday is still WEEKEND since it's not triggered by a Friday PTO
        assert counts[DayType.WORKDAY] == 22  # Normal March workdays


# =============================================================================
# Partial month (get_workdays_up_to)
# =============================================================================


class TestGetWorkdaysUpTo:
    def test_up_to_mid_month(self):
        """Count only working days up to March 15, 2026 (a Sunday).
        Workdays Mar 2-13 = 10 weekdays, Mar 16 onward excluded."""
        counts = get_workdays_up_to(2026, 3, date(2026, 3, 15))
        # Mar 1 is Sun, Mar 2 Mon... Mar 13 Fri = 10 weekdays, Mar 14-15 weekend
        assert counts[DayType.WORKDAY] == 10
        assert counts[DayType.WEEKEND] == 5  # Mar 1,7,8,14,15

    def test_up_to_first_day(self):
        """Mar 1, 2026 is a Sunday — zero workdays."""
        counts = get_workdays_up_to(2026, 3, date(2026, 3, 1))
        assert counts[DayType.WORKDAY] == 0
        assert counts[DayType.WEEKEND] == 1

    def test_up_to_last_day_equals_full_month(self):
        """Up to Mar 31 should equal the full month count."""
        full = get_workdays_in_month(2026, 3)
        partial = get_workdays_up_to(2026, 3, date(2026, 3, 31))
        assert full == partial
