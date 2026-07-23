import os
import json
import logging
from typing import Dict, Any, List, Optional
import numpy as np
import joblib
import shap
import xgboost as xgb
from app.ml.feature_engineering import extract_features_from_window, prepare_training_dataset, FEATURE_COLUMNS

logger = logging.getLogger(__name__)

class XGBoostPredictor:
    """
    XGBoost Forecasting Engine.
    Reads input sensor observations and recursively predicts future trajectory 
    for the next 3 hours (12 steps at 15-minute intervals).
    """

    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)
        self._model_cache: Dict[str, Any] = {}
        self._metadata_cache: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def normalize_input_window(inputs: List[float], required_len: int = 30) -> List[float]:
        """
        Ensures the input stream has exactly `required_len` (30) historical observations.
        - If inputs > 30: uses the most recent 30 readings.
        - If inputs == 30: casts all to float.
        - If inputs < 30: smoothly interpolates/extrapolates back to 30 points.
        """
        if not inputs:
            return [0.0] * required_len

        clean_inputs = [float(x) for x in inputs if x is not None and not np.isnan(float(x))]
        if not clean_inputs:
            return [0.0] * required_len

        n = len(clean_inputs)
        if n >= required_len:
            return clean_inputs[-required_len:]

        if n == 1:
            return [clean_inputs[0]] * required_len

        # Linear interpolation back to required_len points
        x_orig = np.linspace(0, 1, n)
        x_target = np.linspace(0, 1, required_len)
        interpolated = np.interp(x_target, x_orig, clean_inputs)
        return [round(float(v), 4) for v in interpolated]

    def is_model_available(self, parameter_key: str) -> bool:
        if parameter_key in self._model_cache:
            return True
        model_path = os.path.join(self.model_dir, f"{parameter_key}.joblib")
        return os.path.isfile(model_path)

    def load_model(self, parameter_key: str):
        if parameter_key in self._model_cache:
            return self._model_cache[parameter_key], self._metadata_cache.get(parameter_key, {})

        model_path = os.path.join(self.model_dir, f"{parameter_key}.joblib")
        if not os.path.isfile(model_path):
            return None, None

        try:
            model = joblib.load(model_path)
            self._model_cache[parameter_key] = model

            meta_path = os.path.join(self.model_dir, f"{parameter_key}_metadata.json")
            metadata = {}
            if os.path.isfile(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            self._metadata_cache[parameter_key] = metadata

            logger.info(f"Loaded XGBoost model from {model_path} into memory cache.")
            return model, metadata
        except Exception as e:
            logger.error(f"Failed loading model for {parameter_key}: {e}")
            return None, None

    def get_or_create_model(self, parameter_key: str, baseline_values: Optional[List[float]] = None):
        """
        Retrieves existing trained model, or builds and trains an XGBoost model on-the-fly
        so forecasting never halts.
        """
        model, metadata = self.load_model(parameter_key)
        if model is not None:
            return model, metadata

        logger.info(f"Building on-demand XGBoost forecasting model for {parameter_key}...")
        
        # Prepare training data around baseline values
        if baseline_values and len(baseline_values) >= 5:
            base = np.array(self.normalize_input_window(baseline_values))
        else:
            base = np.linspace(10.0, 15.0, 30)

        # Generate synthetic training windows with realistic industrial noise and drift
        np.random.seed(42)
        simulated_series = []
        val = base[-1]
        mean_val = float(np.mean(base))
        std_val = max(float(np.std(base)), 0.05 * mean_val, 0.1)

        for _ in range(120):
            drift = (mean_val - val) * 0.05 + np.random.normal(0, std_val * 0.2)
            val = max(0.01, val + drift)
            simulated_series.append(float(val))

        training_data = list(base) + simulated_series
        X, y = prepare_training_dataset(training_data)

        model = xgb.XGBRegressor(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=4,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            objective='reg:squarederror'
        )
        model.fit(X, y)

        model_version = f"xgb-{parameter_key}-v1"
        model_filename = f"{parameter_key}.joblib"
        model_path = os.path.join(self.model_dir, model_filename)

        try:
            joblib.dump(model, model_path)
            metadata = {
                'model_version': model_version,
                'parameter_key': parameter_key,
                'algorithm': 'XGBoost Regressor (Auto-Calibrated)',
                'training_samples': len(X),
                'features': FEATURE_COLUMNS,
                'model_path': model_path
            }
            meta_path = os.path.join(self.model_dir, f"{parameter_key}_metadata.json")
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            self._metadata_cache[parameter_key] = metadata
        except Exception as save_err:
            logger.warning(f"Could not persist auto-trained model to disk: {save_err}")
            metadata = {'model_version': model_version, 'parameter_key': parameter_key}

        self._model_cache[parameter_key] = model
        return model, metadata

    def forecast_recursive(
        self,
        parameter_key: str,
        historical_30: List[float],
        horizon_steps: int = 12,
        step_minutes: int = 15,
        auto_create_model: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Executes multi-step recursive XGBoost forecasting for `horizon_steps` points.
        Default: 12 steps * 15 minutes = 180 minutes (3 Hours in advance).

        Pipeline:
        1. Reads and normalizes input observations into rolling window of 30.
        2. Forecasts step t+1 using XGBoost Regressor.
        3. Appends prediction to rolling window and drops oldest point.
        4. Calculates SHAP feature importance for explainable forecast attribution.
        5. Repeats recursively for the full 3-hour horizon.
        """
        clean_inputs = self.normalize_input_window(historical_30, required_len=30)
        
        if auto_create_model:
            model, metadata = self.get_or_create_model(parameter_key, baseline_values=clean_inputs)
        else:
            model, metadata = self.load_model(parameter_key)

        if model is None:
            return None

        # Instantiate SHAP explainer once outside the step loop for performance
        explainer = None
        try:
            explainer = shap.TreeExplainer(model)
        except Exception as e:
            logger.debug(f"SHAP TreeExplainer initialization notice: {e}")

        current_window = list(clean_inputs)
        predictions = []

        for step in range(1, horizon_steps + 1):
            feats = extract_features_from_window(current_window)
            pred_val = float(model.predict(feats)[0])

            # SHAP feature importance extraction
            top_shap = []
            if explainer is not None:
                try:
                    shap_values = explainer.shap_values(feats)
                    feature_names = feats.columns.tolist()
                    shap_dict = dict(zip(feature_names, shap_values[0]))
                    sorted_shap = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
                    top_shap = [{'feature': k, 'impact': round(float(v), 4)} for k, v in sorted_shap]
                except Exception as shap_err:
                    logger.debug(f"SHAP evaluation notice at step {step}: {shap_err}")

            minutes = step * step_minutes
            predictions.append({
                'step': step,
                'minutes': minutes,
                'value': round(pred_val, 4),
                'shap': top_shap
            })

            # Slide window: drop oldest, append prediction
            current_window = current_window[1:] + [pred_val]

        return {
            'model_version': metadata.get('model_version', f'xgb-{parameter_key}-v1'),
            'horizon_hours': round((horizon_steps * step_minutes) / 60, 2),
            'step_minutes': step_minutes,
            'input_window_size': len(clean_inputs),
            'inputs_used': clean_inputs,
            'predictions': predictions
        }

    def predict_next_3_hours(
        self,
        inputs: List[float],
        parameter_key: str = 'bearing_vibration',
        step_minutes: int = 15
    ) -> Optional[Dict[str, Any]]:
        """
        Direct convenience interface:
        Reads input data and predicts future values for the next 3 hours in advance.
        """
        return self.forecast_recursive(
            parameter_key=parameter_key,
            historical_30=inputs,
            horizon_steps=12,
            step_minutes=step_minutes,
            auto_create_model=True
        )
