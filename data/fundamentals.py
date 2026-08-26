"""Annual fundamental financial data from Yahoo Finance."""

import pandas as pd
import streamlit as st


FUNDAMENTAL_ROWS = {
    "Revenue": "Total Revenue",
    "Net income": "Net Income",
    "EBITDA": "EBITDA",
}


@st.cache_data(ttl=3600)
def fetch_income_statement(ticker_symbol: str) -> pd.DataFrame:
    """Fetch one company's annual income statement in chronological order."""
    import yfinance as yf

    statement = yf.Ticker(ticker_symbol).financials
    if statement.empty:
        raise ValueError(f"No income statement returned for {ticker_symbol}")
    return statement.sort_index(axis=1)


def prepare_fundamentals(statement: pd.DataFrame) -> pd.DataFrame:
    """Select and rename annual metrics for the fundamentals charts."""
    available_rows = {
        label: source_row
        for label, source_row in FUNDAMENTAL_ROWS.items()
        if source_row in statement.index
    }
    if "Revenue" not in available_rows or "Net income" not in available_rows:
        raise ValueError("Income statement must include revenue and net income")

    prepared = statement.reindex(index=list(available_rows.values())).copy()
    prepared.index = list(available_rows)
    return prepared.transpose().reindex(columns=FUNDAMENTAL_ROWS)
