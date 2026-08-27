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


def calculate_peer_kpis(peer_summary: pd.DataFrame) -> dict[str, str | float]:
    """Calculate headline comparison metrics from the peer summary."""
    if peer_summary.empty:
        raise ValueError("Peer summary cannot be empty")

    valid_returns = peer_summary["Stock return (%)"].dropna()
    valid_pe = peer_summary["P/E"].dropna()
    valid_ev_ebitda = peer_summary["EV/EBITDA"].dropna()
    if valid_returns.empty or valid_pe.empty or valid_ev_ebitda.empty:
        raise ValueError("Peer summary lacks values required for KPI calculation")

    return {
        "Best performer": valid_returns.idxmax(),
        "Best performer return (%)": valid_returns.max(),
        "Average P/E": valid_pe.mean(),
        "Lowest EV/EBITDA": valid_ev_ebitda.idxmin(),
        "Lowest EV/EBITDA value": valid_ev_ebitda.min(),
    }
