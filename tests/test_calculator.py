"""Tests for salary calculation engine."""

from datetime import date

from salary.calculator import (
    SalaryConfig,
    calculate_month_salary,
    calculate_accrued_salary,
    calculate_ytd,
    next_pay_date,
    _adjust_to_friday,
)


# =============================================================================
# Pay rate calculations
# =============================================================================

# Explicit test config — mirrors const.py defaults but keeps calculator free of hardcoded values
DEFAULT_CONFIG = SalaryConfig(
    hourly_rate=41.0,
    average_hourly_rate=41.0,
    daily_hours=7.5,
    tax_rate=35.19,
    pto_multiplier=1.25,
    pto_days_per_year=30,
)


class TestPayRates:
    """Verify the fundamental pay-per-day math."""

    def test_daily_workday_pay(self):
        """41 €/h × 7.5 h = 307.50 €/day."""
        b = calculate_month_salary(DEFAULT_CONFIG, 2026, 2)  # Feb, 20 workdays
        assert b.workday_pay == 20 * 307.50

    def test_daily_holiday_pay(self):
        """41 €/h × 7.5 h = 307.50 €/day."""
        b = calculate_month_salary(DEFAULT_CONFIG, 2026, 1)  # Jan, 2 holidays
        assert b.public_holiday_pay == 2 * 307.50

    def test_daily_pto_pay(self):
        """1.25 × 41 €/h × 7.5 h = 384.375 €/day."""
        pto = {date(2026, 7, 6)}  # Monday
        b = calculate_month_salary(DEFAULT_CONFIG, 2026, 7, pto_dates=pto)
        assert b.pto_pay == 1 * 384.375

    def test_daily_sick_pay_equals_holiday_pay(self):
        """Sick leave pays the same as a public holiday day."""
        sick = {date(2026, 3, 2)}  # Monday
        b = calculate_month_salary(DEFAULT_CONFIG, 2026, 3, sick_dates=sick)
        assert b.sick_leave_pay == 307.50

    def test_pto_saturday_pay_equals_pto_weekday_pay(self):
        """PTO Saturdays pay at the same PTO rate."""
        # Full week PTO to trigger Saturday
        pto = {date(2026, 7, 6 + i) for i in range(5)}
        b = calculate_month_salary(DEFAULT_CONFIG, 2026, 7, pto_dates=pto)
        assert b.pto_saturday_days == 1
        assert b.pto_saturday_pay == 384.375


# =============================================================================
# Gross salary composition
# =============================================================================


class TestGrossSalary:
    def test_gross_is_sum_of_components(self):
        """Gross must equal sum of all pay components."""
        pto = {date(2026, 7, 6 + i) for i in range(5)}
        sick = {date(2026, 7, 13)}
        b = calculate_month_salary(DEFAULT_CONFIG, 2026, 7, pto, sick)
        expected = (
            b.workday_pay
            + b.public_holiday_pay
            + b.pto_pay
            + b.pto_saturday_pay
            + b.sick_leave_pay
        )
        assert abs(b.gross_salary - expected) < 0.01

    def test_normal_february_gross(self):
        """Feb 2026: 20 workdays, 0 holidays. Gross = 20 × 307.50 = 6150.00."""
        b = calculate_month_salary(DEFAULT_CONFIG, 2026, 2)
        assert b.gross_salary == 6150.00

    def test_january_with_holidays(self):
        """Jan 2026: 20 workdays + 2 holidays.
        Gross = 20 × 307.50 + 2 × 307.50 = 6150 + 615 = 6765."""
        b = calculate_month_salary(DEFAULT_CONFIG, 2026, 1)
        assert b.gross_salary == 6765.00


# =============================================================================
# Tax and net calculations
# =============================================================================


