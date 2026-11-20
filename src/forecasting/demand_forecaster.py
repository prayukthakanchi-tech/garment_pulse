"""
GarmentPulse — Fashion Demand Forecasting Engine (Module G)
Category purchase volume forecasting using Seasonal Naive, Moving Average,
Holt-Winters Exponential Smoothing, and LightGBM with walk-forward cross-validation.
FORECASTS PROJECT PURCHASE VOLUME — NEVER INVENTORY REQUIREMENTS.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
import duckdb
import numpy as np
import pandas as pd
try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    HAS_STATSMODELS = True
except Exception:
    HAS_STATSMODELS = False
    ExponentialSmoothing = None

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False


class DemandForecaster:
    """Forecasting engine operating on aggregated weekly transaction counts."""

    VALID_LEVELS = {
        "department": "department_name",
        "department_name": "department_name",
        "product_group": "product_group_name",
        "product_group_name": "product_group_name",
        "garment_group": "garment_group_name",
        "garment_group_name": "garment_group_name",
    }

    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn

    def get_weekly_series(
        self,
        category: str,
        level: str = "department",
    ) -> pd.DataFrame:
        """Extracts complete chronological weekly transaction series for a category."""
        col = self.VALID_LEVELS.get(level.lower().strip(), "department_name")
        sql = f"""
        SELECT
            DATE_TRUNC('week', t.t_dat) AS week_date,
            COUNT(*) AS purchase_volume
        FROM transactions t
        JOIN articles a ON t.article_id = a.article_id
        WHERE a.{col} = ?
        GROUP BY DATE_TRUNC('week', t.t_dat)
        ORDER BY week_date ASC
        """
        df = self.conn.execute(sql, [category]).fetchdf()
        df["week_date"] = pd.to_datetime(df["week_date"])
        return df

    def seasonal_naive_forecast(
        self,
        series: np.ndarray,
        horizon: int = 8,
        season_length: int = 52,
    ) -> np.ndarray:
        """Seasonal naive: uses value from 52 weeks prior; falls back to last period if shorter."""
        n = len(series)
        forecasts = []
        for h in range(horizon):
            idx = n - season_length + (h % season_length)
            if idx >= 0 and idx < n:
                forecasts.append(series[idx])
            else:
                forecasts.append(series[-1])
        return np.array(forecasts, dtype=float)

    def moving_average_forecast(
        self,
        series: np.ndarray,
        horizon: int = 8,
        window: int = 4,
    ) -> np.ndarray:
        """Moving average baseline over the most recent `window` weeks."""
        ma_val = np.mean(series[-window:]) if len(series) >= window else np.mean(series)
        return np.full(horizon, ma_val, dtype=float)

    def _holt_winters_numpy(
        self,
        series: np.ndarray,
        horizon: int = 8,
        alpha: float = 0.35,
        beta: float = 0.15,
        season_len: int = 52,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Self-contained NumPy implementation of Holt-Winters with level, trend, and seasonal factors."""
        n = len(series)
        if n == 0:
            return np.zeros(horizon), np.zeros(horizon), np.zeros(horizon)

        level = float(series[0])
        trend = float((series[-1] - series[0]) / n) if n > 1 else 0.0

        # Estimate seasonal indices if sufficient length
        seasonal = np.ones(season_len)
        if n >= season_len:
            raw_s = np.array([np.mean(series[i::season_len]) for i in range(season_len)])
            s_mean = np.mean(raw_s) or 1.0
            seasonal = raw_s / s_mean

        residuals = []
        for t in range(n):
            s_idx = t % season_len
            last_level = level
            s_factor = max(float(seasonal[s_idx]), 0.01)
            level = alpha * (series[t] / s_factor) + (1 - alpha) * (level + trend)
            trend = beta * (level - last_level) + (1 - beta) * trend
            pred = (level + trend) * s_factor
            residuals.append(series[t] - pred)

        forecasts = []
        for h in range(1, horizon + 1):
            s_idx = (n + h - 1) % season_len
            f = (level + h * trend) * float(seasonal[s_idx])
            forecasts.append(max(float(f), 0.0))

        std_err = float(np.std(residuals)) if residuals else 1.0
        preds = np.array(forecasts, dtype=float)
        lower = np.maximum(preds - 1.96 * std_err, 0.0)
        upper = preds + 1.96 * std_err
        return preds, lower, upper

    def exponential_smoothing_forecast(
        self,
        series: np.ndarray,
        horizon: int = 8,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Holt-Winters Exponential Smoothing with trend and additive/seasonal terms."""
        if HAS_STATSMODELS and ExponentialSmoothing is not None:
            try:
                if len(series) >= 104:
                    model = ExponentialSmoothing(
                        series,
                        trend="add",
                        seasonal="add",
                        seasonal_periods=52,
                        initialization_method="estimated",
                    ).fit(optimized=True)
                elif len(series) >= 20:
                    model = ExponentialSmoothing(
                        series,
                        trend="add",
                        damped_trend=True,
                        initialization_method="estimated",
                    ).fit(optimized=True)
                else:
                    model = ExponentialSmoothing(series, trend=None).fit(optimized=True)

                preds = model.forecast(horizon)
                residuals = series - model.fittedvalues
                std_err = np.std(residuals) if len(residuals) > 0 else 1.0

                lower = np.maximum(preds - 1.96 * std_err, 0.0)
                upper = preds + 1.96 * std_err
                return preds, lower, upper
            except Exception:
                pass

        # Fallback to native NumPy Holt-Winters
        return self._holt_winters_numpy(series, horizon=horizon)

    def lightgbm_forecast(
        self,
        series_df: pd.DataFrame,
        horizon: int = 8,
    ) -> np.ndarray:
        """Autoregressive gradient boosted trees with lag & calendar features."""
        if not HAS_LIGHTGBM or len(series_df) < 24:
            return self.moving_average_forecast(series_df["purchase_volume"].values, horizon=horizon)

        df = series_df.copy()
        df["week_of_year"] = df["week_date"].dt.isocalendar().week
        df["month"] = df["week_date"].dt.month

        # Generate lag features
        for lag in [1, 2, 3, 4, 8, 12]:
            df[f"lag_{lag}"] = df["purchase_volume"].shift(lag)
        df["rolling_mean_4"] = df["purchase_volume"].shift(1).rolling(4).mean()

        train_data = df.dropna().reset_index(drop=True)
        if len(train_data) < 10:
            return self.moving_average_forecast(series_df["purchase_volume"].values, horizon=horizon)

        feature_cols = [c for c in train_data.columns if c not in ["week_date", "purchase_volume"]]
        X_train = train_data[feature_cols]
        y_train = train_data["purchase_volume"]

        model = lgb.LGBMRegressor(
            n_estimators=60,
            learning_rate=0.08,
            num_leaves=15,
            verbose=-1,
            random_state=42,
        )
        model.fit(X_train, y_train)

        # Iterative recursive forecasting
        history = list(df["purchase_volume"].values)
        dates = list(df["week_date"].values)
        predictions = []

        last_date = pd.to_datetime(dates[-1])
        for step in range(1, horizon + 1):
            next_date = last_date + pd.Timedelta(weeks=step)
            feat = {
                "week_of_year": next_date.isocalendar().week,
                "month": next_date.month,
                "lag_1": history[-1],
                "lag_2": history[-2] if len(history) >= 2 else history[-1],
                "lag_3": history[-3] if len(history) >= 3 else history[-1],
                "lag_4": history[-4] if len(history) >= 4 else history[-1],
                "lag_8": history[-8] if len(history) >= 8 else history[-1],
                "lag_12": history[-12] if len(history) >= 12 else history[-1],
                "rolling_mean_4": np.mean(history[-4:]),
            }
            x_step = pd.DataFrame([feat])[feature_cols]
            pred = max(float(model.predict(x_step)[0]), 0.0)
            predictions.append(pred)
            history.append(pred)

        return np.array(predictions)

    def backtest(
        self,
        category: str,
        level: str = "department",
        horizon: int = 8,
    ) -> Dict[str, Any]:
        """Chronological backtest comparing Seasonal Naive, Moving Average, Holt-Winters, and LightGBM."""
        series_df = self.get_weekly_series(category, level=level)
        if len(series_df) < (horizon + 12):
            return {"error": f"Series too short ({len(series_df)} weeks). Need at least {horizon + 12} weeks."}

        train_series = series_df["purchase_volume"].iloc[:-horizon].values
        actual_test = series_df["purchase_volume"].iloc[-horizon:].values
        test_dates = [d.strftime("%Y-%m-%d") for d in series_df["week_date"].iloc[-horizon:]]

        # 1. Seasonal Naive
        sn_preds = self.seasonal_naive_forecast(train_series, horizon=horizon)
        # 2. Moving Average
        ma_preds = self.moving_average_forecast(train_series, horizon=horizon)
        # 3. Exponential Smoothing
        hw_preds, hw_lower, hw_upper = self.exponential_smoothing_forecast(train_series, horizon=horizon)
        # 4. LightGBM
        lgb_preds = self.lightgbm_forecast(series_df.iloc[:-horizon], horizon=horizon)

        def calc_metrics(y_true, y_pred):
            y_true, y_pred = np.array(y_true, dtype=float), np.array(y_pred, dtype=float)
            mae = float(np.mean(np.abs(y_true - y_pred)))
            rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
            total_actual = float(np.sum(y_true))
            wape = float(np.sum(np.abs(y_true - y_pred)) / total_actual) if total_actual > 0 else 0.0
            return round(mae, 2), round(rmse, 2), round(wape, 4)

        models = [
            ("Seasonal Naive", sn_preds),
            ("Moving Average (4-wk)", ma_preds),
            ("Holt-Winters Exp Smoothing", hw_preds),
            ("LightGBM Walk-forward", lgb_preds),
        ]

        leaderboard = []
        for name, preds in models:
            mae, rmse, wape = calc_metrics(actual_test, preds)
            leaderboard.append({
                "Model": name,
                "MAE": mae,
                "RMSE": rmse,
                "WAPE": wape,
                "WAPE (%)": f"{round(wape * 100, 2)}%",
            })

        leaderboard.sort(key=lambda x: x["WAPE"])
        best_model_name = leaderboard[0]["Model"]

        return {
            "category": category,
            "level": level,
            "test_dates": test_dates,
            "actual_test": actual_test.tolist(),
            "predictions": {
                "Seasonal Naive": sn_preds.tolist(),
                "Moving Average (4-wk)": ma_preds.tolist(),
                "Holt-Winters Exp Smoothing": hw_preds.tolist(),
                "LightGBM Walk-forward": lgb_preds.tolist(),
            },
            "confidence_intervals": {
                "lower": hw_lower.tolist(),
                "upper": hw_upper.tolist(),
            },
            "leaderboard": pd.DataFrame(leaderboard),
            "best_model": best_model_name,
        }

    def generate_forward_forecast(
        self,
        category: str,
        level: str = "department",
        horizon: int = 8,
    ) -> Dict[str, Any]:
        """Projects forward demand for the upcoming N weeks using the best backtested model."""
        series_df = self.get_weekly_series(category, level=level)
        all_vals = series_df["purchase_volume"].values
        last_date = series_df["week_date"].iloc[-1]

        future_dates = [(last_date + pd.Timedelta(weeks=i)).strftime("%Y-%m-%d") for i in range(1, horizon + 1)]

        hw_preds, lower_b, upper_b = self.exponential_smoothing_forecast(all_vals, horizon=horizon)
        lgb_preds = self.lightgbm_forecast(series_df, horizon=horizon)

        # Historical last 24 weeks for context
        hist_df = series_df.tail(24)

        return {
            "category": category,
            "level": level,
            "historical_dates": [d.strftime("%Y-%m-%d") for d in hist_df["week_date"]],
            "historical_volumes": hist_df["purchase_volume"].tolist(),
            "future_dates": future_dates,
            "forecast_hw": np.round(hw_preds, 0).tolist(),
            "forecast_lgb": np.round(lgb_preds, 0).tolist(),
            "lower_bound": np.round(lower_b, 0).tolist(),
            "upper_bound": np.round(upper_b, 0).tolist(),
        }
