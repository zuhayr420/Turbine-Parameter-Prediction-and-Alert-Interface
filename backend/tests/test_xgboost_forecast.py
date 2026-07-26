import pytest
from app.ml.predictor import XGBoostPredictor
from app.services.prediction_service import PredictionService

def test_xgboost_normalize_inputs():
    # Test padding
    short_inputs = [3.0, 3.5]
    padded = XGBoostPredictor.normalize_input_window(short_inputs, required_len=30)
    assert len(padded) == 30
    assert padded[0] == 3.0
    assert padded[-1] == 3.5

    # Test exact
    exact = [float(i) for i in range(30)]
    out = XGBoostPredictor.normalize_input_window(exact, required_len=30)
    assert len(out) == 30
    assert out == exact

    # Test truncation
    long_inputs = [float(i) for i in range(50)]
    out2 = XGBoostPredictor.normalize_input_window(long_inputs, required_len=30)
    assert len(out2) == 30
    assert out2[0] == 20.0
    assert out2[-1] == 49.0

def test_xgboost_predict_next_3_hours(app):
    with app.app_context():
        predictor = XGBoostPredictor(app.config['MODEL_DIRECTORY'])
        inputs = [4.0 + i * 0.05 for i in range(30)]
        result = predictor.predict_next_3_hours(inputs, parameter_key='test_param', step_minutes=15)
        
        assert result is not None
        assert result['horizon_hours'] == 3.0
        assert len(result['predictions']) == 12  # 12 steps * 15 min = 180 min (3 Hours)
        assert result['predictions'][0]['minutes'] == 15
        assert result['predictions'][-1]['minutes'] == 180
        assert 'value' in result['predictions'][0]
        assert 'shap' in result['predictions'][0]

def test_direct_forecast_api_endpoint(client):
    inputs = [3.5 + (i * 0.05) for i in range(30)]
    payload = {
        'inputs': inputs,
        'parameter_key': 'bearing_vibration',
        'parameter_name': 'Bearing 1 Vibration',
        'measurement_unit': 'mm/s',
        'warning_threshold': 4.5,
        'critical_threshold': 7.0,
        'horizon_hours': 3,
        'interval_minutes': 15
    }
    res = client.post('/api/forecast', json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data['prediction_horizon_hours'] == 3
    assert len(data['predictions']) == 12
    assert data['predictions'][-1]['minutes'] == 180
    assert 'trend' in data
    assert 'alert' in data

def test_sample_inputs_endpoint(client):
    res = client.get('/api/forecast/sample')
    assert res.status_code == 200
    data = res.get_json()
    assert len(data['inputs']) == 30
    assert data['horizon_hours'] == 3
