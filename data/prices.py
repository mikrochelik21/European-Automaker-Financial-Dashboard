"""Price-history transformations for the dashboard."""

import pandas as pd


def normalize_prices(prices: pd.DataFrame, close_column: str = "Close") -> pd.DataFrame:
    """Index closing prices to 100 on the first available observation."""
    if close_column not in prices.columns:
        raise ValueError(f"Missing required column: {close_column}")

    clean_prices = prices[[close_column]].dropna().copy()
    if clean_prices.empty:
        raise ValueError("Price data cannot be empty")

    clean_prices["Indexed price"] = clean_prices[close_column].div(
        clean_prices[close_column].iloc[0]
    ).mul(100)
    return clean_prices
