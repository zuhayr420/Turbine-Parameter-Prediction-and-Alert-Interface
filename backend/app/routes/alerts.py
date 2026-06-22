from datetime import datetime, timezone
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.alert import Alert
from app.models.unit import Unit
from app.utils.response import success_response, error_response

alerts_bp = Blueprint('alerts', __name__, url_prefix='/api')

@alerts_bp.route('/alerts', methods=['GET'])
@jwt_required()
def list_alerts():
    status = request.args.get('status')
    severity = request.args.get('severity')
    limit = int(request.args.get('limit', 100))

    query = Alert.query
    if status:
        query = query.filter_by(status=status.upper())
    if severity:
        query = query.filter_by(severity=severity.upper())

    alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
    return success_response({'alerts': [a.to_dict() for a in alerts]})

@alerts_bp.route('/units/<int:unit_id>/alerts', methods=['GET'])
@jwt_required()
def list_unit_alerts(unit_id):
    status = request.args.get('status')
    query = Alert.query.filter_by(unit_id=unit_id)
    if status:
        query = query.filter_by(status=status.upper())

    alerts = query.order_by(Alert.created_at.desc()).all()
    return success_response({'unit_id': unit_id, 'alerts': [a.to_dict() for a in alerts]})

@alerts_bp.route('/alerts/<int:alert_id>/acknowledge', methods=['PUT'])
@jwt_required()
def acknowledge_alert(alert_id):
    alert = Alert.query.get(alert_id)
    if not alert:
        return error_response("ALERT_NOT_FOUND", "Alert not found.", 404)

    alert.status = 'ACKNOWLEDGED'
    db.session.commit()
    return success_response({'alert': alert.to_dict()}, message="Alert acknowledged.")

@alerts_bp.route('/alerts/<int:alert_id>/resolve', methods=['PUT'])
@jwt_required()
def resolve_alert(alert_id):
    alert = Alert.query.get(alert_id)
    if not alert:
        return error_response("ALERT_NOT_FOUND", "Alert not found.", 404)

    alert.status = 'RESOLVED'
    alert.resolved_at = datetime.now(timezone.utc)
    db.session.commit()

    # Recalculate unit status after resolving
    from app.services.alert_service import AlertService
    if alert.unit:
        AlertService.recalculate_unit_status(alert.unit)

    return success_response({'alert': alert.to_dict()}, message="Alert marked as resolved.")
