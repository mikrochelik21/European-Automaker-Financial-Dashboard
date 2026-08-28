"""Charts for revenue scenarios."""

import pandas as pd


SCENARIO_COLORS = {
    "Bear case": "#C2410C",
    "Base case": "#1C69D4",
    "Bull case": "#15803D",
}


def create_revenue_scenarios_chart(
    scenarios: pd.DataFrame,
    company_name: str,
) -> object:
    """Build a line chart comparing bear, base, and bull revenue cases."""
    import plotly.graph_objects as go

    figure = go.Figure()
    for scenario, color in SCENARIO_COLORS.items():
        if scenario not in scenarios:
            continue
        figure.add_trace(
            go.Scatter(
                x=scenarios.index,
                y=scenarios[scenario].div(1_000_000_000),
                mode="lines+markers",
                name=scenario,
                line={"color": color, "width": 3},
                hovertemplate=(
                    "%{x|%Y}<br>"
                    f"{scenario}: %{{y:.2f}}B<extra></extra>"
                ),
            )
        )
    figure.update_layout(
        title=f"{company_name}: revenue scenarios",
        xaxis_title="Fiscal year",
        yaxis_title="Revenue (EUR billions)",
        hovermode="x unified",
    )
    return figure
