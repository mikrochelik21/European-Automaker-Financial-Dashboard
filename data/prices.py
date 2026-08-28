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


def fetch_price_histories(
    companies: Mapping[str, str],
    start_date: str,
) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    """Fetch company prices while recording individual failures."""
    histories = {}
    failures = {}
    for company, ticker_symbol in companies.items():
        try:
            histories[company] = fetch_price_history(ticker_symbol, start_date)
        except Exception as error:
            failures[company] = str(error)
    return histories, failures


def get_latest_market_date(price_history_by_company: Mapping[str, pd.DataFrame]) -> pd.Timestamp:
    """Return the latest date available across company price histories."""
    if not price_history_by_company:
        raise ValueError("At least one price history is required")

    latest_dates = [history.index.max() for history in price_history_by_company.values()]
    return max(latest_dates)


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


def calculate_weekly_return_correlation(
    price_history_by_company: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Calculate pairwise correlations of weekly closing-price returns."""
    if not price_history_by_company:
        raise ValueError("At least one price history is required")

    closing_prices = pd.concat(
        {
            company: history["Close"]
            for company, history in price_history_by_company.items()
        },
        axis=1,
    )
    weekly_prices = closing_prices.resample("W-FRI").last()
    weekly_returns = weekly_prices.pct_change().dropna(how="all")
    correlation = weekly_returns.corr()
    return correlation.reindex(
        index=price_history_by_company,
        columns=price_history_by_company,
    )


def summarize_correlation_pairs(correlation: pd.DataFrame) -> dict[str, object]:
    """Return the strongest and weakest distinct correlation pairs."""
    if correlation.shape[0] < 2 or correlation.shape[1] < 2:
        raise ValueError("At least two companies are required")

    pairs = []
    for row_index, company_a in enumerate(correlation.index):
        for column_index, company_b in enumerate(correlation.columns):
            if column_index <= row_index:
                continue
            value = correlation.loc[company_a, company_b]
            if pd.notna(value):
                pairs.append((company_a, company_b, float(value)))

    if not pairs:
        raise ValueError("Correlation matrix contains no comparable pairs")

    strongest = max(pairs, key=lambda pair: pair[2])
    weakest = min(pairs, key=lambda pair: pair[2])
    return {
        "Most correlated pair": f"{strongest[0]} / {strongest[1]}",
        "Most correlated value": strongest[2],
        "Least correlated pair": f"{weakest[0]} / {weakest[1]}",
        "Least correlated value": weakest[2],
    }
