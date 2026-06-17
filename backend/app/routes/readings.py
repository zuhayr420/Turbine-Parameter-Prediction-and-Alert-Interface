from datetime import datetime, timezone
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.reading import Reading
from app.models.parameter import Parameter
from app.models.unit import Unit
from app.utils.response import success_response, error_response
from app.utils.validators import parse_iso_datetime, validate_numeric

readings_bp = Blueprint('readings', __name__, url_prefix='/api')

@readings_bp.route('/units/<int:unit_id>/readings', methods=['POST'])
@jwt_required()
def add_reading(unit_id):
    unit = Unit.query.get(unit_id)
    if not unit:
        return error_response("UNIT_NOT_FOUND", f"Unit {unit_id} not found.", 404)

    data = request.get_json() or {}
    parameter_id = data.get('parameter_id')
    value = data.get('value')
    ts_raw = data.get('timestamp')
    data_source = data.get('data_source', 'MANUAL').upper()

    if parameter_id is None or value is None:
        return error_response("MISSING_FIELDS", "parameter_id and value are required.", 400)

    parameter = Parameter.query.filter_by(id=parameter_id, unit_id=unit_id).first()
    if not parameter:
        return error_response("PARAMETER_NOT_FOUND", f"Parameter {parameter_id} does not belong to unit {unit_id}.", 404)

    ok, num_or_err = validate_numeric(value, parameter.minimum_value, parameter.maximum_value)
    if not ok:
        return error_response("INVALID_VALUE", num_or_err, 400)

    timestamp = parse_iso_datetime(ts_raw) if ts_raw else datetime.now(timezone.utc)
    if not timestamp:
        return error_response("INVALID_TIMESTAMP", "Timestamp must be ISO 8601 formatted.", 400)

    reading = Reading(
        unit_id=unit_id,
        parameter_id=parameter_id,
        value=num_or_err,
        timestamp=timestamp,
        data_source=data_source
    )
    db.session.add(reading)
    db.session.commit()

    return success_response({
        'reading': reading.to_dict(),
        'parameter': parameter.name,
        'value': reading.value,
        'unit': parameter.measurement_unit,
        'timestamp': reading.timestamp.isoformat()
    }, message="Reading recorded.", status_code=201)

@readings_bp.route('/units/<int:unit_id>/readings', methods=['GET'])
@jwt_required()
def get_current_readings(unit_id):
    """
    Returns the latest reading for each enabled parameter of the unit.
    """
    unit = Unit.query.get(unit_id)
    if not unit:
        return error_response("UNIT_NOT_FOUND", f"Unit {unit_id} not found.", 404)

    params = Parameter.query.filter_by(unit_id=unit_id, enabled=True).all()
    results = []

    for p in params:
        latest = Reading.query.filter_by(unit_id=unit_id, parameter_id=p.id)\
            .order_by(Reading.timestamp.desc()).first()

        if latest:
            results.append({
                'parameter_id': p.id,
                'parameter_key': p.parameter_key,
                'parameter': p.name,
                'value': latest.value,
                'unit': p.measurement_unit,
                'timestamp': latest.timestamp.isoformat(),
                'data_source': latest.data_source,
                'warning_threshold': p.warning_threshold,
                'critical_threshold': p.critical_threshold
            })
        else:
            results.append({
                'parameter_id': p.id,
                'parameter_key': p.parameter_key,
                'parameter': p.name,
                'value': None,
                'unit': p.measurement_unit,
                'timestamp': None,
                'data_source': None,
                'warning_threshold': p.warning_threshold,
                'critical_threshold': p.critical_threshold
            })

    return success_response({'current_readings': results, 'unit': unit.to_dict()})

@readings_bp.route('/units/<int:unit_id>/parameters/<int:parameter_id>/history', methods=['GET'])
@jwt_required()
def get_parameter_history(unit_id, parameter_id):
    limit = int(request.args.get('limit', 100))
    readings = Reading.query.filter_by(unit_id=unit_id, parameter_id=parameter_id)\
        .order_by(Reading.timestamp.desc()).limit(limit).all()

    # Return chronologically
    return success_response({
        'history': [r.to_dict() for r in reversed(readings)]
    })
