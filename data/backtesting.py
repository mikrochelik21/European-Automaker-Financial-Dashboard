"""Backtesting utilities for revenue forecasts."""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def backtest_revenue_forecast(revenue: pd.Series, minimum_training_years: int = 2) -> dict[str, float]:
    """Evaluate one-year-ahead linear forecasts with expanding training windows."""
    clean_revenue = revenue.dropna()
    if len(clean_revenue) <= minimum_training_years:
        raise ValueError("More revenue observations than minimum training years are required")
    if minimum_training_years < 2:
        raise ValueError("Minimum training years must be at least two")
    if (clean_revenue <= 0).any():
        raise ValueError("Revenue observations must be positive")

    actual_values = []
    predicted_values = []
    for test_position in range(minimum_training_years, len(clean_revenue)):
        training_values = clean_revenue.iloc[:test_position]
        training_years = np.arange(len(training_values), dtype=float)
        model = LinearRegression().fit(
            training_years.reshape(-1, 1),
            training_values,
        )
        next_year = np.array([[len(training_values)]], dtype=float)
        predicted_values.append(model.predict(next_year)[0])
        actual_values.append(clean_revenue.iloc[test_position])

    actual = np.asarray(actual_values)
    predicted = np.asarray(predicted_values)
    return {
        "MAE (EUR)": float(np.mean(np.abs(actual - predicted))),
        "MAPE (%)": float(np.mean(np.abs((actual - predicted) / actual)) * 100),
        "Backtest observations": float(len(actual)),
    }
