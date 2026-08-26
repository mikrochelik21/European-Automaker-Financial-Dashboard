"""Streamlit entry point for the European automaker dashboard."""

import streamlit as st

from config import COMPANIES, DEFAULT_START_DATE


st.set_page_config(
    page_title="European Automaker Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("European Automaker Financial Dashboard")
st.caption("A live peer comparison of five major European automakers.")

with st.sidebar:
    st.header("Dashboard controls")
    st.date_input("Stock performance start date", value=DEFAULT_START_DATE)
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
    st.info("The normalized price chart will be added in the next block.")

with valuation_tab:
    st.subheader("Valuation multiples")
    st.info("The valuation panel will be added in a later block.")

with fundamentals_tab:
    st.subheader("Fundamental financials")
    st.info("The fundamentals panel will be added in a later block.")

with forecast_tab:
    st.subheader("Revenue forecast")
    st.info("The forecast panel will be added in a later block.")
