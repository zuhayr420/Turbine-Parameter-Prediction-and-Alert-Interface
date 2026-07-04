from datetime import datetime, timezone

def test_add_and_retrieve_readings(client, admin_headers, app):
    # Setup unit and parameter
    with app.app_context():
        from app.models import Unit, Parameter
        from app.extensions import db
        u = Unit(unit_code='U-RD', unit_name='Unit Reading Test')
        db.session.add(u)
        db.session.commit()
        p = Parameter(unit_id=u.id, name='Pressure', parameter_key='pressure', measurement_unit='MPa',
                      warning_threshold=15.0, critical_threshold=18.0, minimum_value=0.0, maximum_value=30.0)
        db.session.add(p)
        db.session.commit()
        u_id, p_id = u.id, p.id

    # 1. Add valid reading
    res = client.post(f'/api/units/{u_id}/readings', json={
        'parameter_id': p_id,
        'value': 12.5,
        'data_source': 'SENSOR'
    }, headers=admin_headers)
    assert res.status_code == 201
    assert res.get_json()['value'] == 12.5

    # 2. Reject out of range reading
    res = client.post(f'/api/units/{u_id}/readings', json={
        'parameter_id': p_id,
        'value': -50.0
    }, headers=admin_headers)
    assert res.status_code == 400

    # 3. Retrieve current readings
    res = client.get(f'/api/units/{u_id}/readings', headers=admin_headers)
    assert res.status_code == 200
    currents = res.get_json()['current_readings']
    assert len(currents) == 1
    assert currents[0]['value'] == 12.5
