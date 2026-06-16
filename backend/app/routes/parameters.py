from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.parameter import Parameter
from app.models.unit import Unit
from app.utils.response import success_response, error_response
from app.utils.decorators import admin_required

parameters_bp = Blueprint('parameters', __name__, url_prefix='/api')

@parameters_bp.route('/units/<int:unit_id>/parameters', methods=['GET'])
@jwt_required()
def get_unit_parameters(unit_id):
    unit = Unit.query.get(unit_id)
    if not unit:
        return error_response("UNIT_NOT_FOUND", f"Unit {unit_id} not found.", 404)
    params = Parameter.query.filter_by(unit_id=unit_id).all()
    return success_response({'parameters': [p.to_dict() for p in params]})

@parameters_bp.route('/units/<int:unit_id>/parameters', methods=['POST'])
@jwt_required()
@admin_required
def create_parameter(unit_id):
    unit = Unit.query.get(unit_id)
    if not unit:
        return error_response("UNIT_NOT_FOUND", f"Unit {unit_id} not found.", 404)

    data = request.get_json() or {}
    name = data.get('name')
    param_key = data.get('parameter_key')
    measurement_unit = data.get('measurement_unit')
    warning_th = data.get('warning_threshold')
    critical_th = data.get('critical_threshold')

    if not name or not param_key or not measurement_unit or warning_th is None or critical_th is None:
        return error_response("MISSING_FIELDS", "name, parameter_key, measurement_unit, warning_threshold, and critical_threshold are required.", 400)

    clean_key = param_key.strip().lower().replace(' ', '_')
    if Parameter.query.filter_by(unit_id=unit_id, parameter_key=clean_key).first():
        return error_response("DUPLICATE_PARAMETER", f"Parameter key '{clean_key}' already configured for this unit.", 409)

    param = Parameter(
        unit_id=unit_id,
        name=name.strip(),
        parameter_key=clean_key,
        description=data.get('description'),
        measurement_unit=measurement_unit.strip(),
        warning_threshold=float(warning_th),
        critical_threshold=float(critical_th),
        minimum_value=float(data['minimum_value']) if 'minimum_value' in data and data['minimum_value'] is not None else None,
        maximum_value=float(data['maximum_value']) if 'maximum_value' in data and data['maximum_value'] is not None else None,
        enabled=bool(data.get('enabled', True)),
        alert_enabled=bool(data.get('alert_enabled', True))
    )
    db.session.add(param)
    db.session.commit()
    return success_response({'parameter': param.to_dict()}, message="Parameter created successfully.", status_code=201)

@parameters_bp.route('/parameters/<int:parameter_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_parameter(parameter_id):
    param = Parameter.query.get(parameter_id)
    if not param:
        return error_response("PARAMETER_NOT_FOUND", "Parameter not found.", 404)

    data = request.get_json() or {}
    if 'name' in data:
        param.name = data['name']
    if 'description' in data:
        param.description = data['description']
    if 'measurement_unit' in data:
        param.measurement_unit = data['measurement_unit']
    if 'warning_threshold' in data:
        param.warning_threshold = float(data['warning_threshold'])
    if 'critical_threshold' in data:
        param.critical_threshold = float(data['critical_threshold'])
    if 'minimum_value' in data:
        param.minimum_value = float(data['minimum_value']) if data['minimum_value'] is not None else None
    if 'maximum_value' in data:
        param.maximum_value = float(data['maximum_value']) if data['maximum_value'] is not None else None
    if 'enabled' in data:
        param.enabled = bool(data['enabled'])
    if 'alert_enabled' in data:
        param.alert_enabled = bool(data['alert_enabled'])

    db.session.commit()
    return success_response({'parameter': param.to_dict()}, message="Parameter updated successfully.")

@parameters_bp.route('/parameters/<int:parameter_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_parameter(parameter_id):
    param = Parameter.query.get(parameter_id)
    if not param:
        return error_response("PARAMETER_NOT_FOUND", "Parameter not found.", 404)

    db.session.delete(param)
    db.session.commit()
    return success_response(message="Parameter deleted successfully.")
