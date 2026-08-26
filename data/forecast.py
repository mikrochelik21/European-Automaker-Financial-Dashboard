"""Revenue trend forecasting."""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def forecast_revenue(
    revenue: pd.Series,
    forecast_years: int = 2,
) -> pd.DataFrame:
    """Fit a linear revenue trend and extend it into future years."""
    clean_revenue = revenue.dropna()
    if len(clean_revenue) < 2:
        raise ValueError("At least two revenue observations are required")
    if forecast_years < 1:
        raise ValueError("Forecast years must be positive")

    historical_years = np.arange(len(clean_revenue), dtype=float)
    model = LinearRegression().fit(historical_years.reshape(-1, 1), clean_revenue)
    fitted_values = model.predict(historical_years.reshape(-1, 1))
    residual_std = np.std(clean_revenue - fitted_values)

    future_years = np.arange(
        len(clean_revenue),
        len(clean_revenue) + forecast_years,
        dtype=float,
    )
    forecast_values = model.predict(future_years.reshape(-1, 1))
    interval = 1.96 * residual_std

    historical_index = clean_revenue.index
    last_year = historical_index[-1].year
    forecast_index = pd.to_datetime(
        [f"{last_year + offset}-12-31" for offset in range(1, forecast_years + 1)]
    )
    return pd.DataFrame(
        {
            "Revenue": forecast_values,
            "Lower bound": forecast_values - interval,
            "Upper bound": forecast_values + interval,
        },
        index=forecast_index,
    )
