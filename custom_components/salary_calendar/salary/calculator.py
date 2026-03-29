"""Salary calculation engine.

Computes gross and net salary based on day classification and configurable rates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from .workdays import DayType, classify_month, count_by_type, get_workdays_up_to


@dataclass
class SalaryConfig:
    """Configurable salary parameters."""

    hourly_rate: float
    average_hourly_rate: float
    daily_hours: float
    tax_rate: float
    pto_multiplier: float
    pto_days_per_year: int


@dataclass
class SalaryBreakdown:
    """Detailed salary breakdown for a period."""

    workdays: int = 0
    public_holiday_days: int = 0
    pto_days: int = 0
    pto_saturday_days: int = 0
    sick_leave_days: int = 0
    weekend_days: int = 0

    workday_pay: float = 0.0
    public_holiday_pay: float = 0.0
    pto_pay: float = 0.0
    pto_saturday_pay: float = 0.0
    sick_leave_pay: float = 0.0

    gross_salary: float = 0.0
    tax_amount: float = 0.0
    net_salary: float = 0.0

    tax_rate: float = 0.0

    def as_dict(self) -> dict:
        """Convert to dict for HA sensor attributes."""
        return {
            "workdays": self.workdays,
            "public_holiday_days": self.public_holiday_days,
            "pto_days": self.pto_days,
            "pto_saturday_days": self.pto_saturday_days,
            "sick_leave_days": self.sick_leave_days,
            "weekend_days": self.weekend_days,
            "workday_pay": round(self.workday_pay, 2),
            "public_holiday_pay": round(self.public_holiday_pay, 2),
            "pto_pay": round(self.pto_pay, 2),
            "pto_saturday_pay": round(self.pto_saturday_pay, 2),
            "sick_leave_pay": round(self.sick_leave_pay, 2),
            "gross_salary": round(self.gross_salary, 2),
            "tax_amount": round(self.tax_amount, 2),
            "net_salary": round(self.net_salary, 2),
            "tax_rate": self.tax_rate,
        }


def calculate_month_salary(
    config: SalaryConfig,
    year: int,
    month: int,
    pto_dates: set[date] | None = None,
    sick_dates: set[date] | None = None,
) -> SalaryBreakdown:
    """Calculate full salary breakdown for a complete month."""
    days = classify_month(year, month, pto_dates, sick_dates)
    counts = count_by_type(days)
    return _compute_breakdown(config, counts)


def calculate_accrued_salary(
    config: SalaryConfig,
    year: int,
    month: int,
    up_to_date: date,
    pto_dates: set[date] | None = None,
    sick_dates: set[date] | None = None,
) -> SalaryBreakdown:
    """Calculate salary accrued up to a specific date in the month."""
    counts = get_workdays_up_to(year, month, up_to_date, pto_dates, sick_dates)
    return _compute_breakdown(config, counts)


def _compute_breakdown(
    config: SalaryConfig, counts: dict[DayType, int]
) -> SalaryBreakdown:
    """Compute salary breakdown from day counts and config."""
    breakdown = SalaryBreakdown()

    # Day counts
    breakdown.workdays = counts.get(DayType.WORKDAY, 0)
    breakdown.public_holiday_days = counts.get(DayType.PUBLIC_HOLIDAY, 0)
    breakdown.pto_days = counts.get(DayType.PTO, 0)
    breakdown.pto_saturday_days = counts.get(DayType.PTO_SATURDAY, 0)
    breakdown.sick_leave_days = counts.get(DayType.SICK_LEAVE, 0)
    breakdown.weekend_days = counts.get(DayType.WEEKEND, 0)

    # Pay calculations
    daily_normal = config.hourly_rate * config.daily_hours
    daily_average = config.average_hourly_rate * config.daily_hours
    daily_pto = config.pto_multiplier * daily_average

    breakdown.workday_pay = breakdown.workdays * daily_normal
    breakdown.public_holiday_pay = breakdown.public_holiday_days * daily_average
    breakdown.pto_pay = breakdown.pto_days * daily_pto
    breakdown.pto_saturday_pay = breakdown.pto_saturday_days * daily_pto
    breakdown.sick_leave_pay = breakdown.sick_leave_days * daily_average

    # Totals
    breakdown.gross_salary = (
        breakdown.workday_pay
        + breakdown.public_holiday_pay
        + breakdown.pto_pay
        + breakdown.pto_saturday_pay
        + breakdown.sick_leave_pay
    )

    breakdown.tax_rate = config.tax_rate
    breakdown.tax_amount = breakdown.gross_salary * (config.tax_rate / 100)
    breakdown.net_salary = breakdown.gross_salary - breakdown.tax_amount

    return breakdown


@dataclass
class YTDSummary:
    """Year-to-date salary summary."""

    months: list[dict] = field(default_factory=list)
    total_gross: float = 0.0
    total_net: float = 0.0
    total_tax: float = 0.0
    total_workdays: int = 0
    total_holiday_days: int = 0
    total_pto_days: int = 0
    total_pto_saturday_days: int = 0
    total_sick_days: int = 0

    def as_dict(self) -> dict:
        """Convert to dict for HA sensor attributes."""
        return {
            "months": self.months,
            "total_gross": round(self.total_gross, 2),
            "total_net": round(self.total_net, 2),
            "total_tax": round(self.total_tax, 2),
            "total_workdays": self.total_workdays,
            "total_holiday_days": self.total_holiday_days,
            "total_pto_days": self.total_pto_days,
            "total_pto_saturday_days": self.total_pto_saturday_days,
            "total_sick_days": self.total_sick_days,
        }


def calculate_ytd(
    config: SalaryConfig,
    year: int,
    up_to_month: int,
    pto_dates: set[date] | None = None,
    sick_dates: set[date] | None = None,
) -> YTDSummary:
    """Calculate year-to-date salary summary.

    Includes all completed months from January through up_to_month (inclusive).
    """
    summary = YTDSummary()

    for month in range(1, up_to_month + 1):
        month_pto = {
            d for d in (pto_dates or set()) if d.month == month and d.year == year
        }
        month_sick = {
            d for d in (sick_dates or set()) if d.month == month and d.year == year
        }

        breakdown = calculate_month_salary(config, year, month, month_pto, month_sick)

        summary.months.append(
            {
                "month": month,
                "gross": round(breakdown.gross_salary, 2),
                "net": round(breakdown.net_salary, 2),
                "workdays": breakdown.workdays,
                "holiday_days": breakdown.public_holiday_days,
                "pto_days": breakdown.pto_days,
                "pto_saturday_days": breakdown.pto_saturday_days,
                "sick_days": breakdown.sick_leave_days,
            }
        )

        summary.total_gross += breakdown.gross_salary
        summary.total_net += breakdown.net_salary
        summary.total_tax += breakdown.tax_amount
        summary.total_workdays += breakdown.workdays
        summary.total_holiday_days += breakdown.public_holiday_days
        summary.total_pto_days += breakdown.pto_days
        summary.total_pto_saturday_days += breakdown.pto_saturday_days
        summary.total_sick_days += breakdown.sick_leave_days

    return summary


def next_pay_date(from_date: date) -> tuple[date, int, int]:
    """Calculate the next pay date from a given date.

    Returns (pay_date, pay_month, pay_year) where pay_month/pay_year is the
    month being paid for.

    Pay date is the 15th of each month, shifted to the previous Friday
    if it falls on a weekend.
    """
    year = from_date.year
    month = from_date.month

    # The 15th of the current month
    pay_day_this_month = date(year, month, 15)

    if from_date <= pay_day_this_month or (
        pay_day_this_month.weekday() >= 5
        and from_date <= _adjust_to_friday(pay_day_this_month)
    ):
        # The next pay date is this month's 15th
        pay_date = _adjust_to_friday(pay_day_this_month)
        if from_date <= pay_date:
            # This pay covers the previous month
            if month == 1:
                return pay_date, 12, year - 1
            return pay_date, month - 1, year

    # Next pay date is next month's 15th
    if month == 12:
        next_month_15 = date(year + 1, 1, 15)
        pay_date = _adjust_to_friday(next_month_15)
        return pay_date, 12, year
    else:
        next_month_15 = date(year, month + 1, 15)
        pay_date = _adjust_to_friday(next_month_15)
        return pay_date, month, year


def _adjust_to_friday(d: date) -> date:
    """If date falls on Saturday or Sunday, move to the previous Friday."""
    weekday = d.weekday()
    if weekday == 5:  # Saturday
        return d - timedelta(days=1)
    if weekday == 6:  # Sunday
        return d - timedelta(days=2)
    return d
