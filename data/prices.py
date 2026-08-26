"""Price-history transformations for the dashboard."""

import pandas as pd
import streamlit as st
from collections.abc import Mapping


@st.cache_data(ttl=3600)
def fetch_price_history(ticker_symbol: str, start_date: str) -> pd.DataFrame:
    """Fetch adjusted daily prices for one ticker from Yahoo Finance."""
    import yfinance as yf

    history = yf.Ticker(ticker_symbol).history(
        start=start_date,
        auto_adjust=True,
    )
    if history.empty:
        raise ValueError(f"No price history returned for {ticker_symbol}")
    return history


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


def build_indexed_prices(
    price_history_by_company: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Align and normalize closing prices for several companies."""
    if not price_history_by_company:
        raise ValueError("At least one company price history is required")

    indexed_by_company = {
        company: normalize_prices(history)["Indexed price"]
        for company, history in price_history_by_company.items()
    }
    return pd.concat(indexed_by_company, axis=1).dropna()
