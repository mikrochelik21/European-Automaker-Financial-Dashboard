"""Tests for price-history transformations."""

import pandas as pd
import unittest
from importlib.util import find_spec
from types import SimpleNamespace
from unittest.mock import patch

from charts.performance import create_performance_chart
from charts.fundamentals import (
    create_ebitda_margin_chart,
    create_revenue_income_chart,
)
from charts.forecast import create_revenue_forecast_chart
from charts.valuation import create_valuation_charts
from data.prices import (
    build_indexed_prices,
    fetch_price_history,
    fetch_price_histories,
    normalize_prices,
)
from data.valuation import build_valuation_table, fetch_valuation_snapshot
from data.summary import build_peer_summary, calculate_peer_kpis
from data.fundamentals import (
    add_ebitda_fallback,
    calculate_ebitda_margin,
    fetch_cash_flow_statement,
    fetch_income_statement,
    load_prepared_fundamentals,
    prepare_fundamentals,
)
from data.forecast import forecast_revenue


class FetchPriceHistoryTests(unittest.TestCase):
    def test_fetches_adjusted_history_from_yahoo_finance(self):
        expected = pd.DataFrame({"Close": [20.0, 22.0]})
        fake_yfinance = SimpleNamespace(
            Ticker=lambda symbol: SimpleNamespace(
                history=lambda **kwargs: expected
            )
        )

        with patch.dict("sys.modules", {"yfinance": fake_yfinance}):
            history = fetch_price_history("MBG.DE", "2020-01-01")

        pd.testing.assert_frame_equal(history, expected)

    def test_records_partial_company_failures(self):
        expected = pd.DataFrame({"Close": [20.0, 22.0]})
        fake_yfinance = SimpleNamespace(
            Ticker=lambda symbol: SimpleNamespace(
                history=(
                    lambda **kwargs: expected
                    if symbol == "MBG.DE"
                    else (_ for _ in ()).throw(RuntimeError("rate limited"))
                )
            )
        )

        with patch.dict("sys.modules", {"yfinance": fake_yfinance}):
            histories, failures = fetch_price_histories(
                {"Mercedes-Benz": "MBG.DE", "BMW": "BMW.DE"},
                "2020-01-01",
            )

        self.assertEqual(list(histories), ["Mercedes-Benz"])
        self.assertIn("BMW", failures)


class FetchIncomeStatementTests(unittest.TestCase):
    def test_returns_annual_columns_in_chronological_order(self):
        latest = pd.Timestamp("2024-12-31")
        oldest = pd.Timestamp("2022-12-31")
        expected = pd.DataFrame(
            {latest: [120.0], oldest: [100.0]},
            index=["Total Revenue"],
        )
        fake_yfinance = SimpleNamespace(
            Ticker=lambda symbol: SimpleNamespace(financials=expected)
        )

        with patch.dict("sys.modules", {"yfinance": fake_yfinance}):
            statement = fetch_income_statement("MBG.DE")

        self.assertEqual(statement.columns.tolist(), [oldest, latest])

    def test_rejects_empty_income_statement(self):
        fake_yfinance = SimpleNamespace(
            Ticker=lambda symbol: SimpleNamespace(financials=pd.DataFrame())
        )

        with patch.dict("sys.modules", {"yfinance": fake_yfinance}):
            with self.assertRaisesRegex(ValueError, "No income statement"):
                fetch_income_statement("RNO.PA")


class FetchCashFlowStatementTests(unittest.TestCase):
    def test_returns_annual_cash_flow_columns_in_chronological_order(self):
        latest = pd.Timestamp("2024-12-31")
        oldest = pd.Timestamp("2022-12-31")
        expected = pd.DataFrame(
            {latest: [12.0], oldest: [10.0]},
            index=["Depreciation And Amortization"],
        )
        fake_yfinance = SimpleNamespace(
            Ticker=lambda symbol: SimpleNamespace(cashflow=expected)
        )

        with patch.dict("sys.modules", {"yfinance": fake_yfinance}):
            statement = fetch_cash_flow_statement("MBG.DE")

        self.assertEqual(statement.columns.tolist(), [oldest, latest])


