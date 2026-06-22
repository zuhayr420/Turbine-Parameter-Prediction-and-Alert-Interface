import logging
from datetime import datetime, timezone, timedelta
from app.extensions import db
from app.models.alert import Alert
from app.models.parameter import Parameter
from app.models.unit import Unit
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class AlertService:
    @staticmethod
    def evaluate_predictive_alert(
        unit: Unit,
        parameter: Parameter,
        current_value: float,
        predictions: list,
        current_time: datetime = None
    ) -> dict:
        """
        Evaluates current reading and multi-step predictions against warning and critical thresholds.
        Predictions list format: [{'minutes': 15, 'value': 63.8}, ...]
        Returns alert info dict and persists/deduplicates alerts if breach is detected.
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        warning_th = parameter.warning_threshold
        critical_th = parameter.critical_threshold

        severity = "NORMAL"
        threshold_breached = None
        expected_breach_minutes = None
        predicted_breach_value = None

        # 1. Check if current value already breaches critical
        if current_value >= critical_th:
            severity = "CRITICAL"
            threshold_breached = critical_th
            expected_breach_minutes = 0
            predicted_breach_value = current_value
        # 2. Check if current value breaches warning
        elif current_value >= warning_th:
            severity = "WARNING"
            threshold_breached = warning_th
            expected_breach_minutes = 0
            predicted_breach_value = current_value

        # 3. Check predicted trajectory for future breaches (CRITICAL takes priority)
        if severity != "CRITICAL":
            # First look for critical breaches across future points
            for pt in predictions:
                val = pt['value']
                mins = pt['minutes']
                if val >= critical_th:
                    severity = "CRITICAL"
                    threshold_breached = critical_th
                    expected_breach_minutes = mins
                    predicted_breach_value = val
                    break

        if severity == "NORMAL":
            # If no critical, check for warning breaches
            for pt in predictions:
                val = pt['value']
                mins = pt['minutes']
                if val >= warning_th:
                    severity = "WARNING"
                    threshold_breached = warning_th
                    expected_breach_minutes = mins
                    predicted_breach_value = val
                    break

        expected_breach_time = None
        if expected_breach_minutes is not None:
            expected_breach_time = current_time + timedelta(minutes=expected_breach_minutes)

        # Generate message
        if severity == "NORMAL":
            message = f"{parameter.name} is operating within normal limits ({current_value} {parameter.measurement_unit})."
        elif expected_breach_minutes == 0:
            message = f"{parameter.name} current value ({current_value} {parameter.measurement_unit}) exceeds {severity.lower()} limit of {threshold_breached} {parameter.measurement_unit}."
        else:
            message = f"Predictive {severity}: {parameter.name} is predicted to breach {severity.lower()} threshold ({threshold_breached} {parameter.measurement_unit}) in approx {expected_breach_minutes} mins (value: {predicted_breach_value} {parameter.measurement_unit})."

        alert_dict = {
            'severity': severity,
            'current_value': current_value,
            'predicted_value': predicted_breach_value if predicted_breach_value is not None else (predictions[-1]['value'] if predictions else current_value),
            'threshold': threshold_breached if threshold_breached is not None else warning_th,
            'expected_breach_minutes': expected_breach_minutes,
            'expected_breach_time': expected_breach_time.isoformat() if expected_breach_time else None,
            'message': message
        }

        # Deduplication & Persistence:
        # If severity is WARNING or CRITICAL and alerts are enabled for this parameter
        if severity in ("WARNING", "CRITICAL") and parameter.alert_enabled:
            # Check for existing active or acknowledged alert for same unit and parameter
            existing_alert = Alert.query.filter_by(
                unit_id=unit.id,
                parameter_id=parameter.id,
                status='ACTIVE'
            ).order_by(Alert.id.desc()).first()

            if existing_alert:
                if existing_alert.severity != severity:
                    # Severity escalated (e.g. WARNING -> CRITICAL)
                    existing_alert.status = 'RESOLVED'
                    existing_alert.resolved_at = current_time
                    db.session.add(existing_alert)
                    db.session.flush()

                    new_alert = Alert(
                        unit_id=unit.id,
                        parameter_id=parameter.id,
                        severity=severity,
                        current_value=current_value,
                        predicted_value=alert_dict['predicted_value'],
                        threshold=alert_dict['threshold'],
                        expected_breach_time=expected_breach_time,
                        message=message,
                        status='ACTIVE',
                        created_at=current_time
                    )
                    db.session.add(new_alert)
                    db.session.commit()
                    NotificationService.send_alert_email(unit.unit_name, parameter.name, severity, message)
                    from app.services.cmms_service import dispatch_cmms_work_order
                    dispatch_cmms_work_order(new_alert)
                else:
                    # Same active alert exists; update reading & prediction without spamming new duplicate alerts
                    existing_alert.current_value = current_value
                    existing_alert.predicted_value = alert_dict['predicted_value']
                    existing_alert.expected_breach_time = expected_breach_time
                    existing_alert.message = message
                    db.session.add(existing_alert)
                    db.session.commit()
            else:
                new_alert = Alert(
                    unit_id=unit.id,
                    parameter_id=parameter.id,
                    severity=severity,
                    current_value=current_value,
                    predicted_value=alert_dict['predicted_value'],
                    threshold=alert_dict['threshold'],
                    expected_breach_time=expected_breach_time,
                    message=message,
                    status='ACTIVE',
                    created_at=current_time
                )
                db.session.add(new_alert)
                db.session.commit()
                NotificationService.send_alert_email(unit.unit_name, parameter.name, severity, message)
                from app.services.cmms_service import dispatch_cmms_work_order
                dispatch_cmms_work_order(new_alert)

        # Auto-update Unit Status based on overall parameters
        AlertService.recalculate_unit_status(unit)

        return alert_dict

    @staticmethod
    def recalculate_unit_status(unit: Unit):
        """
        Recalculates unit status:
        If active alerts contain CRITICAL -> CRITICAL
        Else if active alerts contain WARNING -> WARNING
        Else if active -> RUNNING
        """
        active_alerts = Alert.query.filter_by(unit_id=unit.id, status='ACTIVE').all()
        severities = {a.severity for a in active_alerts}

        if 'CRITICAL' in severities:
            unit.status = 'CRITICAL'
        elif 'WARNING' in severities:
            unit.status = 'WARNING'
        elif unit.active and unit.status not in ('OFFLINE', 'MAINTENANCE', 'STOPPED'):
            unit.status = 'RUNNING'

        db.session.add(unit)
        db.session.commit()
