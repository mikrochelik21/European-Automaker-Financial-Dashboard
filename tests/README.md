# Tests

The test suite uses Python's built-in `unittest` framework.

Run all tests from the repository root:

```powershell
python -m unittest discover -v
```

The tests cover:

- Yahoo Finance price, valuation, income-statement, and cash-flow boundaries
- Missing-data and malformed-input handling
- Price normalization and weekly return correlation
- Valuation and peer-summary calculations
- EBITDA fallback and margin calculations
- Revenue regression forecasts, scenarios, and backtesting
- Plotly chart structure and key visual properties

External Yahoo Finance calls are mocked in unit tests, so the suite is deterministic and does not depend on network availability.
