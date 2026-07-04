from datetime import datetime, timezone
from app.services.alert_service import AlertService

def test_alert_generation_and_deduplication(app):
    with app.app_context():
        from app.models import Unit, Parameter, Alert
        from app.extensions import db

        u = Unit(unit_code='U-ALT', unit_name='Unit Alert Test')
        db.session.add(u)
        db.session.commit()

        p = Parameter(
            unit_id=u.id,
            name='Vibration',
            parameter_key='vibration',
            measurement_unit='mm/s',
            warning_threshold=4.0,
            critical_threshold=5.0,
            enabled=True,
            alert_enabled=True
        )
        db.session.add(p)
        db.session.commit()

        # Simulated predictions where minute 60 crosses warning threshold
        preds = [
            {'minutes': 15, 'value': 3.2},
            {'minutes': 30, 'value': 3.5},
            {'minutes': 45, 'value': 3.8},
            {'minutes': 60, 'value': 4.2},  # Warning breach
            {'minutes': 75, 'value': 4.3}
        ]

        # 1. First evaluation: should create 1 WARNING alert with expected_breach_minutes=60
        alert_info = AlertService.evaluate_predictive_alert(u, p, current_value=3.0, predictions=preds)
        assert alert_info['severity'] == 'WARNING'
        assert alert_info['expected_breach_minutes'] == 60

        active_alerts = Alert.query.filter_by(unit_id=u.id, status='ACTIVE').all()
        assert len(active_alerts) == 1
        assert active_alerts[0].severity == 'WARNING'

        # 2. Second evaluation under same condition: Deduplication should prevent second alert
        AlertService.evaluate_predictive_alert(u, p, current_value=3.1, predictions=preds)
        active_alerts_after = Alert.query.filter_by(unit_id=u.id, status='ACTIVE').all()
        assert len(active_alerts_after) == 1  # Still exactly 1!

        # 3. Third evaluation under CRITICAL breach: Escalates alert
        crit_preds = [
            {'minutes': 15, 'value': 3.5},
            {'minutes': 30, 'value': 5.2}  # Critical breach
        ]
        AlertService.evaluate_predictive_alert(u, p, current_value=3.5, predictions=crit_preds)
        active_alerts_crit = Alert.query.filter_by(unit_id=u.id, status='ACTIVE').all()
        assert len(active_alerts_crit) == 1
        assert active_alerts_crit[0].severity == 'CRITICAL'
