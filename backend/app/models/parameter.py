from datetime import datetime, timezone
from app.extensions import db

class Parameter(db.Model):
    __tablename__ = 'parameters'

    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    parameter_key = db.Column(db.String(100), nullable=False, index=True)  # e.g. vibration, lube_temperature, steam_pressure
    description = db.Column(db.String(255), nullable=True)
    measurement_unit = db.Column(db.String(30), nullable=False)  # e.g. mm/s, °C, MPa, RPM, MW
    warning_threshold = db.Column(db.Float, nullable=False)
    critical_threshold = db.Column(db.Float, nullable=False)
    minimum_value = db.Column(db.Float, nullable=True)
    maximum_value = db.Column(db.Float, nullable=True)
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    alert_enabled = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    readings = db.relationship('Reading', backref='parameter', lazy='dynamic', cascade='all, delete-orphan')
    predictions = db.relationship('Prediction', backref='parameter', lazy='dynamic', cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='parameter', lazy='dynamic', cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('unit_id', 'parameter_key', name='uq_unit_parameter_key'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'unit_id': self.unit_id,
            'name': self.name,
            'parameter_key': self.parameter_key,
            'description': self.description,
            'measurement_unit': self.measurement_unit,
            'warning_threshold': self.warning_threshold,
            'critical_threshold': self.critical_threshold,
            'minimum_value': self.minimum_value,
            'maximum_value': self.maximum_value,
            'enabled': self.enabled,
            'alert_enabled': self.alert_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
