"""Charts for company fundamentals."""

import pandas as pd


def create_revenue_income_chart(
    fundamentals: pd.DataFrame,
    company_name: str,
) -> object:
    """Build a revenue bar and net-income line chart."""
    import plotly.graph_objects as go

    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=fundamentals.index,
            y=fundamentals["Revenue"].div(1_000_000_000),
            name="Revenue",
            marker_color="#1C69D4",
            hovertemplate="%{x|%Y}<br>Revenue: %{y:.2f}B<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=fundamentals.index,
            y=fundamentals["Net income"].div(1_000_000_000),
            name="Net income",
            mode="lines+markers",
            yaxis="y2",
            line={"color": "#F5B700", "width": 3},
            hovertemplate="%{x|%Y}<br>Net income: %{y:.2f}B<extra></extra>",
        )
    )
    figure.update_layout(
        title=f"{company_name}: revenue and net income",
        yaxis={"title": "Revenue (EUR billions)"},
        yaxis2={
            "title": "Net income (EUR billions)",
            "overlaying": "y",
            "side": "right",
        },
        hovermode="x unified",
        barmode="group",
    )
    return figure


def create_ebitda_margin_chart(ebitda_margin: pd.Series, company_name: str) -> object:
    """Build an EBITDA-margin trend chart."""
    import plotly.graph_objects as go

    figure = go.Figure(
        go.Scatter(
            x=ebitda_margin.index,
            y=ebitda_margin,
            mode="lines+markers",
            name="EBITDA margin",
            line={"color": "#00A19C", "width": 3},
            hovertemplate="%{x|%Y}<br>EBITDA margin: %{y:.2f}%<extra></extra>",
        )
    )
    figure.update_layout(
        title=f"{company_name}: EBITDA margin",
        xaxis_title="Fiscal year",
        yaxis_title="EBITDA margin (%)",
        hovermode="x unified",
    )
    return figure
