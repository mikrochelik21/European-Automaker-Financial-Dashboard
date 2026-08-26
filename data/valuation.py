"""Valuation data fetched from Yahoo Finance."""

import streamlit as st


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
