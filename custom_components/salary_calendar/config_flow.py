"""Config flow for Salary Calendar integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

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
)


def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Build the config schema with optional defaults."""
    d = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_HOURLY_RATE,
                default=d.get(CONF_HOURLY_RATE, DEFAULT_HOURLY_RATE),
            ): vol.Coerce(float),
            vol.Required(
                CONF_AVERAGE_HOURLY_RATE,
                default=d.get(CONF_AVERAGE_HOURLY_RATE, DEFAULT_AVERAGE_HOURLY_RATE),
            ): vol.Coerce(float),
            vol.Required(
                CONF_DAILY_HOURS,
                default=d.get(CONF_DAILY_HOURS, DEFAULT_DAILY_HOURS),
            ): vol.Coerce(float),
            vol.Required(
                CONF_TAX_RATE,
                default=d.get(CONF_TAX_RATE, DEFAULT_TAX_RATE),
            ): vol.Coerce(float),
            vol.Required(
                CONF_PTO_MULTIPLIER,
                default=d.get(CONF_PTO_MULTIPLIER, DEFAULT_PTO_MULTIPLIER),
            ): vol.Coerce(float),
            vol.Required(
                CONF_PTO_DAYS_PER_YEAR,
                default=d.get(CONF_PTO_DAYS_PER_YEAR, DEFAULT_PTO_DAYS_PER_YEAR),
            ): vol.Coerce(int),
        }
    )


class SalaryCalendarConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Salary Calendar."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        # Only allow one instance
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title="Salary Calendar", data=user_input)

        return self.async_show_form(step_id="user", data_schema=_schema())

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return SalaryCalendarOptionsFlow(config_entry)


class SalaryCalendarOptionsFlow(OptionsFlow):
    """Handle options flow for Salary Calendar."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**self._config_entry.data, **self._config_entry.options}
        return self.async_show_form(step_id="init", data_schema=_schema(current))
