# Industrial Turbine Predictive Monitoring & Alert System - Backend

Production-grade, modular Flask REST API backend for thermal power station turbine monitoring, featuring recursive time-series forecasting via XGBoost, 30-observation sliding window validation, predictive threshold-breach alerts, time-to-breach calculation, and role-based access control (RBAC).

---

## 1. Architecture Overview

The system follows a strict layered architecture:
```text
Routes (HTTP / JWT / Serialization)
   ↓
Services (Prediction, Alerts, Trends, Reports, Simulation)
   ↓
ML Engine (XGBoost Regressor, Feature Engineering, Rolling Window)
   ↓
Database Models (SQLAlchemy ORM, Time-series Indexes)
```

```text
backend/
├── run.py                     # Application entry point
├── config.py                  # Environment-driven configuration (Dev/Test/Prod)
├── requirements.txt           # Production dependencies
├── seed.py                    # Database seeding and initial ML training script
├── .env.example               # Environment template
│
├── app/
│   ├── __init__.py            # Flask App factory with blueprints and error handlers
│   ├── extensions.py          # SQLAlchemy, JWTManager, CORS
│   │
│   ├── models/                # Database entities
│   │   ├── user.py            # User credentials, roles (admin, engineer, operator)
│   │   ├── unit.py            # Turbine Units (capacity, status, downtime)
│   │   ├── parameter.py       # Configurable parameters & operating thresholds
│   │   ├── reading.py         # Time-series telemetry readings (indexed)
│   │   ├── prediction.py      # Stored multi-step forecasts
│   │   └── alert.py           # Alerts & Model metadata
│   │
│   ├── routes/                # REST API Endpoints
│   │   ├── auth.py            # /api/auth (login, me, logout)
│   │   ├── users.py           # /api/users (CRUD, RBAC)
│   │   ├── units.py           # /api/units (CRUD, soft delete)
│   │   ├── parameters.py      # /api/units/<id>/parameters
│   │   ├── readings.py        # /api/units/<id>/readings & history
│   │   ├── predictions.py     # /api/units/<id>/predict & forecasting
│   │   ├── alerts.py          # /api/alerts (list, acknowledge, resolve)
│   │   ├── reports.py         # /api/reports (unit summary & CSV export)
│   │   ├── dashboard.py       # /api/dashboard (KPIs, plant overview)
│   │   ├── models_mgmt.py     # /api/models (metadata & retraining)
│   │   ├── data_import.py     # /api/data/import (bulk CSV ingestion)
│   │   └── system.py          # /api/health & /api/system/simulate
│   │
│   ├── services/              # Business logic
│   │   ├── prediction_service.py # 30-window validator, multi-step orchestration
│   │   ├── alert_service.py      # Predictive alert engine & deduplication
│   │   ├── trend_service.py      # Trend classification (STABLE, INCREASING, etc.)
│   │   ├── report_service.py     # CSV and operational report generation
│   │   ├── notification_service.py # SMTP email notification dispatcher
│   │   └── simulation_service.py # Synthetic telemetry generation (SIMULATION tag)
│   │
│   ├── ml/                    # Machine Learning Core
│   │   ├── feature_engineering.py # Lags, rolling statistics, rate of change, slope
│   │   ├── predictor.py       # In-memory cached multi-step XGBoost predictor
│   │   ├── trainer.py         # Time-series chronological split trainer (MAE, RMSE, R2)
│   │   └── models/            # Stored .joblib artifacts & metadata JSON
│   │
│   └── utils/
│       ├── decorators.py      # Role-based security decorators (@admin_required, etc.)
│       ├── response.py        # Standardized API response formatters
│       └── validators.py      # Range, email, numeric, and timestamp validators
│
├── data/                      # SQLite storage for development (swappable to Postgres)
└── tests/                     # Automated pytest suite (9 tests)
```

---

## 2. Setup & Installation

### Prerequisites
- Python 3.11 or 3.12 (64-bit)
- `pip` and virtual environment support

### 1. Create Virtual Environment & Install Dependencies
```bash
# In backend directory
py -3.12 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```

