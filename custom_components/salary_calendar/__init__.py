"""The Salary Calendar integration."""

from __future__ import annotations

import logging
from datetime import date, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.storage import Store

from .const import (
    CONF_AVERAGE_HOURLY_RATE,
    CONF_DAILY_HOURS,
    CONF_HOURLY_RATE,
    CONF_PTO_DAYS_PER_YEAR,
    CONF_PTO_MULTIPLIER,
    CONF_TAX_RATE,
    DEFAULT_AVERAGE_HOURLY_RATE,
    DEFAULT_DAILY_HOURS,
    DEFAULT_HOURLY_RATE,
    DEFAULT_PTO_DAYS_PER_YEAR,
    DEFAULT_PTO_MULTIPLIER,
    DEFAULT_TAX_RATE,
    DOMAIN,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .salary.calculator import SalaryConfig

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.CALENDAR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Salary Calendar from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Build salary config from entry options (with fallback to entry data)
    config_data = {**entry.data, **entry.options}
    salary_config = SalaryConfig(
        hourly_rate=config_data.get(CONF_HOURLY_RATE, DEFAULT_HOURLY_RATE),
        average_hourly_rate=config_data.get(
            CONF_AVERAGE_HOURLY_RATE, DEFAULT_AVERAGE_HOURLY_RATE
        ),
        daily_hours=config_data.get(CONF_DAILY_HOURS, DEFAULT_DAILY_HOURS),
        tax_rate=config_data.get(CONF_TAX_RATE, DEFAULT_TAX_RATE),
        pto_multiplier=config_data.get(CONF_PTO_MULTIPLIER, DEFAULT_PTO_MULTIPLIER),
        pto_days_per_year=config_data.get(
            CONF_PTO_DAYS_PER_YEAR, DEFAULT_PTO_DAYS_PER_YEAR
        ),
    )

    # Load PTO and sick leave data from storage
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    stored_data = await store.async_load() or {}

    pto_dates: set[date] = set()
    sick_dates: set[date] = set()
    for d_str in stored_data.get("pto_dates", []):
        pto_dates.add(date.fromisoformat(d_str))
    for d_str in stored_data.get("sick_dates", []):
        sick_dates.add(date.fromisoformat(d_str))

    hass.data[DOMAIN][entry.entry_id] = {
        "config": salary_config,
        "store": store,
        "pto_dates": pto_dates,
        "sick_dates": sick_dates,
    }

    # Register services
    await _async_register_services(hass)

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Listen for options updates
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_save_data(hass: HomeAssistant, entry_id: str) -> None:
    """Save PTO and sick leave data to storage."""
    data = hass.data[DOMAIN][entry_id]
    store: Store = data["store"]
    await store.async_save(
        {
            "pto_dates": sorted(d.isoformat() for d in data["pto_dates"]),
            "sick_dates": sorted(d.isoformat() for d in data["sick_dates"]),
        }
    )


def _get_entry_id(hass: HomeAssistant) -> str:
    """Get the first (and typically only) config entry ID."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        raise ValueError("Salary Calendar is not configured")
    return entries[0].entry_id


def _parse_dates(call: ServiceCall) -> set[date]:
    """Parse dates from a service call. Supports single date or date range."""
    dates: set[date] = set()

    if "date" in call.data:
        dates.add(date.fromisoformat(call.data["date"]))

    if "start_date" in call.data and "end_date" in call.data:
        start = date.fromisoformat(call.data["start_date"])
        end = date.fromisoformat(call.data["end_date"])
        current = start
        while current <= end:
            # Only add weekdays (Mon-Fri) — Saturdays are auto-computed
            if current.weekday() < 5:
                dates.add(current)
            current += timedelta(days=1)

    return dates


async def _async_register_services(hass: HomeAssistant) -> None:
    """Register integration services."""
    if hass.services.has_service(DOMAIN, "add_pto"):
        return  # Already registered

    async def handle_add_pto(call: ServiceCall) -> None:
        entry_id = _get_entry_id(hass)
        new_dates = _parse_dates(call)
        hass.data[DOMAIN][entry_id]["pto_dates"].update(new_dates)
        await _async_save_data(hass, entry_id)
        # Trigger sensor updates
        hass.bus.async_fire(f"{DOMAIN}_data_updated")

    async def handle_remove_pto(call: ServiceCall) -> None:
        entry_id = _get_entry_id(hass)
        remove_dates = _parse_dates(call)
        hass.data[DOMAIN][entry_id]["pto_dates"].difference_update(remove_dates)
        await _async_save_data(hass, entry_id)
        hass.bus.async_fire(f"{DOMAIN}_data_updated")

    async def handle_add_sick_leave(call: ServiceCall) -> None:
        entry_id = _get_entry_id(hass)
        new_dates = _parse_dates(call)
        hass.data[DOMAIN][entry_id]["sick_dates"].update(new_dates)
        await _async_save_data(hass, entry_id)
        hass.bus.async_fire(f"{DOMAIN}_data_updated")

    async def handle_remove_sick_leave(call: ServiceCall) -> None:
        entry_id = _get_entry_id(hass)
        remove_dates = _parse_dates(call)
        hass.data[DOMAIN][entry_id]["sick_dates"].difference_update(remove_dates)
        await _async_save_data(hass, entry_id)
        hass.bus.async_fire(f"{DOMAIN}_data_updated")

    hass.services.async_register(DOMAIN, "add_pto", handle_add_pto)
    hass.services.async_register(DOMAIN, "remove_pto", handle_remove_pto)
    hass.services.async_register(DOMAIN, "add_sick_leave", handle_add_sick_leave)
    hass.services.async_register(DOMAIN, "remove_sick_leave", handle_remove_sick_leave)
