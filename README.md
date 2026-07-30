# Industrial Turbine Predictive Monitoring & SCADA Alert System

An enterprise-grade SCADA and industrial predictive analytics platform engineered for thermal power plant turbines. The platform combines real-time sensory ingestion (WebSocket & MQTT simulation), multi-step recursive forecasting using **XGBoost Regressors**, explainable AI with **SHAP**, automated threshold safety alerts, maintenance dispatch integration (mock SAP PM/CMMS), and interactive P&ID turbine schematics.

---

## System Architecture

```text
Turbine-Parameter-Prediction-and-Alert-Interface/
├── backend/
│   ├── app/
│   │   ├── ml/                 # XGBoost predictor, feature engineering & training
│   │   ├── models/             # SQLAlchemy ORM models (Units, Readings, Alerts, Audit)
│   │   ├── routes/             # REST API routes (Auth, Units, Forecast, Telemetry, etc.)
│   │   ├── services/           # Prediction orchestration, CMMS dispatch, Ingestion loop
│   │   └── utils/              # RBAC decorators & response handlers
│   ├── tests/                  # Pytest automated test suites
│   ├── run.py                  # Backend application entry point (Flask-SocketIO)
│   ├── requirements.txt        # Backend dependencies
│   ├── Dockerfile              # Container definition for web service
│   └── docker-compose.yml      # Multi-container orchestration (PostgreSQL, Redis, Celery)
│
└── frontend/
    ├── css/                    # Industrial SCADA stylesheets (scada.css, layout.css, components.css)
    ├── js/
    │   ├── api.js              # Centralized API client & JWT interceptors
    │   ├── app.js              # Application router, WebSockets & health monitor
    │   ├── auth.js             # Session state & RBAC helpers
    │   ├── charts.js           # Dual-zone time-series Chart.js renderer
    │   └── views/              # Modular view components (Dashboard, Units, Forecast, Alerts, etc.)
    ├── index.html              # Single-page SCADA operational console
    └── login.html              # Industrial authentication terminal
```

---

## Key Features

1. **Multi-Step Recursive 3-Hour Forecasting**:
   - Reads 30 chronological sensor observations.
   - Extracts 17 time-series features (lags, rolling averages, volatility, rate of change, slope).
   - Recursively projects 12 future steps (15-minute intervals = 3 Hours ahead) via `XGBRegressor`.
2. **Explainable AI (SHAP)**:
   - Evaluates tree attribution at each forecast step to show the top 3 driving features.
3. **Automated Safety & Alerting**:
   - Evaluates warning and critical limit breaches along the predicted trajectory.
   - Calculates estimated Time-to-Breach (ETA).
   - Mock CMMS integration: dispatches simulated work orders to SAP PM on critical alerts.
4. **Interactive P&ID Schematic**:
   - Real-time SVG turbine diagram displaying live bearing vibration and temperature overlays via WebSocket events.
5. **Role-Based Access Control (RBAC)**:
   - `admin`: Full station management, unit provisioning, parameter configuration, user administration.
   - `engineer`: Parameter inspection, 3-hour forecasting, manual data imports, model retraining.
   - `operator`: Real-time telemetry monitoring, manual gauge ingestion, alert acknowledgement.

---

## Quickstart Guide

### 1. Prerequisites
- Python 3.10+ (Recommended: Python 3.12)
- Modern web browser (Chrome, Edge, Firefox)

### 2. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations / seed initial accounts
python seed.py

# Launch backend server (runs on http://localhost:5000)
python run.py
```

### 3. Frontend Setup
In a new terminal window:
```bash
cd frontend

# Serve static files on port 3000
python -m http.server 3000
```
Open **[http://localhost:3000/login.html](http://localhost:3000/login.html)** in your browser.

---

## Default Login Credentials

| Role | Username | Password |
| :--- | :--- | :--- |
| **Administrator** | `admin` | `Admin@1234` |
| **Engineer** | `engineer1` | `Engineer@1234` |
| **Operator** | `operator1` | `Operator@1234` |

---

## Running Automated Tests

Run the backend test suite:
```bash
cd backend
python -m pytest
```
All 13 test suites cover authentication, unit provisioning, telemetry ingestion, alert handling, and XGBoost recursive forecasting.
