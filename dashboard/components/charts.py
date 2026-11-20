"""
GarmentPulse Dashboard — Chart Styling & Utilities
Ensures consistent, premium editorial fashion styling across all Plotly visualisations.
"""

import plotly.graph_objects as go
from config.settings import COLORS

CHART_THEME = {
    "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    "background_color": "#ffffff",
    "paper_color": "#ffffff",
    "text_color": "#1a1a2e",
    "muted_text_color": "#6c757d",
    "grid_color": "#f1f3f5",
    "palette": COLORS["chart_palette"],
}


def apply_chart_style(
    fig: go.Figure,
    title: str | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
    height: int = 420,
    show_legend: bool = True,
) -> go.Figure:
    """Applies clean, high-contrast, editorial styling to a Plotly figure."""
    fig.update_layout(
        title={
            "text": f"<b>{title}</b>" if title else "",
            "font": {"size": 15, "color": CHART_THEME["text_color"], "family": CHART_THEME["font_family"]},
            "x": 0.02,
            "y": 0.95,
        },
        font={"family": CHART_THEME["font_family"], "color": CHART_THEME["text_color"], "size": 12},
        paper_bgcolor=CHART_THEME["paper_color"],
        plot_bgcolor=CHART_THEME["background_color"],
        height=height,
        margin={"l": 50, "r": 30, "t": 60, "b": 50},
        showlegend=show_legend,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
            "font": {"size": 11},
        },
        hoverlabel={
            "bgcolor": "#1a1a2e",
            "font_size": 12,
            "font_family": CHART_THEME["font_family"],
            "font_color": "#ffffff",
        },
    )

    fig.update_xaxes(
        title_text=x_title,
        showgrid=True,
        gridcolor=CHART_THEME["grid_color"],
        gridwidth=1,
        zeroline=False,
        linecolor="#dee2e6",
        ticks="outside",
    )

    fig.update_yaxes(
        title_text=y_title,
        showgrid=True,
        gridcolor=CHART_THEME["grid_color"],
        gridwidth=1,
        zeroline=False,
        linecolor="#dee2e6",
        ticks="outside",
    )

    return fig
