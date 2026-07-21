import os
import json
from flask import Blueprint, current_app
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.parameter import Parameter
from app.models.reading import Reading
from app.models.alert import ModelMetadata
from app.ml.trainer import ModelTrainer
from app.services.prediction_service import PredictionService
from app.utils.response import success_response, error_response
from app.utils.decorators import engineer_required

models_mgmt_bp = Blueprint('models_mgmt', __name__, url_prefix='/api/models')

@models_mgmt_bp.route('', methods=['GET'])
@jwt_required()
def list_models():
    records = ModelMetadata.query.order_by(ModelMetadata.training_date.desc()).all()
    return success_response({'models': [r.to_dict() for r in records]})

@models_mgmt_bp.route('/train/<int:parameter_id>', methods=['POST'])
@jwt_required()
@engineer_required
def train_model(parameter_id):
    param = Parameter.query.get(parameter_id)
    if not param:
        return error_response("PARAMETER_NOT_FOUND", f"Parameter {parameter_id} not found.", 404)

    # Retrieve all historical readings for this parameter
    readings = Reading.query.filter_by(parameter_id=parameter_id)\
        .order_by(Reading.timestamp.asc()).all()

    if len(readings) < 35:
        return error_response(
            "INSUFFICIENT_DATA",
            f"Model training requires at least 35 historical readings. Currently available: {len(readings)}.",
            400
        )

    values = [r.value for r in readings]
    model_dir = current_app.config.get('MODEL_DIRECTORY')
    trainer = ModelTrainer(model_dir=model_dir)

    try:
        metadata = trainer.train_parameter_model(param.parameter_key, values)

        # Invalidate in-memory predictor cache so the new model is loaded immediately
        predictor = PredictionService.get_predictor()
        if param.parameter_key in predictor._model_cache:
            del predictor._model_cache[param.parameter_key]
        if param.parameter_key in predictor._metadata_cache:
            del predictor._metadata_cache[param.parameter_key]

        # Record in DB
        db_meta = ModelMetadata(
            model_version=metadata['model_version'],
            parameter_key=metadata['parameter_key'],
            training_samples=metadata['training_samples'],
            features=json.dumps(metadata['features']),
            algorithm=metadata['algorithm'],
            training_status=metadata['training_status'],
            mae=metadata['mae'],
            rmse=metadata['rmse'],
            r2=metadata['r2'],
            model_path=metadata['model_path']
        )
        db.session.add(db_meta)
        db.session.commit()

        return success_response({'model_metadata': db_meta.to_dict()}, message="Model successfully trained and saved.")
    except Exception as e:
        return error_response("TRAINING_FAILED", f"Model training failed: {str(e)}", 500)
