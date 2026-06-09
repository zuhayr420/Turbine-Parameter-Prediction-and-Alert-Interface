from datetime import datetime, timezone
from app.extensions import db

class Prediction(db.Model):
    __tablename__ = 'predictions'

    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id', ondelete='CASCADE'), nullable=False, index=True)
    parameter_id = db.Column(db.Integer, db.ForeignKey('parameters.id', ondelete='CASCADE'), nullable=False, index=True)
    predicted_value = db.Column(db.Float, nullable=False)
    prediction_time = db.Column(db.DateTime, nullable=False, index=True)
    generated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    model_version = db.Column(db.String(50), nullable=False, default='xgb-v1')
    prediction_horizon = db.Column(db.Integer, nullable=False)  # minutes into future: 15, 30, 45, etc.

    __table_args__ = (
        db.Index('ix_prediction_unit_param_time', 'unit_id', 'parameter_id', 'prediction_time'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'unit_id': self.unit_id,
            'parameter_id': self.parameter_id,
            'predicted_value': self.predicted_value,
            'prediction_time': self.prediction_time.isoformat() if self.prediction_time else None,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'model_version': self.model_version,
            'prediction_horizon': self.prediction_horizon
        }
