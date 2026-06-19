import random
from datetime import datetime, timezone, timedelta
from app.extensions import db
from app.models.reading import Reading
from app.models.parameter import Parameter
from app.models.unit import Unit

class SimulationService:
    BASE_PARAM_CONFIGS = {
        'vibration': {'base': 2.8, 'noise': 0.15, 'unit': 'mm/s', 'warn': 4.0, 'crit': 5.0, 'min': 0.0, 'max': 10.0, 'name': 'Vibration'},
        'pressure': {'base': 12.2, 'noise': 0.2, 'unit': 'MPa', 'warn': 16.0, 'crit': 18.0, 'min': 0.0, 'max': 25.0, 'name': 'Steam Pressure'},
        'lube_temperature': {'base': 61.5, 'noise': 0.4, 'unit': '°C', 'warn': 70.0, 'crit': 75.0, 'min': 20.0, 'max': 100.0, 'name': 'Lube Oil Temperature'},
        'bearing_temperature': {'base': 68.0, 'noise': 0.5, 'unit': '°C', 'warn': 80.0, 'crit': 85.0, 'min': 20.0, 'max': 120.0, 'name': 'Bearing Temperature'},
        'rpm': {'base': 3000.0, 'noise': 5.0, 'unit': 'RPM', 'warn': 3150.0, 'crit': 3300.0, 'min': 0.0, 'max': 4000.0, 'name': 'Rotor Speed'},
        'load': {'base': 185.0, 'noise': 2.0, 'unit': 'MW', 'warn': 210.0, 'crit': 225.0, 'min': 0.0, 'max': 250.0, 'name': 'Power Output'}
    }

    @classmethod
    def generate_historical_series(cls, unit_id: int, count: int = 60, trend_direction="normal"):
        """
        Generates `count` simulated chronological readings (spaced by 15 mins) for all parameters of unit.
        Clearly tags data_source = 'SIMULATION'.
        trend_direction: 'normal', 'warning_trend', 'critical_trend'
        """
        unit = Unit.query.get(unit_id)
        if not unit:
            return 0

        parameters = Parameter.query.filter_by(unit_id=unit_id).all()
        now = datetime.now(timezone.utc)
        total_created = 0

        for param in parameters:
            key = param.parameter_key
            cfg = cls.BASE_PARAM_CONFIGS.get(key, {
                'base': (param.warning_threshold * 0.7),
                'noise': 0.2,
                'min': param.minimum_value or 0.0,
                'max': param.maximum_value or 100.0
            })
            base_val = cfg['base']
            noise_scale = cfg['noise']

            for i in range(count):
                ts = now - timedelta(minutes=(count - 1 - i) * 15)
                # Introduce slight upward slope if warning/critical trend is requested
                trend_factor = 0.0
                if trend_direction == "warning_trend" and key in ('vibration', 'lube_temperature'):
                    trend_factor = (i / count) * (param.warning_threshold - base_val) * 1.1
                elif trend_direction == "critical_trend" and key in ('vibration', 'lube_temperature'):
                    trend_factor = (i / count) * (param.critical_threshold - base_val) * 1.15

                val = base_val + trend_factor + random.gauss(0, noise_scale)
                if param.minimum_value is not None:
                    val = max(param.minimum_value, val)
                if param.maximum_value is not None:
                    val = min(param.maximum_value, val)

                reading = Reading(
                    unit_id=unit.id,
                    parameter_id=param.id,
                    value=round(val, 4),
                    timestamp=ts,
                    data_source='SIMULATION'
                )
                db.session.add(reading)
                total_created += 1

        db.session.commit()
        return total_created