class PrepareFundamentalsTests(unittest.TestCase):
    def test_selects_chart_metrics_and_years(self):
        statement = pd.DataFrame(
            {
                pd.Timestamp("2023-12-31"): [120.0, 10.0, 15.0],
                pd.Timestamp("2022-12-31"): [100.0, 8.0, 13.0],
            },
            index=["Total Revenue", "Net Income", "EBITDA"],
        )

        prepared = prepare_fundamentals(statement)

        self.assertEqual(
            prepared.columns.tolist(), ["Revenue", "Net income", "EBITDA"]
        )
        self.assertEqual(prepared.index.tolist(), list(statement.columns))
        self.assertEqual(prepared.loc[pd.Timestamp("2022-12-31"), "Revenue"], 100.0)

    def test_allows_missing_ebitda_for_later_fallback(self):
        statement = pd.DataFrame(
            {pd.Timestamp("2023-12-31"): [120.0, 10.0]},
            index=["Total Revenue", "Net Income"],
        )

        prepared = prepare_fundamentals(statement)

        self.assertTrue(pd.isna(prepared.loc[pd.Timestamp("2023-12-31"), "EBITDA"]))

    def test_calculates_ebitda_margin_as_percentage(self):
        fundamentals = pd.DataFrame(
            {"Revenue": [100.0, 200.0], "EBITDA": [10.0, 30.0]}
        )

        margin = calculate_ebitda_margin(fundamentals)

        self.assertEqual(margin.tolist(), [10.0, 15.0])


class AddEbitdaFallbackTests(unittest.TestCase):
    def test_fills_missing_ebitda_without_overwriting_reported_values(self):
        year = pd.Timestamp("2023-12-31")
        fundamentals = pd.DataFrame(
            {"Revenue": [120.0, 100.0], "Net income": [10.0, 8.0], "EBITDA": [None, 20.0]},
            index=[year, pd.Timestamp("2022-12-31")],
        )
        income_statement = pd.DataFrame(
            {year: [15.0]}, index=["Operating Income"]
        )
        cash_flow = pd.DataFrame(
            {year: [5.0]}, index=["Depreciation And Amortization"]
        )

        completed = add_ebitda_fallback(
            fundamentals,
            income_statement,
            cash_flow,
        )

        self.assertEqual(completed.loc[year, "EBITDA"], 20.0)
        self.assertEqual(completed.loc[pd.Timestamp("2022-12-31"), "EBITDA"], 20.0)


class LoadPreparedFundamentalsTests(unittest.TestCase):
    def test_combines_income_and_cash_flow_data(self):
        year = pd.Timestamp("2023-12-31")
        income_statement = pd.DataFrame(
            {year: [120.0, 10.0, 15.0]},
            index=["Total Revenue", "Net Income", "Operating Income"],
        )
        cash_flow = pd.DataFrame(
            {year: [5.0]}, index=["Depreciation And Amortization"]
        )
        fake_yfinance = SimpleNamespace(
            Ticker=lambda symbol: SimpleNamespace(
                financials=income_statement,
                cashflow=cash_flow,
            )
        )

        with patch.dict("sys.modules", {"yfinance": fake_yfinance}):
            prepared = load_prepared_fundamentals("STLAM.MI")

        self.assertEqual(prepared.loc[year, "Revenue"], 120.0)
        self.assertEqual(prepared.loc[year, "EBITDA"], 20.0)


class FundamentalsChartTests(unittest.TestCase):
    def test_combines_revenue_bars_and_net_income_line(self):
        fundamentals = pd.DataFrame(
            {
                "Revenue": [100_000_000_000, 120_000_000_000],
                "Net income": [8_000_000_000, 10_000_000_000],
            },
            index=pd.to_datetime(["2022-12-31", "2023-12-31"]),
        )

        figure = create_revenue_income_chart(fundamentals, "BMW")

        self.assertEqual(len(figure.data), 2)
        self.assertEqual(figure.data[0].type, "bar")
        self.assertEqual(figure.data[1].type, "scatter")
        self.assertEqual(figure.data[1].yaxis, "y2")

    def test_creates_ebitda_margin_line_chart(self):
        margin = pd.Series(
            [10.0, 12.5],
            index=pd.to_datetime(["2022-12-31", "2023-12-31"]),
            name="EBITDA margin",
        )

        figure = create_ebitda_margin_chart(margin, "BMW")

        self.assertEqual(len(figure.data), 1)
        self.assertEqual(figure.data[0].type, "scatter")
        self.assertEqual(figure.layout.yaxis.title.text, "EBITDA margin (%)")


class ForecastRevenueTests(unittest.TestCase):
    def test_projects_requested_number_of_future_years(self):
        revenue = pd.Series(
            [100.0, 110.0, 120.0],
            index=pd.to_datetime(
                ["2021-12-31", "2022-12-31", "2023-12-31"]
            ),
        )

        forecast = forecast_revenue(revenue, forecast_years=2)

        self.assertEqual(forecast.index.year.tolist(), [2024, 2025])
        self.assertEqual(forecast["Revenue"].tolist(), [130.0, 140.0])
        self.assertTrue((forecast["Lower bound"] <= forecast["Revenue"]).all())
        self.assertTrue((forecast["Revenue"] <= forecast["Upper bound"]).all())

    def test_rejects_insufficient_revenue_history(self):
        with self.assertRaisesRegex(ValueError, "At least two"):
            forecast_revenue(pd.Series([100.0]))


