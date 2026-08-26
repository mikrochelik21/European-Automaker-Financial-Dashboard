"""Streamlit entry point for the European automaker dashboard."""

from datetime import date

import streamlit as st

from charts.performance import create_performance_chart
from config import COMPANIES, COMPANY_COLORS, DEFAULT_START_DATE
from data.prices import build_indexed_prices, fetch_price_history


st.set_page_config(
    page_title="European Automaker Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("European Automaker Financial Dashboard")
st.caption("A live peer comparison of five major European automakers.")

with st.sidebar:
    st.header("Dashboard controls")
    start_date = st.date_input(
        "Stock performance start date",
        value=date.fromisoformat(DEFAULT_START_DATE),
    )
    st.selectbox(
        "Company for fundamentals and forecast",
        options=list(COMPANIES),
        index=0,
    )

stock_tab, valuation_tab, fundamentals_tab, forecast_tab = st.tabs(
    ["Stock performance", "Valuation", "Fundamentals", "Revenue forecast"]
)

with stock_tab:
    st.subheader("Stock performance")
    try:
        with st.spinner("Loading market data..."):
            price_histories = {
                company: fetch_price_history(ticker, start_date.isoformat())
                for company, ticker in COMPANIES.items()
            }
            indexed_prices = build_indexed_prices(price_histories)

        st.plotly_chart(
            create_performance_chart(indexed_prices, COMPANY_COLORS),
            use_container_width=True,
        )
    except ValueError as error:
        st.error(f"Market data could not be prepared: {error}")
    except Exception:
        st.error("Market data is temporarily unavailable. Please try again later.")

with valuation_tab:
    st.subheader("Valuation multiples")
    st.info("The valuation panel will be added in a later block.")

with fundamentals_tab:
    st.subheader("Fundamental financials")
    st.info("The fundamentals panel will be added in a later block.")

with forecast_tab:
    st.subheader("Revenue forecast")
    st.info("The forecast panel will be added in a later block.")
