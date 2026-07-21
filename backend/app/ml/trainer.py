import os
import json
import logging
from datetime import datetime, timezone
import joblib
import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from app.ml.feature_engineering import prepare_training_dataset, FEATURE_COLUMNS

logger = logging.getLogger(__name__)

class ModelTrainer:
    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)

    def train_parameter_model(self, parameter_key: str, chronological_values: list, test_size_ratio=0.2):
        """
        Trains an XGBoost Regressor on chronological values using a time-series chronological split.
        Saves the model as .joblib and outputs training metrics (MAE, RMSE, R2).
        """
        logger.info(f"Preparing training data for {parameter_key} with {len(chronological_values)} samples.")
        X, y = prepare_training_dataset(chronological_values)

        total_samples = len(X)
        split_idx = int(total_samples * (1 - test_size_ratio))
        if split_idx < 1 or (total_samples - split_idx) < 1:
            # Not enough for split, use entire dataset for training and compute train metrics
            X_train, y_train = X, y
            X_val, y_val = X, y
        else:
            # Time-series strict split (NO random shuffling)
            X_train, y_train = X.iloc[:split_idx], y[:split_idx]
            X_val, y_val = X.iloc[split_idx:], y[split_idx:]

        model = xgb.XGBRegressor(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=4,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            objective='reg:squarederror'
        )

        model.fit(X_train, y_train)

        # Train Isolation Forest for Anomaly Detection
        from sklearn.ensemble import IsolationForest
        iso_forest = IsolationForest(contamination=0.05, random_state=42)
        iso_forest.fit(X)

        # Evaluate on validation set
        val_preds = model.predict(X_val)
        mae = float(mean_absolute_error(y_val, val_preds))
        rmse = float(np.sqrt(mean_squared_error(y_val, val_preds)))
        r2 = float(r2_score(y_val, val_preds)) if len(y_val) > 1 and np.var(y_val) > 1e-6 else 1.0

        model_version = f"xgb-{parameter_key}-v1"
        model_filename = f"{parameter_key}.joblib"
        model_path = os.path.join(self.model_dir, model_filename)
        
        iso_filename = f"{parameter_key}_iso.joblib"
        iso_path = os.path.join(self.model_dir, iso_filename)

        joblib.dump(model, model_path)
        joblib.dump(iso_forest, iso_path)
        logger.info(f"Models saved. XGBoost MAE={mae:.4f}, RMSE={rmse:.4f}, R2={r2:.4f}")

        metadata = {
            'model_version': model_version,
            'parameter_key': parameter_key,
            'training_date': datetime.now(timezone.utc).isoformat(),
            'training_samples': total_samples,
            'features': FEATURE_COLUMNS,
            'algorithm': 'XGBoost Regressor',
            'training_status': 'TRAINED',
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
            'model_path': model_path
        }

        # Save metadata JSON file alongside
        meta_path = os.path.join(self.model_dir, f"{parameter_key}_metadata.json")
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        return metadata
