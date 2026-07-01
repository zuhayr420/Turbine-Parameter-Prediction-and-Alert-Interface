import os
from app import create_app
from app.extensions import db
from app.models import User

def reset_and_seed_admin():
    app = create_app('development')
    with app.app_context():
        print("Dropping all existing demo data and tables...")
        db.drop_all()
        print("Recreating clean tables...")
        db.create_all()

        print("Seeding administrative and initial user accounts only (NO demo plants, NO demo parameters, NO demo readings)...")
        admin = User(username='admin', email='admin@powerstation.com', role='admin', active=True)
        admin.set_password('Admin@1234')

        engineer = User(username='engineer1', email='engineer@powerstation.com', role='engineer', active=True)
        engineer.set_password('Engineer@1234')

        operator = User(username='operator1', email='operator@powerstation.com', role='operator', active=True)
        operator.set_password('Operator@1234')

        db.session.add_all([admin, engineer, operator])
        db.session.commit()
        print("Clean database ready! Users created: admin / Admin@1234, engineer1, operator1.")

if __name__ == '__main__':
    reset_and_seed_admin()