class ForecastChartTests(unittest.TestCase):
    def test_contains_history_forecast_and_confidence_band(self):
        historical = pd.Series(
            [100_000_000_000, 110_000_000_000],
            index=pd.to_datetime(["2022-12-31", "2023-12-31"]),
        )
        forecast = pd.DataFrame(
            {
                "Revenue": [120_000_000_000],
                "Lower bound": [115_000_000_000],
                "Upper bound": [125_000_000_000],
            },
            index=pd.to_datetime(["2024-12-31"]),
        )

        figure = create_revenue_forecast_chart(historical, forecast, "BMW")

        self.assertEqual(len(figure.data), 4)
        self.assertEqual(figure.data[0].type, "bar")
        self.assertEqual(figure.data[1].line.dash, "dash")
        self.assertEqual(figure.data[3].fill, "tonexty")
        self.assertEqual(figure.layout.hovermode, "x unified")


class FetchValuationSnapshotTests(unittest.TestCase):
    def test_fetches_requested_multiples(self):
        fake_yfinance = SimpleNamespace(
            Ticker=lambda symbol: SimpleNamespace(
                info={
                    "trailingPE": 7.5,
                    "enterpriseToEbitda": 4.2,
                    "priceToBook": 0.8,
                }
            )
        )

        with patch.dict("sys.modules", {"yfinance": fake_yfinance}):
            snapshot = fetch_valuation_snapshot("BMW.DE")

        self.assertEqual(
            snapshot,
            {"P/E": 7.5, "EV/EBITDA": 4.2, "P/B": 0.8},
        )

    def test_preserves_missing_multiples_as_none(self):
        fake_yfinance = SimpleNamespace(
            Ticker=lambda symbol: SimpleNamespace(info={"trailingPE": 7.5})
        )

        with patch.dict("sys.modules", {"yfinance": fake_yfinance}):
            snapshot = fetch_valuation_snapshot("MBG.DE")

        self.assertIsNone(snapshot["EV/EBITDA"])
        self.assertIsNone(snapshot["P/B"])


class BuildValuationTableTests(unittest.TestCase):
    def test_builds_company_by_metric_table(self):
        snapshots = {
            "BMW": {"P/E": 7.5, "EV/EBITDA": 4.2, "P/B": 0.8},
            "Renault": {"P/E": 5.1, "EV/EBITDA": 3.3, "P/B": 0.6},
        }

        table = build_valuation_table(snapshots)

        self.assertEqual(table.index.tolist(), ["BMW", "Renault"])
        self.assertEqual(table.columns.tolist(), ["P/E", "EV/EBITDA", "P/B"])
        self.assertEqual(table.loc["Renault", "EV/EBITDA"], 3.3)

    def test_rejects_empty_snapshot_mapping(self):
        with self.assertRaisesRegex(ValueError, "At least one company"):
            build_valuation_table({})


class BuildPeerSummaryTests(unittest.TestCase):
    def test_combines_latest_return_and_valuation_metrics(self):
        indexed_prices = pd.DataFrame(
            {"BMW": [100.0, 112.5], "Renault": [100.0, 98.0]},
            index=pd.to_datetime(["2020-01-01", "2020-01-02"]),
        )
        valuation_table = pd.DataFrame(
            {
                "P/E": [7.5, 5.1],
                "EV/EBITDA": [4.2, 3.3],
                "P/B": [0.8, 0.6],
            },
            index=["BMW", "Renault"],
        )

        summary = build_peer_summary(indexed_prices, valuation_table)

        self.assertEqual(
            summary.columns.tolist(),
            ["Stock return (%)", "P/E", "EV/EBITDA", "P/B"],
        )
        self.assertEqual(summary.loc["BMW", "Stock return (%)"], 12.5)
        self.assertEqual(summary.loc["Renault", "P/B"], 0.6)


