from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.station import Station
from app.utils.response import success_response, error_response
from app.utils.decorators import admin_required

stations_bp = Blueprint('stations', __name__, url_prefix='/api/stations')

@stations_bp.route('', methods=['GET'])
@jwt_required()
def list_stations():
    stations = Station.query.all()
    return success_response({'stations': [s.to_dict() for s in stations]})

@stations_bp.route('/<int:station_id>', methods=['GET'])
@jwt_required()
def get_station(station_id):
    station = Station.query.get(station_id)
    if not station:
        return error_response("NOT_FOUND", "Station not found.", 404)
    return success_response({'station': station.to_dict()})


@stations_bp.route('', methods=['POST'])
@jwt_required()
@admin_required
def create_station():
    data = request.get_json() or {}
    name = data.get('name')
    location = data.get('location')

    if not name:
        return error_response("MISSING_FIELDS", "name is required.", 400)

    if Station.query.filter_by(name=name).first():
        return error_response("DUPLICATE_STATION", f"Station '{name}' already exists.", 409)

    station = Station(name=name, location=location)
    db.session.add(station)
    db.session.commit()

    return success_response({'station': station.to_dict()}, status_code=201)

@stations_bp.route('/<int:station_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_station(station_id):
    station = Station.query.get(station_id)
    if not station:
        return error_response("NOT_FOUND", "Station not found.", 404)
        
    data = request.get_json() or {}
    if 'name' in data:
        station.name = data['name']
    if 'location' in data:
        station.location = data['location']
    if 'active' in data:
        station.active = bool(data['active'])
        
    db.session.commit()
    return success_response({'station': station.to_dict()})

@stations_bp.route('/<int:station_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_station(station_id):
    station = Station.query.get(station_id)
    if not station:
        return error_response("NOT_FOUND", "Station not found.", 404)
        
    db.session.delete(station)
    db.session.commit()
    return success_response(message="Station deleted.")
