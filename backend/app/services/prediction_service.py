import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from flask import current_app
from app.extensions import db
from app.models.reading import Reading
from app.models.parameter import Parameter
from app.models.unit import Unit
from app.models.prediction import Prediction
from app.ml.predictor import XGBoostPredictor
from app.services.trend_service import TrendService
from app.services.alert_service import AlertService

logger = logging.getLogger(__name__)

class PredictionService:
    _predictor_instance = None

    @classmethod
    def get_predictor(cls) -> XGBoostPredictor:
        if cls._predictor_instance is None:
            model_dir = current_app.config.get('MODEL_DIRECTORY')
            cls._predictor_instance = XGBoostPredictor(model_dir=model_dir)
        return cls._predictor_instance

    @classmethod
    def predict_for_parameter(
        cls,
        unit_id: int,
        parameter_id: int,
        custom_inputs: Optional[List[float]] = None,
        horizon_hours: Optional[int] = None,
        interval_mins: Optional[int] = None
    ) -> dict:
        """
        Reads input readings and forecasts future values for the next 3 hours in advance
        using the XGBoost model.
        Supports both database readings and user-supplied custom inputs.
        """
        unit = Unit.query.get(unit_id)
        if not unit:
            return {'status': 'error', 'code': 'UNIT_NOT_FOUND', 'message': f'Unit {unit_id} not found.'}

        parameter = Parameter.query.filter_by(id=parameter_id, unit_id=unit_id).first()
        if not parameter:
            return {'status': 'error', 'code': 'PARAMETER_NOT_FOUND', 'message': f'Parameter {parameter_id} not found for unit {unit_id}.'}

        history_window_size = current_app.config.get('HISTORY_WINDOW', 30)
        current_time = datetime.now(timezone.utc)
        predictor = cls.get_predictor()
        param_key = parameter.parameter_key

        if custom_inputs and len(custom_inputs) > 0:
            # Read user-supplied inputs
            values_30 = XGBoostPredictor.normalize_input_window(custom_inputs, required_len=history_window_size)
            current_value = float(values_30[-1])
        else:
            # Retrieve latest readings from database
            readings_query = Reading.query.filter_by(
                unit_id=unit_id,
                parameter_id=parameter_id
            ).order_by(Reading.timestamp.desc()).limit(history_window_size).all()

            available_count = len(readings_query)
            if available_count < history_window_size:
                return {
                    'status': 'insufficient_data',
                    'required': history_window_size,
                    'available': available_count,
                    'message': f'At least {history_window_size} historical observations are required.'
                }

            if not predictor.is_model_available(param_key):
                return {
                    'status': 'model_unavailable',
                    'message': f'No trained XGBoost model is available for parameter {param_key}.'
                }

            readings_chronological = list(reversed(readings_query))
            values_30 = [r.value for r in readings_chronological]
            latest_reading = readings_chronological[-1]
            current_value = latest_reading.value
            if latest_reading.timestamp:
                current_time = latest_reading.timestamp

        interval_mins = interval_mins or current_app.config.get('PREDICTION_INTERVAL_MINUTES', 15)
        horizon_hours = horizon_hours or current_app.config.get('PREDICTION_HORIZON_HOURS', 3)
        total_steps = int((horizon_hours * 60) / interval_mins)

        # Execute 3-Hour Recursive XGBoost Forecast
        forecast_result = predictor.forecast_recursive(
            parameter_key=param_key,
            historical_30=values_30,
            horizon_steps=total_steps,
            step_minutes=interval_mins,
            auto_create_model=bool(custom_inputs)
        )

        if not forecast_result:
            return {
                'status': 'error',
                'code': 'FORECAST_EXECUTION_FAILED',
                'message': f'Failed executing 3-hour XGBoost prediction for {param_key}.'
            }

        predictions_list = forecast_result['predictions']
        model_version = forecast_result['model_version']

        # Store predictions in DB
        try:
            for pt in predictions_list:
                pred_time = current_time + timedelta(minutes=pt['minutes'])
                db_pred = Prediction(
                    unit_id=unit.id,
                    parameter_id=parameter.id,
                    predicted_value=pt['value'],
                    prediction_time=pred_time,
                    generated_at=datetime.now(timezone.utc),
                    model_version=model_version,
                    prediction_horizon=pt['minutes']
                )
                db.session.add(db_pred)
            db.session.commit()
        except Exception as db_err:
            db.session.rollback()
            logger.warning(f"Could not persist prediction records to DB: {db_err}")

        # Trend analysis across the 3-hour horizon
        predicted_3h_val = predictions_list[-1]['value'] if predictions_list else current_value
        trend_info = TrendService.analyze_trend(current_value, predicted_3h_val, values_30)

        # Predictive Alert evaluation
        alert_info = AlertService.evaluate_predictive_alert(
            unit=unit,
            parameter=parameter,
            current_value=current_value,
            predictions=predictions_list,
            current_time=current_time
        )

        return {
            'status': 'success',
            'unit': {
                'id': unit.id,
                'name': unit.unit_name,
                'code': unit.unit_code
            },
            'parameter': {
                'id': parameter.id,
                'name': parameter.name,
                'key': parameter.parameter_key,
                'unit': parameter.measurement_unit
            },
            'current_value': round(current_value, 4),
            'inputs_read': values_30,
            'historical_points': len(values_30),
            'prediction_horizon_hours': horizon_hours,
            'prediction_interval_minutes': interval_mins,
            'trend': trend_info['trend'],
            'rate_of_change': trend_info['rate_of_change'],
            'predictions': predictions_list,
            'alert': alert_info,
            'model': {
                'type': 'XGBoost Regressor (Recursive 3-Hour Horizon)',
                'version': model_version
            }
        }

    @classmethod
    def predict_direct_inputs(
        cls,
        inputs: List[float],
        parameter_key: str = 'bearing_vibration',
        parameter_name: str = 'Bearing Vibration',
        measurement_unit: str = 'mm/s',
        warning_threshold: float = 4.5,
        critical_threshold: float = 7.0,
        horizon_hours: int = 3,
        interval_mins: int = 15
    ) -> dict:
        """
        Direct forecasting API:
        Reads arbitrary input observations and predicts the next 3 hours ahead using XGBoost.
        Does not require existing database records.
        """
        values_30 = XGBoostPredictor.normalize_input_window(inputs, required_len=30)
        current_value = float(values_30[-1])
        current_time = datetime.now(timezone.utc)
        total_steps = int((horizon_hours * 60) / interval_mins)

        predictor = cls.get_predictor()
        forecast_result = predictor.forecast_recursive(
            parameter_key=parameter_key,
            historical_30=values_30,
            horizon_steps=total_steps,
            step_minutes=interval_mins,
            auto_create_model=True
        )

        if not forecast_result:
            return {
                'status': 'error',
                'code': 'FORECAST_FAILED',
                'message': 'Failed generating forecast from provided inputs.'
            }

        predictions_list = forecast_result['predictions']
        model_version = forecast_result['model_version']

        # Determine breach predictions
        breach_status = 'NORMAL'
        expected_breach_mins = None
        predicted_breach_val = None

        for pt in predictions_list:
            v = pt['value']
            if critical_threshold and v >= critical_threshold:
                breach_status = 'CRITICAL'
                expected_breach_mins = pt['minutes']
                predicted_breach_val = v
                break
            elif warning_threshold and v >= warning_threshold and breach_status != 'CRITICAL':
                breach_status = 'WARNING'
                expected_breach_mins = pt['minutes']
                predicted_breach_val = v

        predicted_3h_val = predictions_list[-1]['value'] if predictions_list else current_value
        trend_info = TrendService.analyze_trend(current_value, predicted_3h_val, values_30)

        return {
            'status': 'success',
            'parameter': {
                'key': parameter_key,
                'name': parameter_name,
                'unit': measurement_unit,
                'warning_threshold': warning_threshold,
                'critical_threshold': critical_threshold
            },
            'current_value': round(current_value, 4),
            'inputs_read': values_30,
            'prediction_horizon_hours': horizon_hours,
            'prediction_interval_minutes': interval_mins,
            'trend': trend_info['trend'],
            'rate_of_change': trend_info['rate_of_change'],
            'predictions': predictions_list,
            'alert': {
                'severity': breach_status,
                'current_value': current_value,
                'predicted_3h_value': predicted_3h_val,
                'expected_breach_minutes': expected_breach_mins,
                'expected_breach_value': predicted_breach_val
            },
            'model': {
                'type': 'XGBoost Regressor (Recursive 3-Hour Horizon)',
                'version': model_version
            }
        }
