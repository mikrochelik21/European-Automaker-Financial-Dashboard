"""Charts for valuation comparisons."""

from collections.abc import Mapping

import pandas as pd


def create_valuation_charts(
    valuation_table: pd.DataFrame,
    company_colors: Mapping[str, str],
) -> dict[str, object]:
    """Build sorted bar charts for each valuation multiple."""
    import plotly.graph_objects as go

    charts = {}
    for metric in valuation_table.columns:
        metric_values = valuation_table[metric].dropna().sort_values()
        charts[metric] = go.Figure(
            go.Bar(
                x=metric_values.index,
                y=metric_values.values,
                marker_color=[
                    company_colors.get(company) for company in metric_values.index
                ],
                name=metric,
                hovertemplate=(
                    "%{x}<br>"
                    f"{metric}: %{{y:.2f}}<extra></extra>"
                ),
            )
        ).update_layout(
            title=metric,
            xaxis_title="Company",
            yaxis_title="Multiple",
            showlegend=False,
        )
    return charts
