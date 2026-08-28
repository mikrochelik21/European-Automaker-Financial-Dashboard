# European Automaker Financial Dashboard

**Live dashboard:** [Add the Streamlit Community Cloud URL after deployment](https://streamlit.io/)

Interactive financial analysis of Mercedes-Benz, BMW, Volkswagen, Stellantis, and Renault using live Yahoo Finance data.

<!-- Add a dashboard screenshot here after the first deployment. -->

## What it shows

- Normalized stock performance from a user-selected start date
- Current P/E, EV/EBITDA, and P/B valuation comparisons
- Historical revenue, net income, and EBITDA margin
- Two-year revenue trend extrapolation with a 95% residual-based interval
- Bear, base, and bull revenue scenarios using a transparent +/-10% adjustment
- Weekly stock-return correlation heatmap with strongest and weakest pair summaries
- Peer KPI cards, data freshness information, and partial-data warnings

The forecast is a linear trend extrapolation, not a valuation model. It does not include management guidance, analyst estimates, macroeconomic scenarios, or company-specific events.

The dashboard caches Yahoo Finance responses for one hour and includes a manual refresh control. Missing data for one company is reported without hiding successful peer results where possible.

## Tech stack

Python, pandas, NumPy, Plotly, scikit-learn, Streamlit, and yfinance.

## Run locally

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

Run the test suite with:

```powershell
python -m unittest discover -v
```

## Project structure

```text
app.py                 Streamlit entry point
config.py              Companies, tickers, colors, and constants
data/                  Cached data fetching and preparation
charts/                Plotly chart builders
tests/                 Offline unit tests
```

## Data source

Market prices and financial statements are fetched from Yahoo Finance through the `yfinance` library. Data availability can vary by company and reporting period.

## Deploy

1. Push this repository to GitHub.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/) and connect the repository.
3. Select `app.py` as the main file and deploy.
4. Replace the live dashboard placeholder at the top of this README with the deployed URL.
