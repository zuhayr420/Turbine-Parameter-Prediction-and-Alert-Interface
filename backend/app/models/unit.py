from datetime import datetime, timezone
from app.extensions import db

class Unit(db.Model):
    __tablename__ = 'units'

    id = db.Column(db.Integer, primary_key=True)
    unit_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    unit_name = db.Column(db.String(100), nullable=False)
    station_id = db.Column(db.Integer, db.ForeignKey('stations.id'), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    manufacturer = db.Column(db.String(100), nullable=True)
    model = db.Column(db.String(100), nullable=True)
    capacity_mw = db.Column(db.Float, nullable=False, default=210.0)
    commissioning_date = db.Column(db.Date, nullable=True)
    starting_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(30), nullable=False, default='RUNNING')  # RUNNING, WARNING, CRITICAL, OFFLINE, MAINTENANCE, STOPPED
    downtime_hours = db.Column(db.Float, nullable=False, default=0.0)
    last_maintenance_date = db.Column(db.Date, nullable=True)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    parameters = db.relationship('Parameter', backref='unit', lazy='dynamic', cascade='all, delete-orphan')
    readings = db.relationship('Reading', backref='unit', lazy='dynamic', cascade='all, delete-orphan')
    predictions = db.relationship('Prediction', backref='unit', lazy='dynamic', cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='unit', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'unit_code': self.unit_code,
            'unit_name': self.unit_name,
            'station_id': self.station_id, 'station_name': self.station.name if self.station else None,
            'location': self.location,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'capacity_mw': self.capacity_mw,
            'commissioning_date': self.commissioning_date.isoformat() if self.commissioning_date else None,
            'starting_date': self.starting_date.isoformat() if self.starting_date else None,
            'status': self.status,
            'downtime_hours': self.downtime_hours,
            'last_maintenance_date': self.last_maintenance_date.isoformat() if self.last_maintenance_date else None,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
