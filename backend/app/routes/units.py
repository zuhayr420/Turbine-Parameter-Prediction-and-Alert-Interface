from datetime import datetime, date
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.unit import Unit
from app.utils.response import success_response, error_response
from app.utils.decorators import admin_required

units_bp = Blueprint('units', __name__, url_prefix='/api/units')

@units_bp.route('', methods=['GET'])
@jwt_required()
def list_units():
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    query = Unit.query
    if not include_inactive:
        query = query.filter_by(active=True)
    units = query.all()
    return success_response({'units': [u.to_dict() for u in units]})

@units_bp.route('/<int:unit_id>', methods=['GET'])
@jwt_required()
def get_unit(unit_id):
    unit = Unit.query.get(unit_id)
    if not unit:
        return error_response("UNIT_NOT_FOUND", f"Unit with id {unit_id} not found.", 404)
    return success_response({'unit': unit.to_dict()})

@units_bp.route('', methods=['POST'])
@jwt_required()
@admin_required
def create_unit():
    data = request.get_json() or {}
    unit_code = data.get('unit_code')
    unit_name = data.get('unit_name')
    station_id = data.get('station_id')

    if not unit_code or not unit_name:
        return error_response("MISSING_FIELDS", "unit_code and unit_name are required.", 400)

    if Unit.query.filter_by(unit_code=unit_code).first():
        return error_response("DUPLICATE_CODE", f"Unit with code '{unit_code}' already exists.", 409)

    # Validate station_id if provided
    if station_id is not None:
        from app.models.station import Station
        if not Station.query.get(station_id):
            return error_response("INVALID_STATION", "Provided station_id does not exist.", 400)

    unit = Unit(
        unit_code=unit_code.strip(),
        unit_name=unit_name.strip(),
        station_id=station_id,
        location=data.get('location'),
        manufacturer=data.get('manufacturer'),
        model=data.get('model'),
        capacity_mw=float(data.get('capacity_mw', 210.0)),
        status=data.get('status', 'RUNNING'),
        active=True
    )
    db.session.add(unit)
    db.session.commit()
    return success_response({'unit': unit.to_dict()}, message="Unit created successfully.", status_code=201)

@units_bp.route('/<int:unit_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_unit(unit_id):
    unit = Unit.query.get(unit_id)
    if not unit:
        return error_response("UNIT_NOT_FOUND", "Unit not found.", 404)

    data = request.get_json() or {}
    if 'unit_name' in data:
        unit.unit_name = data['unit_name']
    if 'station_id' in data:
        from app.models.station import Station
        if not Station.query.get(data['station_id']):
            return error_response("INVALID_STATION", "Provided station_id does not exist.", 400)
        unit.station_id = data['station_id']
    if 'location' in data:
        unit.location = data['location']
    if 'manufacturer' in data:
        unit.manufacturer = data['manufacturer']
    if 'model' in data:
        unit.model = data['model']
    if 'capacity_mw' in data:
        unit.capacity_mw = float(data['capacity_mw'])
    if 'status' in data:
        unit.status = data['status']
    if 'active' in data:
        unit.active = bool(data['active'])
    if 'downtime_hours' in data:
        unit.downtime_hours = float(data['downtime_hours'])

    db.session.commit()
    return success_response({'unit': unit.to_dict()}, message="Unit updated.")

@units_bp.route('/<int:unit_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_unit(unit_id):
    unit = Unit.query.get(unit_id)
    if not unit:
        return error_response("UNIT_NOT_FOUND", "Unit not found.", 404)

    hard = request.args.get('hard', 'false').lower() == 'true'
    if hard:
        db.session.delete(unit)
        db.session.commit()
        return success_response(message="Unit permanently deleted.")
    else:
        unit.active = False
        unit.status = 'OFFLINE'
        db.session.commit()
        return success_response(message="Unit deactivated (soft deleted).")
