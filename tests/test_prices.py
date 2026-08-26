"""Tests for price-history transformations."""

import pandas as pd
import unittest
from importlib.util import find_spec
from types import SimpleNamespace
from unittest.mock import patch

from charts.performance import create_performance_chart
from data.prices import fetch_price_history, normalize_prices


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


if __name__ == "__main__":
    unittest.main()
