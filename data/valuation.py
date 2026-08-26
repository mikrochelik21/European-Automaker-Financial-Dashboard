"""Valuation data fetched from Yahoo Finance."""

import streamlit as st
import pandas as pd


VALUATION_FIELDS = {
    "P/E": "trailingPE",
    "EV/EBITDA": "enterpriseToEbitda",
    "P/B": "priceToBook",
}


@st.cache_data(ttl=3600)
def fetch_valuation_snapshot(ticker_symbol: str) -> dict[str, float | None]:
    """Fetch current valuation multiples for one ticker."""
    import yfinance as yf

    info = yf.Ticker(ticker_symbol).info
    return {
        metric: info.get(yahoo_field)
        for metric, yahoo_field in VALUATION_FIELDS.items()
    }


def build_valuation_table(
    snapshot_by_company: dict[str, dict[str, float | None]],
) -> pd.DataFrame:
    """Build a company-by-metric valuation comparison table."""
    if not snapshot_by_company:
        raise ValueError("At least one company valuation is required")

    table = pd.DataFrame.from_dict(snapshot_by_company, orient="index")
    return table.reindex(columns=VALUATION_FIELDS).rename_axis("Company")
