# Industrial Turbine Predictive Monitoring & Alert System - Frontend

Professional, high-density SCADA/industrial analytics frontend application for monitoring thermal power station turbines, interacting with XGBoost multi-step recursive forecasts, managing predictive threshold breaches, and auditing plant telemetry.

---

## 1. Design & SCADA Principles

- **Industrial Control Room Aesthetics**: Deep charcoal palette (`#0f172a`), steel slate panels (`#1e293b`), square borders, high information density, and restrained technical status badges (`NORMAL`, `WARNING`, `CRITICAL`, `OFFLINE`).
- **Strictly No Neon / Futuristic Clichés**: Focused on operational clarity, telemetry accuracy, and fast decision-support for plant operators and maintenance engineers.
- **Dual-Zone Time-Series Visualization**: Chart.js charts rendering solid lines for measured historical observations ($t-29 \dots t$), dashed lines for the recursive 3-hour forecast ($t+15 \dots t+180$ minutes), and horizontal warning/critical threshold boundary lines.

---

## 2. Directory Structure

```text
frontend/
├── index.html                # Main application container / Single-Page SCADA Dashboard
├── login.html                # Industrial authentication page
├── css/
│   ├── scada.css             # Theme variables, typography, badges, buttons, tables, panels
│   ├── layout.css            # Navigation sidebar, top telemetry bar, view containers
│   └── components.css        # KPI cards, turbine cards, trend tags, chart panels
└── js/
    ├── api.js                # REST API Client handling JWT auth and all backend endpoints
    ├── auth.js               # User role and session manager
    ├── charts.js             # Dual-zone time-series Chart.js renderer
    ├── views/
    │   ├── dashboard.js      # Plant KPIs, unit overview grid, active predictive alerts
    │   ├── unit_detail.js    # Operational stats, current parameters, live forecasting
    │   ├── predictions.js    # Dedicated 3-hour multi-step forecasting & breach ETA view
    │   ├── alerts.js         # Central alerts table, filtering, acknowledge/resolve actions
    │   ├── telemetry_input.js# Operator live parameter entry & "Record & Predict" action
    │   ├── historical.js     # Time-series query & CSV export
    │   ├── reports.js        # Audit report generation & PDF/print export
    │   ├── admin.js          # Turbine provisioning, model metrics, user administration
    │   └── simulation.js     # Dev simulation harness (Normal, Warning, Critical trends)
    └── app.js                # View router and system health heartbeat monitor
```

---

## 3. Running Locally

The frontend connects directly to the Flask backend running at `http://localhost:5000`.

### Step 1: Ensure the Backend is Running
```bash
# In backend directory
.\.venv\Scripts\python.exe run.py
```

### Step 2: Serve Frontend Files
You can open `login.html` directly in any modern browser, or serve it using Python's built-in HTTP server:
```bash
# In frontend directory
python -m http.server 3000
```
Open `http://localhost:3000/login.html` in your browser.

---

## 4. Default Login Credentials

| Role | Username | Password | Access Level |
|------|----------|----------|--------------|
| Administrator | `admin` | `Admin@1234` | Full access (provisioning, users, settings, models) |
| Engineer | `engineer1` | `Engineer@1234` | Predictions, alerts, reports, simulation |
| Operator | `operator1` | `Operator@1234` | Telemetry input, predictions, alerts, reports |
