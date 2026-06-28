from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.models.unit import Unit
from app.models.alert import Alert
from app.models.parameter import Parameter
from app.utils.response import success_response

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('', methods=['GET'])
@jwt_required()
def get_dashboard_summary():
    units = Unit.query.all()
    total_units = len(units)
    running_units = sum(1 for u in units if u.status == 'RUNNING' and u.active)
    warning_units = sum(1 for u in units if u.status == 'WARNING' and u.active)
    critical_units = sum(1 for u in units if u.status == 'CRITICAL' and u.active)
    offline_units = sum(1 for u in units if (u.status == 'OFFLINE' or not u.active))

    active_alerts = Alert.query.filter_by(status='ACTIVE').count()
    critical_alerts = Alert.query.filter_by(status='ACTIVE', severity='CRITICAL').count()
    warning_alerts = Alert.query.filter_by(status='ACTIVE', severity='WARNING').count()

    total_parameters = Parameter.query.filter_by(enabled=True).count()

    return success_response({
        'total_units': total_units,
        'running_units': running_units,
        'warning_units': warning_units,
        'critical_units': critical_units,
        'offline_units': offline_units,
        'active_alerts': active_alerts,
        'critical_alerts': critical_alerts,
        'warning_alerts': warning_alerts,
        'parameters_monitored': total_parameters,
        'system_health': 'ONLINE',
        'units': [u.to_dict() for u in units]
    })
