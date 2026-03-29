"""Constants for the Salary Calendar integration."""

DOMAIN = "salary_calendar"

# Configuration keys
CONF_HOURLY_RATE = "hourly_rate"
CONF_AVERAGE_HOURLY_RATE = "average_hourly_rate"
CONF_DAILY_HOURS = "daily_hours"
CONF_TAX_RATE = "tax_rate"
CONF_PTO_MULTIPLIER = "pto_multiplier"
CONF_PTO_DAYS_PER_YEAR = "pto_days_per_year"

# Default values
DEFAULT_HOURLY_RATE = 41.0
DEFAULT_AVERAGE_HOURLY_RATE = 41.0
DEFAULT_DAILY_HOURS = 7.5
DEFAULT_TAX_RATE = 35.19
DEFAULT_PTO_MULTIPLIER = 1.25
DEFAULT_PTO_DAYS_PER_YEAR = 30

# Storage
STORAGE_KEY = f"{DOMAIN}.pto_sick"
STORAGE_VERSION = 1
