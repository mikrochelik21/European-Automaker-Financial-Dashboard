"""Charts for stock-return correlations."""

import pandas as pd


def create_correlation_heatmap(correlation: pd.DataFrame) -> object:
    """Build a heatmap for pairwise weekly-return correlations."""
    import plotly.graph_objects as go

    figure = go.Figure(
        go.Heatmap(
            z=correlation.values,
            x=correlation.columns,
            y=correlation.index,
            zmin=-1,
            zmax=1,
            colorscale="RdBu",
            reversescale=True,
            text=correlation.round(2).values,
            texttemplate="%{text}",
            hovertemplate="%{y} vs %{x}<br>Correlation: %{z:.2f}<extra></extra>",
        )
    )
    figure.update_layout(
        title="Weekly stock-return correlation",
        xaxis_title="Company",
        yaxis_title="Company",
    )
    return figure
