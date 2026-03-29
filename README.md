# Salary Calendar for Home Assistant

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
| Average hourly rate | €37.00 | Rate for holidays, sick leave, PTO base |
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
- **Net salary**: gross × (1 − tax_rate/100)

## Finnish Public Holidays

Automatically calculated per year:
- New Year's Day, Epiphany, Good Friday, Easter Monday
- May Day, Ascension Day, Midsummer Eve
- All Saints' Day, Independence Day
- Christmas Eve, Christmas Day, St. Stephen's Day