class TestTaxAndNet:
    def test_tax_calculation(self):
        """Tax = gross × 35.19%."""
        b = calculate_month_salary(DEFAULT_CONFIG, 2026, 2)
        expected_tax = 6150.00 * 0.3519
        assert abs(b.tax_amount - expected_tax) < 0.01

    def test_net_is_gross_minus_tax(self):
        b = calculate_month_salary(DEFAULT_CONFIG, 2026, 2)
        assert abs(b.net_salary - (b.gross_salary - b.tax_amount)) < 0.01

    def test_net_equals_gross_times_complement(self):
        """Net = gross × (1 - 0.3519) = gross × 0.6481."""
        b = calculate_month_salary(DEFAULT_CONFIG, 2026, 2)
        assert abs(b.net_salary - b.gross_salary * 0.6481) < 0.01

    def test_tax_rate_stored_in_breakdown(self):
        b = calculate_month_salary(DEFAULT_CONFIG, 2026, 2)
        assert b.tax_rate == 35.19


# =============================================================================
# Custom config
# =============================================================================


class TestCustomConfig:
    def test_custom_hourly_rate(self):
        config = SalaryConfig(
            hourly_rate=50.0,
            average_hourly_rate=41.0,
            daily_hours=7.5,
            tax_rate=35.19,
            pto_multiplier=1.25,
            pto_days_per_year=30,
        )
        b = calculate_month_salary(config, 2026, 2)
        assert b.workday_pay == 20 * (50.0 * 7.5)

    def test_custom_tax_rate(self):
        config = SalaryConfig(
            hourly_rate=41.0,
            average_hourly_rate=41.0,
            daily_hours=7.5,
            tax_rate=30.0,
            pto_multiplier=1.25,
            pto_days_per_year=30,
        )
        b = calculate_month_salary(config, 2026, 2)
        assert abs(b.tax_amount - b.gross_salary * 0.30) < 0.01

    def test_custom_pto_multiplier(self):
        config = SalaryConfig(
            hourly_rate=41.0,
            average_hourly_rate=41.0,
            daily_hours=7.5,
            tax_rate=35.19,
            pto_multiplier=1.5,
            pto_days_per_year=30,
        )
        pto = {date(2026, 7, 6)}
        b = calculate_month_salary(config, 2026, 7, pto_dates=pto)
        expected = 1.5 * 41.0 * 7.5
        assert abs(b.pto_pay - expected) < 0.01

    def test_custom_daily_hours(self):
        config = SalaryConfig(
            hourly_rate=41.0,
            average_hourly_rate=41.0,
            daily_hours=8.0,
            tax_rate=35.19,
            pto_multiplier=1.25,
            pto_days_per_year=30,
        )
        b = calculate_month_salary(config, 2026, 2)
        assert b.workday_pay == 20 * (41.0 * 8.0)


# =============================================================================
# Accrued salary (partial month)
# =============================================================================


class TestAccruedSalary:
    def test_mid_month_accrual(self):
        """Accrued through Mar 15 (Sunday): 10 workdays × 307.50."""
        b = calculate_accrued_salary(DEFAULT_CONFIG, 2026, 3, date(2026, 3, 15))
        assert b.workdays == 10
        assert b.workday_pay == 10 * 307.50

    def test_full_month_accrual_matches_full_calc(self):
        full = calculate_month_salary(DEFAULT_CONFIG, 2026, 3)
        accrued = calculate_accrued_salary(DEFAULT_CONFIG, 2026, 3, date(2026, 3, 31))
        assert full.gross_salary == accrued.gross_salary


# =============================================================================
# Year-to-date
# =============================================================================


