"""Annual fundamental financial data from Yahoo Finance."""

import pandas as pd
import streamlit as st


@st.cache_data(ttl=3600)
def fetch_income_statement(ticker_symbol: str) -> pd.DataFrame:
    """Fetch one company's annual income statement in chronological order."""
    import yfinance as yf

    statement = yf.Ticker(ticker_symbol).financials
    if statement.empty:
        raise ValueError(f"No income statement returned for {ticker_symbol}")
    return statement.sort_index(axis=1)
