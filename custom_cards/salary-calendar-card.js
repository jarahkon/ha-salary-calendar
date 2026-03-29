/**
 * Salary Calendar Card for Home Assistant
 *
 * A custom Lovelace card that displays salary information,
 * pay date countdown, and PTO/sick leave tracking.
 */

class SalaryCalendarCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
    this._activeTab = "paycheck";
  }

  static getConfigElement() {
    return document.createElement("salary-calendar-card-editor");
  }

  static getStubConfig() {
    return {};
  }

  setConfig(config) {
    this._config = config;
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _getEntity(suffix) {
    if (!this._hass) return null;
    const states = this._hass.states;
    // Find the entity matching the suffix
    const key = Object.keys(states).find((k) =>
      k.startsWith("sensor.salary_") && k.endsWith(suffix)
    );
    return key ? states[key] : null;
  }

  _render() {
    if (!this._hass) return;

    const payDate = this._getEntity("next_pay_date");
    const gross = this._getEntity("pay_period_gross");
    const net = this._getEntity("pay_period_net");
    const accrued = this._getEntity("current_month_accrued");
    const pto = this._getEntity("pto_remaining");
    const ytdGross = this._getEntity("ytd_gross");
    const ytdNet = this._getEntity("ytd_net");

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          --card-bg: var(--ha-card-background, var(--card-background-color, #1c1c1c));
          --text-primary: var(--primary-text-color, #e1e1e1);
          --text-secondary: var(--secondary-text-color, #9e9e9e);
          --accent: var(--primary-color, #03a9f4);
          --accent-green: #4caf50;
          --accent-orange: #ff9800;
          --accent-red: #f44336;
          --divider: var(--divider-color, rgba(255,255,255,0.12));
        }

        ha-card {
          padding: 0;
          overflow: hidden;
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 20px 8px;
        }

        .card-title {
          font-size: 1.1em;
          font-weight: 500;
          color: var(--text-primary);
        }

        .tabs {
          display: flex;
          gap: 0;
          border-bottom: 1px solid var(--divider);
          padding: 0 16px;
        }

        .tab {
          padding: 8px 16px;
          font-size: 0.85em;
          color: var(--text-secondary);
          cursor: pointer;
          border-bottom: 2px solid transparent;
          transition: all 0.2s;
          background: none;
          border-top: none;
          border-left: none;
          border-right: none;
          font-family: inherit;
        }

        .tab:hover {
          color: var(--text-primary);
        }

        .tab.active {
          color: var(--accent);
          border-bottom-color: var(--accent);
        }

        .tab-content {
          padding: 16px 20px 20px;
        }

        .pay-hero {
          text-align: center;
          padding: 12px 0 16px;
        }

        .pay-date {
          font-size: 0.9em;
          color: var(--text-secondary);
          margin-bottom: 4px;
        }

        .pay-countdown {
          font-size: 1.8em;
          font-weight: 700;
          color: var(--accent);
          margin-bottom: 2px;
        }

        .pay-countdown-label {
          font-size: 0.8em;
          color: var(--text-secondary);
        }

        .salary-amounts {
          display: flex;
          justify-content: space-around;
          margin: 16px 0;
          padding: 12px 0;
          border-top: 1px solid var(--divider);
          border-bottom: 1px solid var(--divider);
        }

        .salary-amount {
          text-align: center;
        }

        .salary-label {
          font-size: 0.75em;
          color: var(--text-secondary);
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: 4px;
        }

        .salary-value {
          font-size: 1.3em;
          font-weight: 600;
        }

        .salary-value.gross {
          color: var(--text-primary);
        }

        .salary-value.tax {
          color: var(--accent-red);
        }

        .salary-value.net {
          color: var(--accent-green);
        }

        .breakdown {
          margin-top: 12px;
        }

        .breakdown-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 6px 0;
          font-size: 0.85em;
        }

        .breakdown-row + .breakdown-row {
          border-top: 1px solid var(--divider);
        }

        .breakdown-label {
          color: var(--text-secondary);
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .breakdown-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          display: inline-block;
        }

        .breakdown-value {
          color: var(--text-primary);
          font-weight: 500;
        }

        .accrued-bar {
          background: var(--divider);
          border-radius: 4px;
          height: 8px;
          margin: 12px 0;
          overflow: hidden;
        }

        .accrued-fill {
          height: 100%;
          background: var(--accent-green);
          border-radius: 4px;
          transition: width 0.5s ease;
        }

        .pto-hero {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 16px;
          padding: 16px 0;
        }

        .pto-circle {
          width: 80px;
          height: 80px;
          border-radius: 50%;
          border: 4px solid var(--accent);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
        }

        .pto-number {
          font-size: 1.6em;
          font-weight: 700;
          color: var(--accent);
          line-height: 1;
        }

        .pto-unit {
          font-size: 0.65em;
          color: var(--text-secondary);
        }

        .pto-details {
          text-align: left;
        }

        .pto-detail-row {
          font-size: 0.85em;
          color: var(--text-secondary);
          padding: 2px 0;
        }

        .pto-detail-row span {
          color: var(--text-primary);
          font-weight: 500;
        }

        .ytd-section {
          margin-top: 8px;
        }

        .ytd-row {
          display: flex;
          justify-content: space-between;
          padding: 8px 0;
          font-size: 0.85em;
          border-bottom: 1px solid var(--divider);
        }

        .ytd-row:last-child {
          border-bottom: none;
          font-weight: 600;
          font-size: 0.95em;
        }

        .ytd-month {
          color: var(--text-secondary);
        }

        .ytd-gross {
          color: var(--text-primary);
        }

        .ytd-net {
          color: var(--accent-green);
        }

        .unavailable {
          text-align: center;
          padding: 20px;
          color: var(--text-secondary);
          font-style: italic;
        }

        .month-names {
          display: grid;
          grid-template-columns: 1fr 1fr 1fr;
          gap: 0;
        }
      </style>

      <ha-card>
        <div class="card-header">
          <span class="card-title">💰 Salary Calendar</span>
        </div>

        <div class="tabs">
          <button class="tab ${this._activeTab === "paycheck" ? "active" : ""}" data-tab="paycheck">Paycheck</button>
          <button class="tab ${this._activeTab === "current" ? "active" : ""}" data-tab="current">This Month</button>
          <button class="tab ${this._activeTab === "pto" ? "active" : ""}" data-tab="pto">PTO</button>
          <button class="tab ${this._activeTab === "ytd" ? "active" : ""}" data-tab="ytd">YTD</button>
        </div>

        <div class="tab-content">
          ${this._renderTab(payDate, gross, net, accrued, pto, ytdGross, ytdNet)}
        </div>
      </ha-card>
    `;

    // Bind tab clicks
    this.shadowRoot.querySelectorAll(".tab").forEach((tab) => {
      tab.addEventListener("click", (e) => {
        this._activeTab = e.target.dataset.tab;
        this._render();
      });
    });
  }

  _renderTab(payDate, gross, net, accrued, pto, ytdGross, ytdNet) {
    switch (this._activeTab) {
      case "paycheck":
        return this._renderPaycheck(payDate, gross, net);
      case "current":
        return this._renderCurrent(accrued);
      case "pto":
        return this._renderPTO(pto);
      case "ytd":
        return this._renderYTD(ytdGross, ytdNet);
      default:
        return "";
    }
  }

  _renderPaycheck(payDate, gross, net) {
    if (!payDate || !gross || !net) {
      return '<div class="unavailable">Salary sensors unavailable</div>';
    }

    const attrs = gross.attributes || {};
    const netAttrs = net.attributes || {};
    const payAttrs = payDate.attributes || {};

    const countdown = payAttrs.countdown_days ?? "?";
    const payDateStr = payDate.state;
    const payPeriod = attrs.pay_period || "";

    const grossVal = parseFloat(gross.state) || 0;
    const taxVal = parseFloat(netAttrs.tax_amount) || 0;
    const netVal = parseFloat(net.state) || 0;

    const workdays = attrs.workdays || 0;
    const holidays = attrs.public_holiday_days || 0;
    const ptoDays = attrs.pto_days || 0;
    const ptoSatDays = attrs.pto_saturday_days || 0;
    const sickDays = attrs.sick_leave_days || 0;

    const workdayPay = parseFloat(attrs.workday_pay) || 0;
    const holidayPay = parseFloat(attrs.public_holiday_pay) || 0;
    const ptoPay = parseFloat(attrs.pto_pay) || 0;
    const ptoSatPay = parseFloat(attrs.pto_saturday_pay) || 0;
    const sickPay = parseFloat(attrs.sick_leave_pay) || 0;

    const dateObj = new Date(payDateStr + "T00:00:00");
    const friendlyDate = dateObj.toLocaleDateString("en-US", {
      weekday: "short",
      month: "long",
      day: "numeric",
    });

    return `
      <div class="pay-hero">
        <div class="pay-date">Pay date for ${payPeriod}</div>
        <div class="pay-countdown">${countdown}</div>
        <div class="pay-countdown-label">days until ${friendlyDate}</div>
      </div>

      <div class="salary-amounts">
        <div class="salary-amount">
          <div class="salary-label">Gross</div>
          <div class="salary-value gross">${this._fmt(grossVal)}</div>
        </div>
        <div class="salary-amount">
          <div class="salary-label">Tax</div>
          <div class="salary-value tax">−${this._fmt(taxVal)}</div>
        </div>
        <div class="salary-amount">
          <div class="salary-label">Net</div>
          <div class="salary-value net">${this._fmt(netVal)}</div>
        </div>
      </div>

      <div class="breakdown">
        ${workdays > 0 ? this._breakdownRow("#4caf50", `${workdays} workdays`, workdayPay) : ""}
        ${holidays > 0 ? this._breakdownRow("#ff9800", `${holidays} public holidays`, holidayPay) : ""}
        ${ptoDays > 0 ? this._breakdownRow("#03a9f4", `${ptoDays} PTO days`, ptoPay) : ""}
        ${ptoSatDays > 0 ? this._breakdownRow("#29b6f6", `${ptoSatDays} PTO Saturdays`, ptoSatPay) : ""}
        ${sickDays > 0 ? this._breakdownRow("#f44336", `${sickDays} sick days`, sickPay) : ""}
      </div>
    `;
  }

  _renderCurrent(accrued) {
    if (!accrued) {
      return '<div class="unavailable">Accrual sensor unavailable</div>';
    }

    const attrs = accrued.attributes || {};
    const accruedVal = parseFloat(accrued.state) || 0;
    const forecast = parseFloat(attrs.month_forecast_gross) || 0;
    const forecastNet = parseFloat(attrs.month_forecast_net) || 0;
    const worked = attrs.days_worked || 0;
    const remaining = attrs.remaining_workdays || 0;
    const total = worked + remaining;
    const pct = total > 0 ? (worked / total) * 100 : 0;

    return `
      <div class="pay-hero">
        <div class="pay-date">Accrued as of ${attrs.as_of_date || "today"}</div>
        <div class="pay-countdown">${this._fmt(accruedVal)}</div>
        <div class="pay-countdown-label">${worked} days worked, ${remaining} remaining</div>
      </div>

      <div class="accrued-bar">
        <div class="accrued-fill" style="width: ${pct}%"></div>
      </div>

      <div class="salary-amounts">
        <div class="salary-amount">
          <div class="salary-label">Month Forecast</div>
          <div class="salary-value gross">${this._fmt(forecast)}</div>
        </div>
        <div class="salary-amount">
          <div class="salary-label">Forecast Net</div>
          <div class="salary-value net">${this._fmt(forecastNet)}</div>
        </div>
      </div>

      <div class="breakdown">
        ${attrs.pto_days > 0 ? this._breakdownRow("#03a9f4", `${attrs.pto_days} PTO days this month`, null) : ""}
        ${attrs.sick_days > 0 ? this._breakdownRow("#f44336", `${attrs.sick_days} sick days this month`, null) : ""}
      </div>
    `;
  }

  _renderPTO(pto) {
    if (!pto) {
      return '<div class="unavailable">PTO sensor unavailable</div>';
    }

    const attrs = pto.attributes || {};
    const remaining = parseInt(pto.state) || 0;
    const total = attrs.total || 30;
    const used = attrs.used || 0;
    const planned = attrs.planned || 0;
    const weeks = attrs.weeks_equivalent || 0;

    const ptoColor = remaining > 10 ? "var(--accent)" : remaining > 5 ? "var(--accent-orange)" : "var(--accent-red)";

    return `
      <div class="pto-hero">
        <div class="pto-circle" style="border-color: ${ptoColor}">
          <div class="pto-number" style="color: ${ptoColor}">${remaining}</div>
          <div class="pto-unit">days left</div>
        </div>
        <div class="pto-details">
          <div class="pto-detail-row">Total: <span>${total} days</span></div>
          <div class="pto-detail-row">Used: <span>${used} days</span></div>
          <div class="pto-detail-row">Planned: <span>${planned} days</span></div>
          <div class="pto-detail-row">≈ <span>${weeks} weeks</span> remaining</div>
        </div>
      </div>
    `;
  }

  _renderYTD(ytdGross, ytdNet) {
    if (!ytdGross || !ytdNet) {
      return '<div class="unavailable">YTD sensors unavailable</div>';
    }

    const grossAttrs = ytdGross.attributes || {};
    const months = grossAttrs.months || [];

    const monthNames = [
      "Jan", "Feb", "Mar", "Apr", "May", "Jun",
      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ];

    let rows = months
      .map(
        (m) => `
      <div class="ytd-row">
        <span class="ytd-month">${monthNames[m.month - 1]}</span>
        <span class="ytd-gross">${this._fmt(m.gross)}</span>
        <span class="ytd-net">${this._fmt(m.net)}</span>
      </div>
    `
      )
      .join("");

    rows += `
      <div class="ytd-row">
        <span class="ytd-month">Total</span>
        <span class="ytd-gross">${this._fmt(parseFloat(ytdGross.state) || 0)}</span>
        <span class="ytd-net">${this._fmt(parseFloat(ytdNet.state) || 0)}</span>
      </div>
    `;

    return `
      <div class="ytd-section">
        <div class="ytd-row" style="font-weight:600; font-size:0.8em; color:var(--text-secondary); border-bottom: 1px solid var(--divider);">
          <span>Month</span>
          <span>Gross</span>
          <span>Net</span>
        </div>
        ${rows}
      </div>
    `;
  }

  _breakdownRow(color, label, amount) {
    return `
      <div class="breakdown-row">
        <span class="breakdown-label">
          <span class="breakdown-dot" style="background: ${color}"></span>
          ${label}
        </span>
        ${amount !== null ? `<span class="breakdown-value">${this._fmt(amount)}</span>` : ""}
      </div>
    `;
  }

  _fmt(val) {
    return new Intl.NumberFormat("fi-FI", {
      style: "currency",
      currency: "EUR",
    }).format(val);
  }

  getCardSize() {
    return 4;
  }
}

customElements.define("salary-calendar-card", SalaryCalendarCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "salary-calendar-card",
  name: "Salary Calendar",
  description: "Displays salary information, pay date countdown, and PTO tracking",
});
