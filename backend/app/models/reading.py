from datetime import datetime, timezone
from app.extensions import db

class Reading(db.Model):
    __tablename__ = 'readings'

    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id', ondelete='CASCADE'), nullable=False, index=True)
    parameter_id = db.Column(db.Integer, db.ForeignKey('parameters.id', ondelete='CASCADE'), nullable=False, index=True)
    value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    data_source = db.Column(db.String(30), nullable=False, default='SENSOR')  # MANUAL, CSV, SIMULATION, SENSOR, API
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        db.Index('ix_reading_unit_param_ts', 'unit_id', 'parameter_id', 'timestamp'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'unit_id': self.unit_id,
            'parameter_id': self.parameter_id,
            'value': self.value,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'data_source': self.data_source,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
