"""Revenue forecast scenarios."""

import pandas as pd


def build_revenue_scenarios(
    base_forecast: pd.DataFrame,
    adjustment: float = 0.10,
) -> pd.DataFrame:
    """Create bear, base, and bull revenue cases from a base forecast."""
    required_columns = {"Revenue", "Lower bound", "Upper bound"}
    if not required_columns.issubset(base_forecast.columns):
        raise ValueError("Forecast must include revenue and confidence bounds")
    if adjustment < 0 or adjustment >= 1:
        raise ValueError("Scenario adjustment must be between 0 and 1")

    base_revenue = base_forecast["Revenue"]
    scenarios = pd.DataFrame(
        {
            "Bear case": base_revenue * (1 - adjustment),
            "Base case": base_revenue,
            "Bull case": base_revenue * (1 + adjustment),
        },
        index=base_forecast.index,
    )
    return scenarios
