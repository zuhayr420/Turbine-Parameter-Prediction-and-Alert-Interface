from flask import Blueprint, Response, request
from flask_jwt_extended import jwt_required
from app.services.report_service import ReportService
from app.utils.response import success_response, error_response

reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')

@reports_bp.route('/units/<int:unit_id>', methods=['GET'])
@jwt_required()
def get_unit_report(unit_id):
    data = ReportService.generate_unit_report_data(unit_id)
    if not data:
        return error_response("UNIT_NOT_FOUND", "Unit not found.", 404)
    return success_response({'report': data})

@reports_bp.route('/units/<int:unit_id>/export/csv', methods=['GET'])
@jwt_required()
def export_readings_csv(unit_id):
    param_id = request.args.get('parameter_id', type=int)
    limit = request.args.get('limit', default=500, type=int)

    csv_data = ReportService.export_readings_csv(unit_id, parameter_id=param_id, limit=limit)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=turbine_unit_{unit_id}_readings.csv"}
    )
