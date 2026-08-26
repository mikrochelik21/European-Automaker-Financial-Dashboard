"""Charts for revenue forecasts."""

import pandas as pd


def create_revenue_forecast_chart(
    historical_revenue: pd.Series,
    forecast: pd.DataFrame,
    company_name: str,
) -> object:
    """Build historical bars, forecast line, and confidence band."""
    import plotly.graph_objects as go

    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=historical_revenue.index,
            y=historical_revenue.div(1_000_000_000),
            name="Historical revenue",
            marker_color="#1C69D4",
            hovertemplate="%{x|%Y}<br>Revenue: %{y:.2f}B<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=forecast.index,
            y=forecast["Revenue"].div(1_000_000_000),
            mode="lines+markers",
            name="Trend forecast",
            line={"color": "#F5B700", "dash": "dash", "width": 3},
            hovertemplate="%{x|%Y}<br>Forecast: %{y:.2f}B<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=forecast.index,
            y=forecast["Upper bound"].div(1_000_000_000),
            mode="lines",
            line={"color": "rgba(245, 183, 0, 0)"},
            name="95% confidence interval",
            showlegend=True,
            hoverinfo="skip",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=forecast.index,
            y=forecast["Lower bound"].div(1_000_000_000),
            mode="lines",
            line={"color": "rgba(245, 183, 0, 0)"},
            fill="tonexty",
            fillcolor="rgba(245, 183, 0, 0.18)",
            name="95% confidence interval",
            showlegend=False,
            hoverinfo="skip",
        )
    )
    figure.update_layout(
        title=f"{company_name}: revenue trend extrapolation",
        xaxis_title="Fiscal year",
        yaxis_title="Revenue (EUR billions)",
        hovermode="x unified",
        barmode="group",
    )
    return figure
