import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.unit import Unit
from app.models.parameter import Parameter
from app.models.reading import Reading
from app.models.alert import Alert

@pytest.fixture
def app():
    test_app = create_app('testing')
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_headers(app, client):
    with app.app_context():
        admin = User(username='testadmin', email='admin@test.com', role='admin', active=True)
        admin.set_password('Admin@1234')
        db.session.add(admin)
        db.session.commit()

    resp = client.post('/api/auth/login', json={'username': 'testadmin', 'password': 'Admin@1234'})
    token = resp.get_json()['access_token']
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def operator_headers(app, client):
    with app.app_context():
        op = User(username='testoperator', email='operator@test.com', role='operator', active=True)
        op.set_password('Operator@1234')
        db.session.add(op)
        db.session.commit()

    resp = client.post('/api/auth/login', json={'username': 'testoperator', 'password': 'Operator@1234'})
    token = resp.get_json()['access_token']
    return {'Authorization': f'Bearer {token}'}