class TestYTD:
    def test_ytd_single_month(self):
        """Payment month 1 (January) pays for December of the previous year."""
        summary = calculate_ytd(DEFAULT_CONFIG, 2026, 1)
        assert len(summary.months) == 1
        assert summary.months[0]["month"] == 1
        assert summary.months[0]["earned_month"] == 12
        assert summary.months[0]["earned_year"] == 2025
        dec = calculate_month_salary(DEFAULT_CONFIG, 2025, 12)
        assert abs(summary.total_gross - dec.gross_salary) < 0.01

    def test_ytd_multiple_months(self):
        """Payment months 1-3 cover Dec 2025 + Jan 2026 + Feb 2026."""
        summary = calculate_ytd(DEFAULT_CONFIG, 2026, 3)
        assert len(summary.months) == 3
        # Verify total is sum of the *earned* months
        dec = calculate_month_salary(DEFAULT_CONFIG, 2025, 12)
        jan = calculate_month_salary(DEFAULT_CONFIG, 2026, 1)
        feb = calculate_month_salary(DEFAULT_CONFIG, 2026, 2)
        total = dec.gross_salary + jan.gross_salary + feb.gross_salary
        assert abs(summary.total_gross - total) < 0.01

    def test_ytd_with_pto(self):
        """PTO in January is paid in payment month 2 (February)."""
        pto = {date(2026, 1, 7), date(2026, 1, 8)}  # Wed-Thu, no holidays
        summary = calculate_ytd(DEFAULT_CONFIG, 2026, 2, pto_dates=pto)
        # Payment month 2 covers January earnings
        jan_entry = summary.months[1]
        assert jan_entry["earned_month"] == 1
        assert jan_entry["pto_days"] == 2

    def test_ytd_tax_consistency(self):
        """Total tax should equal total_gross * tax_rate."""
        summary = calculate_ytd(DEFAULT_CONFIG, 2026, 3)
        expected_tax = summary.total_gross * (35.19 / 100)
        assert abs(summary.total_tax - expected_tax) < 0.01

    def test_ytd_net_is_gross_minus_tax(self):
        summary = calculate_ytd(DEFAULT_CONFIG, 2026, 3)
        assert abs(summary.total_net - (summary.total_gross - summary.total_tax)) < 0.01

    def test_ytd_earned_month_fields(self):
        """Verify earned_month and earned_year are correctly populated."""
        summary = calculate_ytd(DEFAULT_CONFIG, 2026, 3)
        expected = [
            {"month": 1, "earned_month": 12, "earned_year": 2025},
            {"month": 2, "earned_month": 1, "earned_year": 2026},
            {"month": 3, "earned_month": 2, "earned_year": 2026},
        ]
        for entry, exp in zip(summary.months, expected):
            assert entry["month"] == exp["month"]
            assert entry["earned_month"] == exp["earned_month"]
            assert entry["earned_year"] == exp["earned_year"]

    def test_ytd_previous_year_pto(self):
        """PTO in December of previous year should appear in payment month 1."""
        pto = {date(2025, 12, 1), date(2025, 12, 2)}
        summary = calculate_ytd(DEFAULT_CONFIG, 2026, 1, pto_dates=pto)
        assert summary.months[0]["pto_days"] == 2


# =============================================================================
# as_dict serialization
# =============================================================================


class TestBreakdownAsDict:
    def test_all_keys_present(self):
        b = calculate_month_salary(DEFAULT_CONFIG, 2026, 1)
        d = b.as_dict()
        expected_keys = {
            "workdays",
            "public_holiday_days",
            "pto_days",
            "pto_saturday_days",
            "sick_leave_days",
            "weekend_days",
            "workday_pay",
            "public_holiday_pay",
            "pto_pay",
            "pto_saturday_pay",
            "sick_leave_pay",
            "gross_salary",
            "tax_amount",
            "net_salary",
            "tax_rate",
        }
        assert set(d.keys()) == expected_keys

    def test_values_are_rounded(self):
        b = calculate_month_salary(DEFAULT_CONFIG, 2026, 1)
        d = b.as_dict()
        # All monetary values should be rounded to 2 decimal places
        for key in [
            "workday_pay",
            "public_holiday_pay",
            "gross_salary",
            "tax_amount",
            "net_salary",
        ]:
            val = d[key]
            assert val == round(val, 2), f"{key} not rounded: {val}"


# =============================================================================
# _adjust_to_friday
# =============================================================================


class TestAdjustToFriday:
    def test_weekday_unchanged(self):
        """Mon-Fri should not be adjusted."""
        for day in [12, 13, 14, 15, 16]:  # Mon-Fri in Jan 2026 (week of 12th)
            d = date(2026, 1, day)
            assert _adjust_to_friday(d) == d

    def test_saturday_to_friday(self):
        d = date(2026, 1, 17)  # Saturday
        assert _adjust_to_friday(d) == date(2026, 1, 16)

    def test_sunday_to_friday(self):
        d = date(2026, 1, 18)  # Sunday
        assert _adjust_to_friday(d) == date(2026, 1, 16)


# =============================================================================
# next_pay_date
# =============================================================================


