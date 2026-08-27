"""Annual fundamental financial data from Yahoo Finance."""

import pandas as pd
import streamlit as st


FUNDAMENTAL_ROWS = {
    "Revenue": "Total Revenue",
    "Net income": "Net Income",
    "EBITDA": "EBITDA",
}

OPERATING_INCOME_ROW = "Operating Income"
DEPRECIATION_ROW = "Depreciation And Amortization"


@st.cache_data(ttl=3600)
def fetch_income_statement(ticker_symbol: str) -> pd.DataFrame:
    """Fetch one company's annual income statement in chronological order."""
    import yfinance as yf

    statement = yf.Ticker(ticker_symbol).financials
    if statement.empty:
        raise ValueError(f"No income statement returned for {ticker_symbol}")
    return statement.sort_index(axis=1)


@st.cache_data(ttl=3600)
def fetch_cash_flow_statement(ticker_symbol: str) -> pd.DataFrame:
    """Fetch one company's annual cash-flow statement chronologically."""
    import yfinance as yf

    statement = yf.Ticker(ticker_symbol).cashflow
    if statement.empty:
        raise ValueError(f"No cash-flow statement returned for {ticker_symbol}")
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


def add_ebitda_fallback(
    fundamentals: pd.DataFrame,
    income_statement: pd.DataFrame,
    cash_flow_statement: pd.DataFrame,
) -> pd.DataFrame:
    """Fill missing EBITDA using operating income plus depreciation."""
    completed = fundamentals.copy()
    if "EBITDA" not in completed:
        completed["EBITDA"] = pd.NA

    if OPERATING_INCOME_ROW not in income_statement.index:
        return completed
    if DEPRECIATION_ROW not in cash_flow_statement.index:
        return completed

    operating_income = income_statement.loc[OPERATING_INCOME_ROW]
    depreciation = cash_flow_statement.loc[DEPRECIATION_ROW]
    fallback = operating_income.add(depreciation)
    completed["EBITDA"] = completed["EBITDA"].fillna(fallback)
    return completed


def calculate_ebitda_margin(fundamentals: pd.DataFrame) -> pd.Series:
    """Calculate EBITDA margin as a percentage of revenue."""
    required_columns = {"Revenue", "EBITDA"}
    if not required_columns.issubset(fundamentals.columns):
        raise ValueError("Fundamentals must include revenue and EBITDA")

    revenue = fundamentals["Revenue"].replace(0, pd.NA)
    return fundamentals["EBITDA"].div(revenue).mul(100).rename("EBITDA margin")


@st.cache_data(ttl=3600)
def load_prepared_fundamentals(ticker_symbol: str) -> pd.DataFrame:
    """Fetch and prepare all annual fundamentals for one company."""
    income_statement = fetch_income_statement(ticker_symbol)
    cash_flow_statement = fetch_cash_flow_statement(ticker_symbol)
    fundamentals = prepare_fundamentals(income_statement)
    return add_ebitda_fallback(
        fundamentals,
        income_statement,
        cash_flow_statement,
    )
