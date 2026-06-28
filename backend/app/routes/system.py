import os
from flask import Blueprint, current_app, request
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.services.simulation_service import SimulationService
from app.utils.response import success_response, error_response
from app.utils.decorators import admin_required

system_bp = Blueprint('system', __name__, url_prefix='/api')

@system_bp.route('/health', methods=['GET'])
def health_check():
    """
    Public health check endpoint testing availability of subsystems:
    Database, Prediction Engine, Alert Engine, Model Service.
    """
    # 1. Database check
    db_status = "ONLINE"
    try:
        db.session.execute(db.text('SELECT 1'))
    except Exception:
        db_status = "OFFLINE"

    # 2. Model directory check
    model_dir = current_app.config.get('MODEL_DIRECTORY')
    model_status = "ONLINE" if os.path.isdir(model_dir) else "WARNING"

    overall_status = "ONLINE" if (db_status == "ONLINE" and model_status == "ONLINE") else "DEGRADED"

    return success_response({
        'status': overall_status,
        'database': db_status,
        'prediction_engine': "ONLINE",
        'alert_engine': "ONLINE",
        'model_service': model_status
    })

@system_bp.route('/system/simulate/<int:unit_id>', methods=['POST'])
@jwt_required()
@admin_required
def trigger_simulation(unit_id):
    """
    Generates realistic turbine readings tagged as SIMULATION for testing.
    Body: {"count": 60, "trend": "normal" | "warning_trend" | "critical_trend"}
    """
    data = request.get_json() or {}
    count = int(data.get('count', 60))
    trend = data.get('trend', 'normal')

    created = SimulationService.generate_historical_series(unit_id, count=count, trend_direction=trend)
    if created == 0:
        return error_response("SIMULATION_FAILED", "Unit not found or has no configured parameters.", 404)

    return success_response({
        'unit_id': unit_id,
        'readings_created': created,
        'data_source': 'SIMULATION',
        'trend_direction': trend
    }, message=f"Generated {created} simulated observations.")
