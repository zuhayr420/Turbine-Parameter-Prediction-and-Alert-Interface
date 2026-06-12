from app.routes.auth import auth_bp
from app.routes.users import users_bp
from app.routes.units import units_bp
from app.routes.parameters import parameters_bp
from app.routes.readings import readings_bp
from app.routes.predictions import predictions_bp
from app.routes.alerts import alerts_bp
from app.routes.reports import reports_bp
from app.routes.dashboard import dashboard_bp
from app.routes.models_mgmt import models_mgmt_bp
from app.routes.data_import import data_import_bp
from app.routes.system import system_bp

__all__ = [
    'auth_bp',
    'users_bp',
    'units_bp',
    'parameters_bp',
    'readings_bp',
    'predictions_bp',
    'alerts_bp',
    'reports_bp',
    'dashboard_bp',
    'models_mgmt_bp',
    'data_import_bp',
    'system_bp'
]

from .stations import stations_bp
