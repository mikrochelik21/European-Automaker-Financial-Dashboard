"""Combined peer-comparison summaries."""

import pandas as pd


def build_peer_summary(
    indexed_prices: pd.DataFrame,
    valuation_table: pd.DataFrame,
) -> pd.DataFrame:
    """Combine latest stock returns with valuation multiples by company."""
    if indexed_prices.empty:
        raise ValueError("Indexed prices cannot be empty")
    if valuation_table.empty:
        raise ValueError("Valuation table cannot be empty")

    latest_indexed = indexed_prices.iloc[-1].rename("Stock return (%)").sub(100)
    summary = valuation_table.join(latest_indexed, how="outer")
    return summary.reindex(
        columns=["Stock return (%)", "P/E", "EV/EBITDA", "P/B"]
    )
