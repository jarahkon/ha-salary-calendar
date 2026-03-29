"""Calendar platform for Salary Calendar.

Shows PTO days, sick leave days, public holidays, and pay dates on the HA calendar.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .salary.calculator import next_pay_date
from .salary.holidays import get_finnish_public_holidays
from .salary.workdays import compute_pto_saturdays

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Salary Calendar calendar entities."""
    async_add_entities(
        [SalaryCalendarEntity(hass, entry)],
        update_before_add=True,
    )


class SalaryCalendarEntity(CalendarEntity):
    """Calendar entity showing PTO, sick leave, holidays, and pay dates."""

    _attr_has_entity_name = True
    _attr_name = "Salary Calendar"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._events: list[CalendarEvent] = []

    @property
    def _data(self) -> dict:
        return self._hass.data[DOMAIN][self._entry.entry_id]

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        today = date.today()
        upcoming = [e for e in self._events if e.start >= today]
        return upcoming[0] if upcoming else None

    async def async_added_to_hass(self) -> None:
        """Register update listener for data changes."""
        self.async_on_remove(
            self._hass.bus.async_listen(f"{DOMAIN}_data_updated", self._data_updated)
        )

    @callback
    def _data_updated(self, event) -> None:
        self.async_schedule_update_ha_state(True)

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a date range."""
        return self._build_events(start_date.date(), end_date.date())

    async def async_update(self) -> None:
        """Update current events list."""
        today = date.today()
        start = today - timedelta(days=30)
        end = today + timedelta(days=90)
        self._events = self._build_events(start, end)

    def _build_events(self, start: date, end: date) -> list[CalendarEvent]:
        """Build calendar events for a date range."""
        events: list[CalendarEvent] = []

        pto_dates = self._data["pto_dates"]
        sick_dates = self._data["sick_dates"]
        pto_saturdays = compute_pto_saturdays(pto_dates)

        # PTO events
        for d in sorted(pto_dates):
            if start <= d <= end:
                events.append(
                    CalendarEvent(
                        start=d,
                        end=d + timedelta(days=1),
                        summary="PTO",
                        description="Paid time off",
                    )
                )

        # PTO Saturday events
        for d in sorted(pto_saturdays):
            if start <= d <= end:
                events.append(
                    CalendarEvent(
                        start=d,
                        end=d + timedelta(days=1),
                        summary="PTO (Saturday)",
                        description="Auto-calculated PTO Saturday",
                    )
                )

        # Sick leave events
        for d in sorted(sick_dates):
            if start <= d <= end:
                events.append(
                    CalendarEvent(
                        start=d,
                        end=d + timedelta(days=1),
                        summary="Sick Leave",
                        description="Paid sick leave",
                    )
                )

        # Public holidays
        for year in range(start.year, end.year + 1):
            holidays = get_finnish_public_holidays(year)
            for d, name in holidays.items():
                if start <= d <= end and d.weekday() < 5:
                    events.append(
                        CalendarEvent(
                            start=d,
                            end=d + timedelta(days=1),
                            summary=f"🇫🇮 {name}",
                            description=f"Finnish public holiday: {name}",
                        )
                    )

        # Pay dates — show next few
        check_date = start
        while check_date <= end:
            pay_d, pay_month, pay_year = next_pay_date(check_date)
            if pay_d > end:
                break
            if start <= pay_d <= end:
                events.append(
                    CalendarEvent(
                        start=pay_d,
                        end=pay_d + timedelta(days=1),
                        summary="💰 Pay Day",
                        description=f"Salary payment for {pay_year}-{pay_month:02d}",
                    )
                )
            # Jump to after this pay date to find the next one
            check_date = pay_d + timedelta(days=1)

        events.sort(key=lambda e: e.start)
        return events
