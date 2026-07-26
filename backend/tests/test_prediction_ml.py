from datetime import datetime, timezone, timedelta

def test_prediction_insufficient_data(client, admin_headers, app):
    with app.app_context():
        from app.models import Unit, Parameter, Reading
        from app.extensions import db
        u = Unit(unit_code='U-PRED-1', unit_name='Unit Pred Test 1')
        db.session.add(u)
        db.session.commit()
        p = Parameter(unit_id=u.id, name='Vibration', parameter_key='vibration', measurement_unit='mm/s',
                      warning_threshold=4.0, critical_threshold=5.0)
        db.session.add(p)
        db.session.commit()

        # Insert only 10 readings (< 30)
        now = datetime.now(timezone.utc)
        for i in range(10):
            r = Reading(unit_id=u.id, parameter_id=p.id, value=2.5, timestamp=now - timedelta(minutes=i*15))
            db.session.add(r)
        db.session.commit()
        u_id, p_id = u.id, p.id

    res = client.post(f'/api/units/{u_id}/parameters/{p_id}/predict', headers=admin_headers)
    assert res.status_code == 422
    err = res.get_json()['error']
    assert err['code'] == 'INSUFFICIENT_DATA'
    assert err['details']['available'] == 10
    assert err['details']['required'] == 30

def test_prediction_model_unavailable(client, admin_headers, app):
    with app.app_context():
        from app.models import Unit, Parameter, Reading
        from app.extensions import db
        u = Unit(unit_code='U-PRED-2', unit_name='Unit Pred Test 2')
        db.session.add(u)
        db.session.commit()
        # Non-existent trained model parameter
        p = Parameter(unit_id=u.id, name='UnknownParam', parameter_key='unknown_param', measurement_unit='units',
                      warning_threshold=50.0, critical_threshold=80.0)
        db.session.add(p)
        db.session.commit()

        # Insert 30 readings
        now = datetime.now(timezone.utc)
        for i in range(30):
            r = Reading(unit_id=u.id, parameter_id=p.id, value=10.0, timestamp=now - timedelta(minutes=i*15))
            db.session.add(r)
        db.session.commit()
        u_id, p_id = u.id, p.id

    res = client.post(f'/api/units/{u_id}/parameters/{p_id}/predict', headers=admin_headers)
    assert res.status_code == 503
    assert res.get_json()['error']['code'] == 'MODEL_UNAVAILABLE'
