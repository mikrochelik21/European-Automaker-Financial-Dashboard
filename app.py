"""Streamlit entry point for the European automaker dashboard."""

from datetime import date

import streamlit as st

from charts.performance import create_performance_chart
from charts.fundamentals import (
    create_ebitda_margin_chart,
    create_revenue_income_chart,
)
from charts.valuation import create_valuation_charts
from config import COMPANIES, COMPANY_COLORS, DEFAULT_START_DATE
from data.fundamentals import (
    add_ebitda_fallback,
    calculate_ebitda_margin,
    fetch_cash_flow_statement,
    fetch_income_statement,
    prepare_fundamentals,
)
from data.prices import build_indexed_prices, fetch_price_history
from data.valuation import build_valuation_table, fetch_valuation_snapshot


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
    selected_company = st.selectbox(
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
        st.subheader("Indexed performance data")
        display_prices = indexed_prices.copy()
        display_prices.index.name = "Date"
        st.dataframe(
            display_prices.round(2),
            use_container_width=True,
        )
    except ValueError as error:
        st.error(f"Market data could not be prepared: {error}")
    except Exception:
        st.error("Market data is temporarily unavailable. Please try again later.")

with valuation_tab:
    st.subheader("Valuation multiples")
    try:
        with st.spinner("Loading valuation data..."):
            valuation_snapshots = {
                company: fetch_valuation_snapshot(ticker)
                for company, ticker in COMPANIES.items()
            }
            valuation_table = build_valuation_table(valuation_snapshots)
            valuation_charts = create_valuation_charts(
                valuation_table,
                COMPANY_COLORS,
            )

        chart_columns = st.columns(len(valuation_charts))
        for column, (metric, figure) in zip(chart_columns, valuation_charts.items()):
            with column:
                st.plotly_chart(figure, use_container_width=True)

        st.dataframe(valuation_table.round(2), use_container_width=True)
    except ValueError as error:
        st.error(f"Valuation data could not be prepared: {error}")
    except Exception:
        st.error("Valuation data is temporarily unavailable. Please try again later.")

with fundamentals_tab:
    st.subheader("Fundamental financials")
    selected_ticker = COMPANIES[selected_company]
    try:
        with st.spinner("Loading fundamental data..."):
            income_statement = fetch_income_statement(selected_ticker)
            cash_flow_statement = fetch_cash_flow_statement(selected_ticker)
            fundamentals = prepare_fundamentals(income_statement)
            fundamentals = add_ebitda_fallback(
                fundamentals,
                income_statement,
                cash_flow_statement,
            )
            ebitda_margin = calculate_ebitda_margin(fundamentals)

        st.plotly_chart(
            create_revenue_income_chart(fundamentals, selected_company),
            use_container_width=True,
        )
        st.plotly_chart(
            create_ebitda_margin_chart(ebitda_margin, selected_company),
            use_container_width=True,
        )
        display_fundamentals = fundamentals.div(1_000_000_000).round(2)
        display_fundamentals["EBITDA margin (%)"] = ebitda_margin.round(2)
        st.dataframe(display_fundamentals, use_container_width=True)
    except ValueError as error:
        st.error(f"Fundamental data could not be prepared: {error}")
    except Exception:
        st.error("Fundamental data is temporarily unavailable. Please try again later.")

with forecast_tab:
    st.subheader("Revenue forecast")
    st.info("The forecast panel will be added in a later block.")
