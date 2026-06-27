import io
import csv
from datetime import datetime
from app.models.unit import Unit
from app.models.parameter import Parameter
from app.models.reading import Reading
from app.models.prediction import Prediction
from app.models.alert import Alert

class ReportService:
    @staticmethod
    def generate_unit_report_data(unit_id: int, start_date=None, end_date=None) -> dict:
        unit = Unit.query.get(unit_id)
        if not unit:
            return None

        params = Parameter.query.filter_by(unit_id=unit_id).all()
        param_data = []

        for p in params:
            latest_reading = Reading.query.filter_by(
                unit_id=unit_id,
                parameter_id=p.id
            ).order_by(Reading.timestamp.desc()).first()

            latest_predictions = Prediction.query.filter_by(
                unit_id=unit_id,
                parameter_id=p.id
            ).order_by(Prediction.generated_at.desc(), Prediction.prediction_horizon.asc()).limit(12).all()

            active_alerts = Alert.query.filter_by(
                unit_id=unit_id,
                parameter_id=p.id,
                status='ACTIVE'
            ).all()

            param_data.append({
                'parameter': p.to_dict(),
                'latest_reading': latest_reading.to_dict() if latest_reading else None,
                'forecast': [pr.to_dict() for pr in latest_predictions],
                'active_alerts': [a.to_dict() for a in active_alerts]
            })

        return {
            'generated_at': datetime.utcnow().isoformat(),
            'unit': unit.to_dict(),
            'parameters': param_data
        }

    @staticmethod
    def export_readings_csv(unit_id: int, parameter_id: int = None, limit: int = 500) -> str:
        query = Reading.query.filter_by(unit_id=unit_id)
        if parameter_id:
            query = query.filter_by(parameter_id=parameter_id)
        readings = query.order_by(Reading.timestamp.desc()).limit(limit).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['reading_id', 'unit_id', 'parameter_id', 'parameter_name', 'value', 'unit', 'timestamp', 'data_source'])

        for r in readings:
            p_name = r.parameter.name if r.parameter else ""
            p_unit = r.parameter.measurement_unit if r.parameter else ""
            writer.writerow([r.id, r.unit_id, r.parameter_id, p_name, r.value, p_unit, r.timestamp.isoformat(), r.data_source])

        return output.getvalue()
