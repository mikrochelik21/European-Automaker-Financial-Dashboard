"""Tests for price-history transformations."""

import pandas as pd
import unittest

from data.prices import normalize_prices


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
