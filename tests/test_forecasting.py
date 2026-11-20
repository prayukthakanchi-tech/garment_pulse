"""
Unit tests for forecasting algorithms, backtesting splits, and error metrics.
"""

import numpy as np
from src.forecasting.demand_forecaster import DemandForecaster


def test_seasonal_naive_length(test_db):
    """Verify seasonal naive forecast returns requested horizon."""
    forecaster = DemandForecaster(test_db)
    dummy_series = np.array([100, 120, 110, 130, 140, 125, 135, 150] * 7, dtype=float)

    preds = forecaster.seasonal_naive_forecast(dummy_series, horizon=8)
    assert len(preds) == 8, f"Expected 8 predictions, got {len(preds)}"
    assert all(p > 0 for p in preds), "Forecasted values must be positive."


def test_moving_average_length(test_db):
    """Verify moving average forecast returns constant value of recent window."""
    forecaster = DemandForecaster(test_db)
    dummy_series = np.array([10, 20, 30, 40], dtype=float)

    preds = forecaster.moving_average_forecast(dummy_series, horizon=4, window=2)
    assert len(preds) == 4
    assert np.allclose(preds, 35.0), f"Expected MA of [30, 40] to be 35.0, got {preds[0]}"


def test_exponential_smoothing_bounds(test_db):
    """Verify exponential smoothing produces predictions and valid uncertainty intervals."""
    forecaster = DemandForecaster(test_db)
    dummy_series = np.array([50 + 2 * i + (5 if i % 2 == 0 else -5) for i in range(30)], dtype=float)

    preds, lower, upper = forecaster.exponential_smoothing_forecast(dummy_series, horizon=6)
    assert len(preds) == 6
    assert len(lower) == 6
    assert len(upper) == 6
    assert all(lower[i] <= preds[i] <= upper[i] for i in range(6)), "Predictions must lie within confidence bounds."
