import numpy as np

class TrendService:
    @staticmethod
    def analyze_trend(current_value: float, predicted_3h_value: float, historical_values: list = None) -> dict:
        """
        Analyzes the trend between current observation and 3-hour forecast.
        Categorizes into:
        STABLE, INCREASING, DECREASING, RAPIDLY_INCREASING, RAPIDLY_DECREASING.
        """
        diff = predicted_3h_value - current_value
        denom = abs(current_value) if abs(current_value) > 1e-5 else 1.0
        rate_of_change = diff / denom
        abs_rate = abs(rate_of_change)

        if abs_rate < 0.02:
            trend = "STABLE"
        elif rate_of_change > 0:
            if rate_of_change >= 0.15:
                trend = "RAPIDLY_INCREASING"
            else:
                trend = "INCREASING"
        else:
            if rate_of_change <= -0.15:
                trend = "RAPIDLY_DECREASING"
            else:
                trend = "DECREASING"

        return {
            'trend': trend,
            'rate_of_change': round(rate_of_change, 4),
            'current_value': round(current_value, 4),
            'predicted_3h_value': round(predicted_3h_value, 4)
        }
