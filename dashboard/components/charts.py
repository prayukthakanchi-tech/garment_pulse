"""
GarmentPulse Dashboard — Chart Styling & Utilities
Ensures consistent, premium editorial fashion styling across all Plotly visualisations.
Adheres strictly to WCAG AA contrast standards and professional typography.
"""

from typing import Optional
import plotly.graph_objects as go

CHART_THEME = {
    "font_family": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    "background_color": "#FFFFFF",
    "paper_color": "#FFFFFF",
    "text_color": "#0F172A",        # Slate 900
    "muted_text_color": "#64748B",  # Slate 500
    "grid_color": "#F1F5F9",        # Slate 100
    "border_color": "#E2E8F0",      # Slate 200
    "primary_accent": "#2563EB",    # Cobalt blue
    "palette": [
        "#1E3A8A",  # Deep Cobalt
        "#0D9488",  # Deep Teal
        "#D97706",  # Warm Amber
        "#E11D48",  # Rose
        "#6366F1",  # Indigo
        "#0284C7",  # Cerulean
        "#059669",  # Emerald
        "#7C3AED",  # Violet
        "#EA580C",  # Burnt Orange
        "#475569",  # Slate
    ],
}


def apply_chart_style(
    fig: go.Figure,
    title: Optional[str] = None,
    x_title: Optional[str] = None,
    y_title: Optional[str] = None,
    height: int = 420,
    show_legend: bool = True,
) -> go.Figure:
    """Applies clean, high-contrast, editorial styling to a Plotly figure."""
    fig.update_layout(
        title={
            "text": f"<b>{title}</b>" if title else "",
            "font": {
                "size": 15,
                "color": CHART_THEME["text_color"],
                "family": CHART_THEME["font_family"],
            },
            "x": 0.01,
            "y": 0.95,
        },
        font={
            "family": CHART_THEME["font_family"],
            "color": CHART_THEME["text_color"],
            "size": 12,
        },
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
            "font": {"size": 11, "color": CHART_THEME["muted_text_color"]},
        },
        hoverlabel={
            "bgcolor": "#0F172A",
            "font_size": 12,
            "font_family": CHART_THEME["font_family"],
            "font_color": "#FFFFFF",
            "bordercolor": "#1E293B",
        },
    )

    fig.update_xaxes(
        title_text=x_title,
        title_font={"size": 12, "color": CHART_THEME["muted_text_color"]},
        showgrid=True,
        gridcolor=CHART_THEME["grid_color"],
        gridwidth=1,
        zeroline=False,
        linecolor=CHART_THEME["border_color"],
        ticks="outside",
        tickcolor=CHART_THEME["border_color"],
        tickfont={"size": 11, "color": CHART_THEME["muted_text_color"]},
    )

    fig.update_yaxes(
        title_text=y_title,
        title_font={"size": 12, "color": CHART_THEME["muted_text_color"]},
        showgrid=True,
        gridcolor=CHART_THEME["grid_color"],
        gridwidth=1,
        zeroline=False,
        linecolor=CHART_THEME["border_color"],
        ticks="outside",
        tickcolor=CHART_THEME["border_color"],
        tickfont={"size": 11, "color": CHART_THEME["muted_text_color"]},
    )

    return fig
