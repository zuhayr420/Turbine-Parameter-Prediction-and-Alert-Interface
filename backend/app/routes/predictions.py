from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.models.parameter import Parameter
from app.models.prediction import Prediction
from app.models.unit import Unit
from app.services.prediction_service import PredictionService
from app.utils.response import success_response, error_response

predictions_bp = Blueprint('predictions', __name__, url_prefix='/api')

@predictions_bp.route('/units/<int:unit_id>/parameters/<int:parameter_id>/predict', methods=['POST'])
@jwt_required()
def predict_parameter(unit_id, parameter_id):
    """
    Executes a 3-hour XGBoost forecast for a specific unit parameter.
    Optionally reads custom `inputs` from JSON payload.
    """
    body = request.get_json(silent=True) or {}
    custom_inputs = body.get('inputs') or body.get('readings') or body.get('historical_values')
    horizon_hours = body.get('horizon_hours')
    interval_mins = body.get('interval_minutes')

    result = PredictionService.predict_for_parameter(
        unit_id=unit_id,
        parameter_id=parameter_id,
        custom_inputs=custom_inputs,
        horizon_hours=horizon_hours,
        interval_mins=interval_mins
    )
    status = result.get('status')

    if status == 'insufficient_data':
        return error_response(
            code="INSUFFICIENT_DATA",
            message=result.get('message', "At least 30 historical observations are required."),
            status_code=422,
            details={'required': result.get('required', 30), 'available': result.get('available', 0)}
        )
    elif status == 'model_unavailable':
        return error_response(
            code="MODEL_UNAVAILABLE",
            message=result.get('message', "No trained XGBoost model is available for this parameter."),
            status_code=503
        )
    elif status == 'error':
        return error_response(
            code=result.get('code', 'PREDICTION_ERROR'),
            message=result.get('message', 'Failed generating 3-hour XGBoost prediction.'),
            status_code=400
        )

    return success_response(result)

@predictions_bp.route('/forecast', methods=['POST'])
@predictions_bp.route('/predict', methods=['POST'])
@jwt_required(optional=True)
def direct_forecast():
    """
    Direct XGBoost Forecasting Endpoint:
    Reads arbitrary input readings from JSON payload and predicts the next 3 hours in advance.
    
    Request Body:
    {
      "inputs": [4.1, 4.2, 4.15, ... 30 values ...],
      "parameter_key": "bearing_vibration",
      "parameter_name": "Bearing Vibration",
      "measurement_unit": "mm/s",
      "warning_threshold": 4.5,
      "critical_threshold": 7.0,
      "horizon_hours": 3,
      "interval_minutes": 15
    }
    """
    body = request.get_json(silent=True) or {}
    inputs = body.get('inputs') or body.get('readings') or body.get('values')

    if not inputs or not isinstance(inputs, list):
        return error_response(
            code="INVALID_INPUTS",
            message="Please provide a non-empty list of input observations under 'inputs'.",
            status_code=400
        )

    parameter_key = body.get('parameter_key', 'bearing_vibration')
    parameter_name = body.get('parameter_name', 'Turbine Parameter')
    measurement_unit = body.get('measurement_unit', 'unit')
    warning_threshold = float(body.get('warning_threshold', 60.0)) if body.get('warning_threshold') is not None else None
    critical_threshold = float(body.get('critical_threshold', 80.0)) if body.get('critical_threshold') is not None else None
    horizon_hours = int(body.get('horizon_hours', 3))
    interval_mins = int(body.get('interval_minutes', 15))

    result = PredictionService.predict_direct_inputs(
        inputs=inputs,
        parameter_key=parameter_key,
        parameter_name=parameter_name,
        measurement_unit=measurement_unit,
        warning_threshold=warning_threshold,
        critical_threshold=critical_threshold,
        horizon_hours=horizon_hours,
        interval_mins=interval_mins
    )

    if result.get('status') == 'error':
        return error_response(
            code=result.get('code', 'FORECAST_FAILED'),
            message=result.get('message', 'Failed generating forecast.'),
            status_code=400
        )

    return success_response(result)

@predictions_bp.route('/forecast/sample', methods=['GET'])
def get_sample_inputs():
    """
    Provides a sample 30-observation input payload for demonstration and testing.
    """
    # 30 simulated readings of bearing vibration with a slight upward trend
    import numpy as np
    base = 3.5
    sample_inputs = [round(float(base + i * 0.08 + np.sin(i * 0.5) * 0.15), 4) for i in range(30)]

    return success_response({
        'description': 'Sample 30-observation input window for 3-hour XGBoost prediction',
        'inputs': sample_inputs,
        'parameter_key': 'bearing_vibration',
        'parameter_name': 'Bearing 1 Vibration',
        'measurement_unit': 'mm/s',
        'warning_threshold': 4.5,
        'critical_threshold': 7.0,
        'horizon_hours': 3,
        'interval_minutes': 15
    })

@predictions_bp.route('/units/<int:unit_id>/predict', methods=['POST'])
@jwt_required()
def predict_unit(unit_id):
    """
    Runs 3-hour XGBoost forecasts for all configured parameters of the unit.
    """
    unit = Unit.query.get(unit_id)
    if not unit:
        return error_response("UNIT_NOT_FOUND", f"Unit {unit_id} not found.", 404)

    params = Parameter.query.filter_by(unit_id=unit_id, enabled=True).all()
    results = []
    errors = []

    for p in params:
        res = PredictionService.predict_for_parameter(unit_id, p.id)
        if res.get('status') == 'success':
            results.append(res)
        else:
            errors.append({
                'parameter_id': p.id,
                'parameter_name': p.name,
                'status': res.get('status'),
                'message': res.get('message')
            })

    return success_response({
        'unit_id': unit_id,
        'predictions': results,
        'skipped_or_errors': errors
    })

@predictions_bp.route('/units/<int:unit_id>/parameters/<int:parameter_id>/predictions', methods=['GET'])
@jwt_required()
def get_parameter_predictions(unit_id, parameter_id):
    limit = int(request.args.get('limit', 24))
    preds = Prediction.query.filter_by(unit_id=unit_id, parameter_id=parameter_id)\
        .order_by(Prediction.generated_at.desc(), Prediction.prediction_horizon.asc()).limit(limit).all()

    return success_response({
        'predictions': [p.to_dict() for p in preds]
    })

@predictions_bp.route('/units/<int:unit_id>/predictions', methods=['GET'])
@jwt_required()
def get_unit_predictions(unit_id):
    unit = Unit.query.get(unit_id)
    if not unit:
        return error_response("UNIT_NOT_FOUND", f"Unit {unit_id} not found.", 404)

    # Get most recent prediction run for each parameter
    params = Parameter.query.filter_by(unit_id=unit_id).all()
    output = []
    for p in params:
        preds = Prediction.query.filter_by(unit_id=unit_id, parameter_id=p.id)\
            .order_by(Prediction.generated_at.desc(), Prediction.prediction_horizon.asc()).limit(12).all()
        if preds:
            output.append({
                'parameter_id': p.id,
                'parameter_name': p.name,
                'measurement_unit': p.measurement_unit,
                'predictions': [pr.to_dict() for pr in preds]
            })

    return success_response({'unit_id': unit_id, 'forecasts': output})
