"""Streamlit entry point for the European automaker dashboard."""

from datetime import date, datetime, timezone

import streamlit as st

from charts.performance import create_performance_chart
from charts.fundamentals import (
    create_ebitda_margin_chart,
    create_revenue_income_chart,
)
from charts.forecast import create_revenue_forecast_chart
from charts.valuation import create_valuation_charts
from config import COMPANIES, COMPANY_COLORS, DEFAULT_START_DATE, FORECAST_YEARS
from data.fundamentals import (
    calculate_ebitda_margin,
    load_prepared_fundamentals,
)
from data.prices import build_indexed_prices, fetch_price_histories
from data.summary import build_peer_summary, calculate_peer_kpis
from data.valuation import (
    build_valuation_table,
    fetch_valuation_snapshot,
    fetch_valuation_snapshots,
)
from data.forecast import forecast_revenue


st.set_page_config(
    page_title="European Automaker Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("European Automaker Financial Dashboard")
st.caption("A live peer comparison of five major European automakers.")
st.caption("Source: Yahoo Finance via yfinance | Annual financial data and daily prices")

with st.sidebar:
    st.header("Dashboard controls")
    if st.button("Refresh data"):
        st.session_state["last_refresh"] = datetime.now(timezone.utc)
        st.cache_data.clear()
        st.rerun()
    if "last_refresh" not in st.session_state:
        st.session_state["last_refresh"] = datetime.now(timezone.utc)
    st.caption(
        "Data checked: "
        f"{st.session_state['last_refresh'].strftime('%Y-%m-%d %H:%M UTC')}"
    )
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
            price_histories, price_failures = fetch_price_histories(
                COMPANIES,
                start_date.isoformat(),
            )
            if price_failures:
                st.warning(
                    "Price data unavailable for: "
                    + ", ".join(price_failures)
                )
            indexed_prices = build_indexed_prices(price_histories)

        st.plotly_chart(
            create_performance_chart(indexed_prices, COMPANY_COLORS),
            width="stretch",
        )
        valuation_snapshots = {
            company: fetch_valuation_snapshot(ticker)
            for company, ticker in COMPANIES.items()
        }
        valuation_table = build_valuation_table(valuation_snapshots)
        peer_summary = build_peer_summary(indexed_prices, valuation_table)
        peer_kpis = calculate_peer_kpis(peer_summary)
        kpi_columns = st.columns(3)
        kpi_columns[0].metric(
            "Best performer",
            peer_kpis["Best performer"],
            f"{peer_kpis['Best performer return (%)']:.2f}% return",
        )
        kpi_columns[1].metric(
            "Average P/E",
            f"{peer_kpis['Average P/E']:.2f}x",
        )
        kpi_columns[2].metric(
            "Lowest EV/EBITDA",
            peer_kpis["Lowest EV/EBITDA"],
            f"{peer_kpis['Lowest EV/EBITDA value']:.2f}x",
        )
        st.subheader("Peer comparison summary")
        st.dataframe(
            peer_summary.style.format(
                {
                    "Stock return (%)": "{:.2f}%",
                    "P/E": "{:.2f}x",
                    "EV/EBITDA": "{:.2f}x",
                    "P/B": "{:.2f}x",
                }
            ),
            width="stretch",
        )
        st.subheader("Indexed performance data")
        display_prices = indexed_prices.copy()
        display_prices.index.name = "Date"
        st.dataframe(
            display_prices.round(2),
            width="stretch",
        )
    except ValueError as error:
        st.error(f"Market data could not be prepared: {error}")
    except Exception:
        st.error("Market data is temporarily unavailable. Please try again later.")

with valuation_tab:
    st.subheader("Valuation multiples")
    try:
        with st.spinner("Loading valuation data..."):
            valuation_snapshots, valuation_failures = fetch_valuation_snapshots(
                COMPANIES
            )
            if valuation_failures:
                st.warning(
                    "Valuation data unavailable for: "
                    + ", ".join(valuation_failures)
                )
            valuation_table = build_valuation_table(valuation_snapshots)
            valuation_charts = create_valuation_charts(
                valuation_table,
                COMPANY_COLORS,
            )

        chart_columns = st.columns(len(valuation_charts))
        for column, (metric, figure) in zip(chart_columns, valuation_charts.items()):
            with column:
                st.plotly_chart(figure, width="stretch")

        st.dataframe(valuation_table.round(2), width="stretch")
    except ValueError as error:
        st.error(f"Valuation data could not be prepared: {error}")
    except Exception:
        st.error("Valuation data is temporarily unavailable. Please try again later.")

with fundamentals_tab:
    st.subheader("Fundamental financials")
    selected_ticker = COMPANIES[selected_company]
    try:
        with st.spinner("Loading fundamental data..."):
            fundamentals = load_prepared_fundamentals(selected_ticker)
            ebitda_margin = calculate_ebitda_margin(fundamentals)

        st.plotly_chart(
            create_revenue_income_chart(fundamentals, selected_company),
            width="stretch",
        )
        st.plotly_chart(
            create_ebitda_margin_chart(ebitda_margin, selected_company),
            width="stretch",
        )
        display_fundamentals = fundamentals.div(1_000_000_000).round(2)
        display_fundamentals["EBITDA margin (%)"] = ebitda_margin.round(2)
        st.dataframe(display_fundamentals, width="stretch")
    except ValueError as error:
        st.error(f"Fundamental data could not be prepared: {error}")
    except Exception:
        st.warning(
            f"Fundamental data is unavailable for {selected_company}. "
            "Please try again later."
        )

with forecast_tab:
    st.subheader("Revenue forecast")
    selected_ticker = COMPANIES[selected_company]
    try:
        with st.spinner("Building revenue forecast..."):
            forecast_fundamentals = load_prepared_fundamentals(selected_ticker)
            revenue_forecast = forecast_revenue(
                forecast_fundamentals["Revenue"],
                forecast_years=FORECAST_YEARS,
            )

        st.plotly_chart(
            create_revenue_forecast_chart(
                forecast_fundamentals["Revenue"],
                revenue_forecast,
                selected_company,
            ),
            width="stretch",
        )
        st.caption(
            "This is a linear trend extrapolation based on historical revenue, "
            "not a valuation model."
        )
        st.dataframe(
            revenue_forecast.div(1_000_000_000).round(2),
            width="stretch",
        )
    except ValueError as error:
        st.error(f"Revenue forecast could not be prepared: {error}")
    except Exception:
        st.warning(
            f"Revenue forecast is unavailable for {selected_company}. "
            "Please try again later."
        )
