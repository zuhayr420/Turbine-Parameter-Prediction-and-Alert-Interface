from datetime import datetime, timezone
from app.extensions import db

class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id', ondelete='CASCADE'), nullable=False, index=True)
    parameter_id = db.Column(db.Integer, db.ForeignKey('parameters.id', ondelete='CASCADE'), nullable=False, index=True)
    severity = db.Column(db.String(20), nullable=False)  # NORMAL, WARNING, CRITICAL
    current_value = db.Column(db.Float, nullable=False)
    predicted_value = db.Column(db.Float, nullable=True)
    threshold = db.Column(db.Float, nullable=False)
    expected_breach_time = db.Column(db.DateTime, nullable=True)
    message = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='ACTIVE', index=True)  # ACTIVE, ACKNOWLEDGED, RESOLVED
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.Index('ix_alert_unit_param_status', 'unit_id', 'parameter_id', 'status'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'unit_id': self.unit_id,
            'parameter_id': self.parameter_id,
            'parameter_name': self.parameter.name if self.parameter else None,
            'unit_code': self.unit.unit_code if self.unit else None,
            'severity': self.severity,
            'current_value': self.current_value,
            'predicted_value': self.predicted_value,
            'threshold': self.threshold,
            'expected_breach_time': self.expected_breach_time.isoformat() if self.expected_breach_time else None,
            'message': self.message,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }


class ModelMetadata(db.Model):
    __tablename__ = 'model_metadata'

    id = db.Column(db.Integer, primary_key=True)
    model_version = db.Column(db.String(50), nullable=False, index=True)
    parameter_key = db.Column(db.String(100), nullable=False, index=True)
    training_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    training_samples = db.Column(db.Integer, nullable=False)
    features = db.Column(db.Text, nullable=False)  # JSON-string of feature column names
    algorithm = db.Column(db.String(50), default='XGBoost Regressor', nullable=False)
    training_status = db.Column(db.String(30), default='TRAINED', nullable=False)
    mae = db.Column(db.Float, nullable=True)
    rmse = db.Column(db.Float, nullable=True)
    r2 = db.Column(db.Float, nullable=True)
    model_path = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'model_version': self.model_version,
            'parameter_key': self.parameter_key,
            'training_date': self.training_date.isoformat() if self.training_date else None,
            'training_samples': self.training_samples,
            'features': json.loads(self.features) if self.features else [],
            'algorithm': self.algorithm,
            'training_status': self.training_status,
            'validation_metrics': {
                'mae': round(self.mae, 4) if self.mae is not None else None,
                'rmse': round(self.rmse, 4) if self.rmse is not None else None,
                'r2': round(self.r2, 4) if self.r2 is not None else None
            }
        }