class CalculatePeerKpisTests(unittest.TestCase):
    def test_calculates_best_performer_and_valuation_headlines(self):
        summary = pd.DataFrame(
            {
                "Stock return (%)": [12.5, -2.0],
                "P/E": [7.5, 5.1],
                "EV/EBITDA": [4.2, 3.3],
                "P/B": [0.8, 0.6],
            },
            index=["BMW", "Renault"],
        )

        kpis = calculate_peer_kpis(summary)

        self.assertEqual(kpis["Best performer"], "BMW")
        self.assertEqual(kpis["Best performer return (%)"], 12.5)
        self.assertEqual(kpis["Average P/E"], 6.3)
        self.assertEqual(kpis["Lowest EV/EBITDA"], "Renault")


class ValuationChartTests(unittest.TestCase):
    def test_creates_sorted_chart_for_each_metric(self):
        valuation_table = pd.DataFrame(
            {
                "P/E": [7.5, 5.1],
                "EV/EBITDA": [4.2, 3.3],
                "P/B": [0.8, 0.6],
            },
            index=["BMW", "Renault"],
        )

        charts = create_valuation_charts(
            valuation_table,
            {"BMW": "#1C69D4", "Renault": "#F5B700"},
        )

        self.assertEqual(list(charts), ["P/E", "EV/EBITDA", "P/B"])
        self.assertEqual(list(charts["P/E"].data[0].x), ["Renault", "BMW"])
        self.assertEqual(
            list(charts["P/E"].data[0].marker.color), ["#F5B700", "#1C69D4"]
        )


@unittest.skipUnless(find_spec("plotly"), "Plotly is not installed")
class PerformanceChartTests(unittest.TestCase):
    def test_chart_contains_one_trace_per_company(self):
        indexed_prices = pd.DataFrame(
            {"BMW": [100.0, 105.0], "Renault": [100.0, 98.0]},
            index=pd.to_datetime(["2020-01-01", "2020-01-02"]),
        )

        figure = create_performance_chart(
            indexed_prices,
            {"BMW": "#1C69D4", "Renault": "#F5B700"},
        )

        self.assertEqual(len(figure.data), 2)
        self.assertEqual(figure.layout.hovermode, "x unified")


class FundamentalsChartTests(unittest.TestCase):
    def test_combines_revenue_bars_and_net_income_line(self):
        fundamentals = pd.DataFrame(
            {
                "Revenue": [100_000_000_000, 120_000_000_000],
                "Net income": [8_000_000_000, 10_000_000_000],
            },
            index=pd.to_datetime(["2022-12-31", "2023-12-31"]),
        )

        figure = create_revenue_income_chart(fundamentals, "BMW")

        self.assertEqual(len(figure.data), 2)
        self.assertEqual(figure.data[0].type, "bar")
        self.assertEqual(figure.data[1].type, "scatter")
        self.assertEqual(figure.data[1].yaxis, "y2")
        self.assertEqual(figure.layout.hovermode, "x unified")


class NormalizePricesTests(unittest.TestCase):
    def test_starts_at_100(self):
        prices = pd.DataFrame({"Close": [20.0, 22.0, 18.0]})

        normalized = normalize_prices(prices)

        for actual, expected in zip(
            normalized["Indexed price"], [100.0, 110.0, 90.0]
        ):
            self.assertAlmostEqual(actual, expected)


    def test_drops_missing_closes(self):
        prices = pd.DataFrame({"Close": [20.0, None, 22.0]})

        normalized = normalize_prices(prices)

        self.assertAlmostEqual(normalized["Indexed price"].iloc[0], 100.0)
        self.assertAlmostEqual(normalized["Indexed price"].iloc[1], 110.0)


    def test_rejects_missing_close_column(self):
        with self.assertRaisesRegex(ValueError, "Missing required column"):
            normalize_prices(pd.DataFrame({"Price": [20.0]}))


class BuildIndexedPricesTests(unittest.TestCase):
    def test_aligns_companies_on_shared_dates(self):
        dates = pd.to_datetime(["2020-01-01", "2020-01-02"])
        histories = {
            "BMW": pd.DataFrame({"Close": [100.0, 110.0]}, index=dates),
            "Renault": pd.DataFrame(
                {"Close": [50.0, None]},
                index=dates,
            ),
        }

        indexed_prices = build_indexed_prices(histories)

        self.assertEqual(indexed_prices.columns.tolist(), ["BMW", "Renault"])
        self.assertEqual(indexed_prices.index.tolist(), [dates[0]])
        self.assertAlmostEqual(indexed_prices.loc[dates[0], "BMW"], 100.0)
        self.assertAlmostEqual(indexed_prices.loc[dates[0], "Renault"], 100.0)

    def test_rejects_empty_company_mapping(self):
        with self.assertRaisesRegex(ValueError, "At least one company"):
            build_indexed_prices({})


if __name__ == "__main__":
    unittest.main()
