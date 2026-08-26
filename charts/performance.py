"""Charts for relative stock performance."""

from collections.abc import Mapping

import pandas as pd


def create_performance_chart(
    indexed_prices: pd.DataFrame,
    company_colors: Mapping[str, str],
):
    """Build an indexed stock-performance chart with a 100 baseline."""
    import plotly.graph_objects as go

    figure = go.Figure()
    for company in indexed_prices.columns:
        figure.add_trace(
            go.Scatter(
                x=indexed_prices.index,
                y=indexed_prices[company],
                mode="lines",
                name=company,
                line={"color": company_colors.get(company)},
                customdata=(indexed_prices[company] - 100).round(2),
                hovertemplate=(
                    "%{x|%d %b %Y}<br>"
                    "Indexed value: %{y:.2f}<br>"
                    "Return: %{customdata:.2f}%<extra>%{fullData.name}</extra>"
                ),
            )
        )

    figure.add_hline(y=100, line_dash="dash", line_color="#6B7280")
    figure.update_layout(
        title="Indexed stock performance",
        yaxis_title="Indexed value (start = 100)",
        hovermode="x unified",
        legend_title="Company",
    )
    return figure