class TestNextPayDate:
    def test_normal_weekday_15th(self):
        """Apr 15, 2026 is Wednesday — no adjustment needed.
        Pays for March."""
        pay, month, year = next_pay_date(date(2026, 4, 1))
        assert pay == date(2026, 4, 15)
        assert month == 3
        assert year == 2026

    def test_saturday_15th_shifted_to_friday(self):
        """Aug 15, 2026 is Saturday → pay on Friday Aug 14.
        From Aug 1, should see Aug 14 paying for July."""
        pay, month, year = next_pay_date(date(2026, 8, 1))
        assert pay == date(2026, 8, 14)
        assert month == 7
        assert year == 2026

    def test_sunday_15th_shifted_to_friday(self):
        """Feb 15, 2026 is Sunday → pay on Friday Feb 13.
        From Feb 1, should see Feb 13 paying for January."""
        pay, month, year = next_pay_date(date(2026, 2, 1))
        assert pay == date(2026, 2, 13)
        assert month == 1
        assert year == 2026

    def test_on_pay_day_itself(self):
        """On the pay date, it should still show as the next pay date."""
        pay, month, year = next_pay_date(date(2026, 4, 15))
        assert pay == date(2026, 4, 15)
        assert month == 3

    def test_on_adjusted_pay_day(self):
        """On Aug 14 (the adjusted Friday for Aug 15 Sat), show that date."""
        pay, month, year = next_pay_date(date(2026, 8, 14))
        assert pay == date(2026, 8, 14)
        assert month == 7

    def test_day_after_pay_date_shows_next_month(self):
        """Apr 16 → next pay is May 15 (Fri) paying for April."""
        pay, month, year = next_pay_date(date(2026, 4, 16))
        assert pay == date(2026, 5, 15)
        assert month == 4
        assert year == 2026

    def test_day_after_adjusted_pay_date(self):
        """Aug 15 is Saturday (pay was Aug 14). On Aug 15, next pay = Sep 15."""
        pay, month, year = next_pay_date(date(2026, 8, 15))
        assert pay == date(2026, 9, 15)
        assert month == 8
        assert year == 2026

    def test_between_adjusted_and_nominal(self):
        """Feb 14 (Saturday) — adjusted pay was Feb 13, Feb 15 is Sunday.
        Pay already happened. Next = Mar 13 (Fri, adjusted from Mar 15 Sun)."""
        pay, month, year = next_pay_date(date(2026, 2, 14))
        assert pay == date(2026, 3, 13)
        assert month == 2
        assert year == 2026

    def test_january_pays_for_december(self):
        """Jan 1 → next pay is Jan 15, paying for December of previous year."""
        pay, month, year = next_pay_date(date(2026, 1, 1))
        assert pay == date(2026, 1, 15)
        assert month == 12
        assert year == 2025

    def test_december_after_15th_wraps_to_january(self):
        """Dec 16, 2026 → next pay is Jan 15, 2027, paying for December 2026."""
        pay, month, year = next_pay_date(date(2026, 12, 16))
        assert pay == date(2027, 1, 15)
        assert month == 12
        assert year == 2026

    def test_end_of_year(self):
        """Dec 31 → next pay is Jan 15 of next year."""
        pay, month, year = next_pay_date(date(2026, 12, 31))
        assert pay == date(2027, 1, 15)
        assert month == 12
        assert year == 2026

    def test_pay_date_always_in_future_or_today(self):
        """For any date in 2026, next pay date should be >= that date."""
        for month in range(1, 13):
            import calendar

            for day in range(1, calendar.monthrange(2026, month)[1] + 1):
                from_d = date(2026, month, day)
                pay, _, _ = next_pay_date(from_d)
                assert pay >= from_d, f"Pay date {pay} < from_date {from_d}"

    def test_pay_month_always_before_or_equal_pay_date_month(self):
        """The paid-for month should always be before the pay date month
        (or December when pay is in January)."""
        for month in range(1, 13):
            import calendar

            for day in range(1, calendar.monthrange(2026, month)[1] + 1):
                from_d = date(2026, month, day)
                pay, pay_m, pay_y = next_pay_date(from_d)
                paid_for = date(pay_y, pay_m, 1)
                assert paid_for < date(pay.year, pay.month, 1), (
                    f"Pay date {pay} (for {pay_y}-{pay_m:02d}) doesn't precede pay month"
                )
