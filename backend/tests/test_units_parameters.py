def test_unit_crud(client, admin_headers):
    # 1. Create Unit
    res = client.post('/api/units', json={
        'unit_code': 'UNIT-TEST-1',
        'unit_name': 'Test Turbine Unit',
        'capacity_mw': 250.0
    }, headers=admin_headers)
    assert res.status_code == 201
    unit_id = res.get_json()['unit']['id']

    # 2. Get Unit
    res = client.get(f'/api/units/{unit_id}', headers=admin_headers)
    assert res.status_code == 200
    assert res.get_json()['unit']['unit_code'] == 'UNIT-TEST-1'

    # 3. Create Parameter
    res = client.post(f'/api/units/{unit_id}/parameters', json={
        'name': 'Bearing Vibration',
        'parameter_key': 'bearing_vibration',
        'measurement_unit': 'mm/s',
        'warning_threshold': 4.5,
        'critical_threshold': 6.0,
        'minimum_value': 0.0,
        'maximum_value': 15.0
    }, headers=admin_headers)
    assert res.status_code == 201
    param_id = res.get_json()['parameter']['id']

    # 4. Soft delete unit
    res = client.delete(f'/api/units/{unit_id}', headers=admin_headers)
    assert res.status_code == 200
    res = client.get(f'/api/units/{unit_id}', headers=admin_headers)
    assert res.get_json()['unit']['active'] is False
