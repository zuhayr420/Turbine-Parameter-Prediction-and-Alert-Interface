def test_login_valid(client, app):
    with app.app_context():
        from app.models.user import User
        from app.extensions import db
        u = User(username='user1', email='u1@test.com', role='engineer', active=True)
        u.set_password('Pass1234')
        db.session.add(u)
        db.session.commit()

    resp = client.post('/api/auth/login', json={'username': 'user1', 'password': 'Pass1234'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert 'access_token' in data

def test_login_invalid(client):
    resp = client.post('/api/auth/login', json={'username': 'unknown', 'password': 'bad'})
    assert resp.status_code == 401
    assert resp.get_json()['success'] is False

def test_protected_endpoint_unauthorized(client):
    resp = client.get('/api/units')
    assert resp.status_code == 401

def test_rbac_admin_only(client, operator_headers):
    # Operator should be rejected from creating a unit
    resp = client.post('/api/units', json={'unit_code': 'U-X', 'unit_name': 'Turbine X'}, headers=operator_headers)
    assert resp.status_code == 403
