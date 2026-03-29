# Salary Calendar for Home Assistant

[![Tests](https://github.com/jarahkon/ha-salary-calendar/actions/workflows/tests.yml/badge.svg)](https://github.com/jarahkon/ha-salary-calendar/actions/workflows/tests.yml)
[![HACS Validation](https://github.com/jarahkon/ha-salary-calendar/actions/workflows/validate-hacs.yml/badge.svg)](https://github.com/jarahkon/ha-salary-calendar/actions/workflows/validate-hacs.yml)
[![Hassfest Validation](https://github.com/jarahkon/ha-salary-calendar/actions/workflows/validate-hassfest.yml/badge.svg)](https://github.com/jarahkon/ha-salary-calendar/actions/workflows/validate-hassfest.yml)

A custom Home Assistant integration that calculates and displays your monthly salary based on Finnish employment rules — including public holidays, PTO with Saturday counting, sick leave, and configurable tax rates.

## Features

- **Next Paycheck** — countdown to pay day with gross/net breakdown
- **Current Month Accrual** — salary earned so far this month with forecast
- **PTO Tracking** — remaining days with Finnish Saturday rule (Mon–Sat counting)
- **Sick Leave Tracking** — paid at average hourly rate
- **Year-to-Date Summary** — monthly and cumulative gross/net
- **Finnish Public Holidays** — automatically calculated including Easter-based moveable dates
- **Custom Lovelace Card** — tabbed UI with paycheck, accrual, PTO, and YTD views
- **HA Calendar Entity** — PTO, sick leave, holidays, and pay dates on your calendar
- **Fully Configurable** — hourly rate, tax %, PTO allowance, and more via UI

## Installation

### HACS (Recommended)

1. Add this repository as a custom repository in HACS
2. Install "Salary Calendar"
3. Restart Home Assistant
4. Go to Settings → Devices & Services → Add Integration → "Salary Calendar"
5. Configure your salary parameters

### Manual

1. Copy `custom_components/salary_calendar/` to your HA `custom_components/` directory
2. Copy `custom_cards/salary-calendar-card.js` to your HA `www/` directory
3. Restart Home Assistant
4. Add the integration via Settings → Devices & Services
5. Add the card resource: Settings → Dashboards → Resources → `/local/salary-calendar-card.js` (JavaScript Module)

## Configuration

All parameters are configurable via the UI (Settings → Devices & Services → Salary Calendar → Configure):

| Parameter | Default | Description |
|---|---|---|
| Hourly rate | €41.00 | Normal working day hourly rate |
| Average hourly rate | €41.00 | Rate for holidays, sick leave, PTO base |
| Daily hours | 7.5 | Working hours per day |
| Tax rate | 35.19% | Total tax + tax-like deductions |
| PTO multiplier | 1.25 | Multiplier for PTO daily pay |
| PTO days/year | 30 | Annual PTO allowance |

## Sensors

| Entity | Description |
|---|---|
| `sensor.salary_next_pay_date` | Next pay date with countdown |
| `sensor.salary_pay_period_gross` | Gross salary for the pay period |
| `sensor.salary_pay_period_net` | Net salary for the pay period |
| `sensor.salary_current_month_accrued` | Salary accrued this month so far |
| `sensor.salary_pto_remaining` | Remaining PTO days |
| `sensor.salary_ytd_gross` | Year-to-date gross salary |
| `sensor.salary_ytd_net` | Year-to-date net salary |

## Services

| Service | Description |
|---|---|
| `salary_calendar.add_pto` | Mark days as PTO (single date or range) |
| `salary_calendar.remove_pto` | Remove PTO from days |
| `salary_calendar.add_sick_leave` | Mark days as sick leave |
| `salary_calendar.remove_sick_leave` | Remove sick leave from days |

### Service Examples

```yaml
# Add a single PTO day
service: salary_calendar.add_pto
data:
  date: "2026-07-01"

# Add a PTO range (weekdays only — Saturdays auto-computed)
service: salary_calendar.add_pto
data:
  start_date: "2026-07-06"
  end_date: "2026-07-17"

# Add sick leave
service: salary_calendar.add_sick_leave
data:
  start_date: "2026-03-10"
  end_date: "2026-03-12"
```

## Lovelace Card

Add to your dashboard:

```yaml
type: custom:salary-calendar-card
```

The card has four tabs:
- **Paycheck** — next pay date countdown, gross/tax/net, day breakdown
- **This Month** — accrued salary, progress bar, month forecast
- **PTO** — remaining days circle, used/planned breakdown
- **YTD** — monthly gross/net table with totals

## Salary Calculation Rules

- **Pay date**: 15th of each month (previous Friday if weekend)
- **Pay period**: Previous completed calendar month
- **Workday pay**: hourly_rate × daily_hours
- **Holiday/sick pay**: average_hourly_rate × daily_hours
- **PTO pay**: pto_multiplier × average_hourly_rate × daily_hours
- **PTO Saturdays**: If a Friday is PTO, the following Saturday is auto-counted as PTO (Finnish Vuosilomalaki rule). Saturday PTO pays at the PTO rate.
- **Public holidays**: Only weekday holidays affect salary. Saturday/Sunday holidays have no impact.
- **Priority order**: public holiday > sick leave > PTO > PTO Saturday > workday > weekend
- **Net salary**: gross × (1 − tax_rate/100)

## Finnish Public Holidays

Automatically calculated per year (14 total):

| Holiday | Date | Type |
|---|---|---|
| New Year's Day | January 1 | Fixed |
| Epiphany | January 6 | Fixed |
| Good Friday | Easter − 2 | Moveable |
| Easter Sunday | Varies | Moveable |
| Easter Monday | Easter + 1 | Moveable |
| May Day | May 1 | Fixed |
| Ascension Day | Easter + 39 | Moveable (always Thursday) |
| Midsummer Eve | Fri between Jun 19–25 | Moveable (always Friday) |
| Midsummer Day | Sat between Jun 20–26 | Moveable (always Saturday) |
| All Saints' Day | Sat between Oct 31–Nov 6 | Moveable (always Saturday) |
| Independence Day | December 6 | Fixed |
| Christmas Eve | December 24 | Fixed |
| Christmas Day | December 25 | Fixed |
| St. Stephen's Day | December 26 | Fixed |

## Project Structure

```
ha-salary-calendar/
├── .github/workflows/
│   ├── tests.yml              # CI — pytest on Python 3.12 & 3.13
│   ├── validate-hacs.yml      # HACS repository validation
│   └── validate-hassfest.yml  # HA integration manifest validation
├── custom_components/salary_calendar/
│   ├── brand/                 # Integration branding
│   │   ├── icon.png           #   Icon for HA integrations list
│   │   └── logo.png           #   Logo for HA integrations list
│   ├── salary/                # Core engine (no HA dependencies)
│   │   ├── holidays.py        #   Finnish public holiday computation
│   │   ├── workdays.py        #   Day classification & PTO Saturday logic
│   │   └── calculator.py      #   Gross/net salary, YTD, pay date logic
│   ├── __init__.py            # Integration setup, services, storage
│   ├── calendar.py            # Calendar entity
│   ├── config_flow.py         # UI configuration flow
│   ├── const.py               # Constants and defaults
│   ├── manifest.json          # HA integration manifest
│   ├── sensor.py              # 7 sensor entities
│   ├── services.yaml          # Service definitions
│   ├── strings.json           # UI strings
│   └── translations/en.json   # English translations
├── custom_cards/
│   └── salary-calendar-card.js  # Lovelace card
├── tests/
│   ├── conftest.py            # Test configuration
│   ├── test_holidays.py       # Holiday calculation tests
│   ├── test_workdays.py       # Day classification tests
│   └── test_calculator.py     # Salary math & pay date tests
├── hacs.json                  # HACS metadata
├── pyproject.toml             # Project config + dev dependencies
└── README.md
```

## Development

### Setup

```bash
# Clone and set up environment
git clone https://github.com/jarahkon/ha-salary-calendar.git
cd ha-salary-calendar
uv venv
uv sync --extra dev
```

### Running Tests

```bash
uv run pytest tests/ -v
```

The test suite covers the core salary engine (101 tests):
- **Holiday computation** — Easter dates, Midsummer, All Saints' Day, all 14 holidays across multiple years
- **Day classification** — workday counts, PTO/sick/holiday precedence, PTO Saturday logic
- **Salary calculation** — pay rates, gross/net, tax, accrued salary, YTD, pay date adjustment

### CI Pipelines

| Workflow | Purpose |
|---|---|
| **Tests** | Runs pytest on Python 3.12 and 3.13 |
| **HACS Validation** | Validates repository structure for HACS compatibility |
| **Hassfest** | Validates `manifest.json` against HA standards |

## License

MIT
