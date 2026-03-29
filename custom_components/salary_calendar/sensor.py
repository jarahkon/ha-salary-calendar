"""Sensor platform for Salary Calendar."""

from __future__ import annotations

import logging
from datetime import date, datetime

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change

from .const import DOMAIN
from .salary.calculator import (
    SalaryConfig,
    calculate_accrued_salary,
    calculate_month_salary,
    calculate_ytd,
    next_pay_date,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Salary Calendar sensors."""
    sensors = [
        NextPayDateSensor(hass, entry),
        PayPeriodGrossSensor(hass, entry),
        PayPeriodNetSensor(hass, entry),
        CurrentMonthAccruedSensor(hass, entry),
        PTORemainingSensor(hass, entry),
        YTDGrossSensor(hass, entry),
        YTDNetSensor(hass, entry),
    ]

    async_add_entities(sensors, update_before_add=True)


class SalaryBaseSensor(SensorEntity):
    """Base class for salary sensors."""

    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._entry = entry
        self._hass = hass

    @property
    def _data(self) -> dict:
        return self._hass.data[DOMAIN][self._entry.entry_id]

    @property
    def _config(self) -> SalaryConfig:
        return self._data["config"]

    @property
    def _pto_dates(self) -> set[date]:
        return self._data["pto_dates"]

    @property
    def _sick_dates(self) -> set[date]:
        return self._data["sick_dates"]

    async def async_added_to_hass(self) -> None:
        """Register update listeners."""
        # Update at midnight
        self.async_on_remove(
            async_track_time_change(
                self._hass, self._midnight_update, hour=0, minute=0, second=5
            )
        )
        # Update when PTO/sick data changes
        self.async_on_remove(
            self._hass.bus.async_listen(f"{DOMAIN}_data_updated", self._data_updated)
        )

    @callback
    def _midnight_update(self, now: datetime) -> None:
        self.async_schedule_update_ha_state(True)

    @callback
    def _data_updated(self, event) -> None:
        self.async_schedule_update_ha_state(True)


class NextPayDateSensor(SalaryBaseSensor):
    """Sensor showing the next pay date and countdown."""

    _attr_name = "Next Pay Date"
    _attr_icon = "mdi:calendar-clock"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_next_pay_date"

    async def async_update(self) -> None:
        today = date.today()
        pay_date, pay_month, pay_year = next_pay_date(today)
        delta = (pay_date - today).days

        self._attr_native_value = pay_date.isoformat()
        self._attr_extra_state_attributes = {
            "countdown_days": delta,
            "pay_period_month": pay_month,
            "pay_period_year": pay_year,
            "adjusted": pay_date.day != 15,
            "friendly": f"{pay_date.strftime('%B %d')} — in {delta} day{'s' if delta != 1 else ''}",
        }


class PayPeriodGrossSensor(SalaryBaseSensor):
    """Sensor showing gross salary for the pay period (previous completed month)."""

    _attr_name = "Pay Period Gross"
    _attr_icon = "mdi:cash-plus"
    _attr_native_unit_of_measurement = "€"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_pay_period_gross"

    async def async_update(self) -> None:
        today = date.today()
        _, pay_month, pay_year = next_pay_date(today)

        month_pto = {
            d for d in self._pto_dates if d.month == pay_month and d.year == pay_year
        }
        month_sick = {
            d for d in self._sick_dates if d.month == pay_month and d.year == pay_year
        }

        breakdown = calculate_month_salary(
            self._config, pay_year, pay_month, month_pto, month_sick
        )

        self._attr_native_value = round(breakdown.gross_salary, 2)
        self._attr_extra_state_attributes = {
            "pay_period": f"{pay_year}-{pay_month:02d}",
            **breakdown.as_dict(),
        }


class PayPeriodNetSensor(SalaryBaseSensor):
    """Sensor showing net salary for the pay period."""

    _attr_name = "Pay Period Net"
    _attr_icon = "mdi:cash-check"
    _attr_native_unit_of_measurement = "€"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_pay_period_net"

    async def async_update(self) -> None:
        today = date.today()
        _, pay_month, pay_year = next_pay_date(today)

        month_pto = {
            d for d in self._pto_dates if d.month == pay_month and d.year == pay_year
        }
        month_sick = {
            d for d in self._sick_dates if d.month == pay_month and d.year == pay_year
        }

        breakdown = calculate_month_salary(
            self._config, pay_year, pay_month, month_pto, month_sick
        )

        self._attr_native_value = round(breakdown.net_salary, 2)
        self._attr_extra_state_attributes = {
            "pay_period": f"{pay_year}-{pay_month:02d}",
            "gross": round(breakdown.gross_salary, 2),
            "tax_amount": round(breakdown.tax_amount, 2),
            "tax_rate": breakdown.tax_rate,
        }


class CurrentMonthAccruedSensor(SalaryBaseSensor):
    """Sensor showing salary accrued so far this month."""

    _attr_name = "Current Month Accrued"
    _attr_icon = "mdi:cash-sync"
    _attr_native_unit_of_measurement = "€"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_current_month_accrued"

    async def async_update(self) -> None:
        today = date.today()

        month_pto = {
            d
            for d in self._pto_dates
            if d.month == today.month and d.year == today.year
        }
        month_sick = {
            d
            for d in self._sick_dates
            if d.month == today.month and d.year == today.year
        }

        breakdown = calculate_accrued_salary(
            self._config, today.year, today.month, today, month_pto, month_sick
        )

        # Also get full month forecast
        full_month = calculate_month_salary(
            self._config, today.year, today.month, month_pto, month_sick
        )

        self._attr_native_value = round(breakdown.gross_salary, 2)
        self._attr_extra_state_attributes = {
            "as_of_date": today.isoformat(),
            "days_worked": breakdown.workdays,
            "pto_days": breakdown.pto_days,
            "sick_days": breakdown.sick_leave_days,
            "month_forecast_gross": round(full_month.gross_salary, 2),
            "month_forecast_net": round(full_month.net_salary, 2),
            "remaining_workdays": full_month.workdays - breakdown.workdays,
        }


class PTORemainingSensor(SalaryBaseSensor):
    """Sensor showing remaining PTO days for the year."""

    _attr_name = "PTO Remaining"
    _attr_icon = "mdi:beach"
    _attr_native_unit_of_measurement = "days"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_pto_remaining"

    async def async_update(self) -> None:
        today = date.today()
        year = today.year
        total = self._config.pto_days_per_year

        # Count PTO weekdays used this year
        year_pto = {d for d in self._pto_dates if d.year == year}

        # Count auto-computed PTO Saturdays too
        from .salary.workdays import compute_pto_saturdays

        pto_saturdays = compute_pto_saturdays(year_pto)
        used = len(year_pto) + len(pto_saturdays)

        # Planned future PTO
        future_pto = {d for d in year_pto if d > today}
        future_saturdays = {d for d in pto_saturdays if d > today}
        planned = len(future_pto) + len(future_saturdays)

        remaining = total - used
        weeks_equivalent = remaining / 6  # Finnish PTO counts Mon-Sat

        self._attr_native_value = remaining
        self._attr_extra_state_attributes = {
            "total": total,
            "used": used - planned,
            "planned": planned,
            "remaining": remaining,
            "weeks_equivalent": round(weeks_equivalent, 1),
        }


class YTDGrossSensor(SalaryBaseSensor):
    """Sensor showing year-to-date gross salary."""

    _attr_name = "YTD Gross"
    _attr_icon = "mdi:chart-line"
    _attr_native_unit_of_measurement = "€"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_ytd_gross"

    async def async_update(self) -> None:
        today = date.today()
        # YTD includes completed months only (up to previous month)
        last_completed_month = today.month - 1
        if last_completed_month < 1:
            self._attr_native_value = 0
            self._attr_extra_state_attributes = {"months": []}
            return

        summary = calculate_ytd(
            self._config,
            today.year,
            last_completed_month,
            self._pto_dates,
            self._sick_dates,
        )

        self._attr_native_value = round(summary.total_gross, 2)
        self._attr_extra_state_attributes = summary.as_dict()


class YTDNetSensor(SalaryBaseSensor):
    """Sensor showing year-to-date net salary."""

    _attr_name = "YTD Net"
    _attr_icon = "mdi:chart-line-variant"
    _attr_native_unit_of_measurement = "€"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_ytd_net"

    async def async_update(self) -> None:
        today = date.today()
        last_completed_month = today.month - 1
        if last_completed_month < 1:
            self._attr_native_value = 0
            self._attr_extra_state_attributes = {"months": []}
            return

        summary = calculate_ytd(
            self._config,
            today.year,
            last_completed_month,
            self._pto_dates,
            self._sick_dates,
        )

        self._attr_native_value = round(summary.total_net, 2)
        self._attr_extra_state_attributes = summary.as_dict()