### 3. Seed Database & Train Initial ML Models
Runs table creation, seeds 3 roles (`admin`, `engineer1`, `operator1`), creates 3 turbine units, creates 6 parameters, inserts 60 simulated historical observations, and trains initial XGBoost models:
```bash
python seed.py
```

### 4. Run Automated Tests
```bash
$env:PYTHONPATH="."
pytest -v tests
```

### 5. Start Development Server
```bash
python run.py
```
Backend API will be accessible at: `http://localhost:5000`

---

## 3. Production Deployment (WSGI)

Run with Gunicorn (Linux/Containers) or Waitress (Windows):

### Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app('production')"
```

### Waitress (Windows):
```bash
pip install waitress
waitress-serve --port=5000 "app:create_app('production')"
```

---

## 4. Default Seed Credentials

| Role | Username | Password |
|------|----------|----------|
| Administrator | `admin` | `Admin@1234` |
| Engineer | `engineer1` | `Engineer@1234` |
| Operator | `operator1` | `Operator@1234` |

---

## 5. Key API Endpoints Reference

### Authentication
- `POST /api/auth/login` - Authenticate user & retrieve JWT access token
- `GET /api/auth/me` - Current user details (Protected)
- `POST /api/auth/logout` - Invalidate session

### Dashboard & Health
- `GET /api/health` - Public subsystem health check (`database`, `prediction_engine`, `alert_engine`, `model_service`)
- `GET /api/dashboard` - High-level KPIs, unit statuses, and active alerts summary

### Turbines & Parameters
- `GET /api/units` - List all units
- `POST /api/units` - Create new turbine (Admin only)
- `GET /api/units/<id>` - Turbine details
- `PUT /api/units/<id>` - Update turbine (Admin only)
- `DELETE /api/units/<id>` - Soft/hard delete (Admin only)
- `GET /api/units/<id>/parameters` - Monitored parameters for turbine
- `POST /api/units/<id>/parameters` - Add new parameter (Admin only)

### Telemetry & Historical Readings
- `POST /api/units/<id>/readings` - Ingest current parameter reading
- `GET /api/units/<id>/readings` - Retrieve current values for all parameters
- `GET /api/units/<id>/parameters/<param_id>/history` - Parameter time-series history
- `POST /api/data/import` - Bulk CSV historical readings upload

### Machine Learning Forecasting & Alerts
- `POST /api/units/<id>/parameters/<param_id>/predict` - Generate 3-hour forecast (12 points at 15-min intervals) using 30 historical window
- `POST /api/units/<id>/predict` - Forecast all parameters for turbine
- `GET /api/alerts` - List alerts (filterable by severity & status)
- `PUT /api/alerts/<id>/acknowledge` - Acknowledge alert
- `PUT /api/alerts/<id>/resolve` - Resolve alert & re-evaluate unit status
- `POST /api/models/train/<param_id>` - Retrain XGBoost model on historical data
- `GET /api/models` - View model metadata and validation metrics (MAE, RMSE, R2)

---

## 6. Machine Learning Architecture Details

1. **Sliding Window Validation**:
   - Queries the latest 30 chronological readings: $[t-29, t-28, \dots, t-1, t]$.
   - If $<30$ valid readings exist, returns HTTP 422 `INSUFFICIENT_DATA` with available and required counts.
2. **Feature Engineering**:
   - Identical transformations applied during training and inference:
     - Lags: `lag_1`, `lag_2`, `lag_3`, `lag_5`
     - Rolling metrics: Mean, Std (windows 5, 15, 30), Min, Max
     - Rate of change: Relative to `lag_5`
     - Short-term trend slope: Linear fit over 5 most recent observations
3. **Multi-Step Recursive Forecasting**:
   - Predicts $t+1$ (15 minutes into future).
   - Appends prediction to rolling window and re-extracts features.
   - Iterates 12 times to produce the 3-hour trajectory.
4. **Predictive Alert & Time-to-Breach**:
   - Scans the 12 forecast points against warning and critical thresholds.
   - Calculates exact `expected_breach_minutes` and estimated breach timestamp.
   - Deduplicates active alerts to prevent flooding the control room console.
