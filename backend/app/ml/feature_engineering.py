import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    'value_t',
    'lag_1',
    'lag_2',
    'lag_3',
    'lag_5',
    'diff_1',
    'diff_3',
    'rolling_mean_5',
    'rolling_std_5',
    'rolling_mean_15',
    'rolling_std_15',
    'rolling_mean_30',
    'rolling_std_30',
    'rolling_min_30',
    'rolling_max_30',
    'rate_of_change',
    'short_term_slope'
]

def extract_features_from_window(values_30: list) -> pd.DataFrame:
    """
    Given a list or array of exactly 30 chronological historical values:
    [t-29, t-28, ..., t-1, t]
    Computes time-series engineering features corresponding to observation t.
    Returns a single-row DataFrame with FEATURE_COLUMNS.
    """
    if len(values_30) != 30:
        raise ValueError(f"Feature engineering requires exactly 30 observations, got {len(values_30)}")
    
    s = pd.Series(values_30, dtype=np.float64)
    if s.isna().any():
        raise ValueError("Historical values contain NaN or missing elements.")

    val_t = float(s.iloc[-1])
    lag_1 = float(s.iloc[-2])
    lag_2 = float(s.iloc[-3])
    lag_3 = float(s.iloc[-4])
    lag_5 = float(s.iloc[-6])

    diff_1 = val_t - lag_1
    diff_3 = val_t - lag_3

    rolling_5 = s.iloc[-5:]
    rolling_mean_5 = float(rolling_5.mean())
    rolling_std_5 = float(rolling_5.std(ddof=0))

    rolling_15 = s.iloc[-15:]
    rolling_mean_15 = float(rolling_15.mean())
    rolling_std_15 = float(rolling_15.std(ddof=0))

    rolling_30 = s
    rolling_mean_30 = float(rolling_30.mean())
    rolling_std_30 = float(rolling_30.std(ddof=0))
    rolling_min_30 = float(rolling_30.min())
    rolling_max_30 = float(rolling_30.max())

    # Rate of change relative to lag_5
    denom = abs(lag_5) if abs(lag_5) > 1e-5 else 1.0
    rate_of_change = float((val_t - lag_5) / denom)

    # Short-term linear slope over last 5 points
    x = np.arange(5)
    y = rolling_5.values
    if np.all(y == y[0]):
        short_term_slope = 0.0
    else:
        # cov(x, y) / var(x)
        short_term_slope = float(np.polyfit(x, y, 1)[0])

    data = {
        'value_t': [val_t],
        'lag_1': [lag_1],
        'lag_2': [lag_2],
        'lag_3': [lag_3],
        'lag_5': [lag_5],
        'diff_1': [diff_1],
        'diff_3': [diff_3],
        'rolling_mean_5': [rolling_mean_5],
        'rolling_std_5': [rolling_std_5],
        'rolling_mean_15': [rolling_mean_15],
        'rolling_std_15': [rolling_std_15],
        'rolling_mean_30': [rolling_mean_30],
        'rolling_std_30': [rolling_std_30],
        'rolling_min_30': [rolling_min_30],
        'rolling_max_30': [rolling_max_30],
        'rate_of_change': [rate_of_change],
        'short_term_slope': [short_term_slope]
    }
    return pd.DataFrame(data)[FEATURE_COLUMNS]

def prepare_training_dataset(readings_series: list):
    """
    Given a list of chronological readings (floats), constructs sliding windows of 30 items
    as features, and item t+1 as the 1-step forecast target for training.
    """
    X_rows = []
    y_vals = []
    n = len(readings_series)
    if n < 35:
        raise ValueError(f"Insufficient historical data for training. Required >= 35, got {n}.")

    for i in range(30, n):
        window = readings_series[i-30:i]
        target = readings_series[i]
        feats = extract_features_from_window(window)
        X_rows.append(feats)
        y_vals.append(target)

    X = pd.concat(X_rows, ignore_index=True)
    y = np.array(y_vals, dtype=np.float64)
    return X, y
