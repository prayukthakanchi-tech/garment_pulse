"""
GarmentPulse Dashboard — Metric Card Components
Styled editorial KPI display cards.
"""

import streamlit as st


def render_metric_card(
    label: str,
    value: str,
    delta: str | None = None,
    delta_color: str = "normal",
    help_text: str | None = None,
) -> None:
    """Renders a styled editorial fashion KPI card."""
    delta_html = ""
    if delta:
        color = "#2a9d8f" if delta.startswith("+") else ("#e76f51" if delta.startswith("-") else "#6c757d")
        delta_html = f'<div style="font-size: 0.85rem; font-weight: 600; color: {color}; margin-top: 4px;">{delta}</div>'

    help_attr = f'title="{help_text}"' if help_text else ""

    card_html = f"""
    <div {help_attr} style="
        background: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        margin-bottom: 12px;
    ">
        <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #6c757d;">
            {label}
        </div>
        <div style="font-size: 1.8rem; font-weight: 700; color: #1a1a2e; margin-top: 4px; line-height: 1.2;">
            {value}
        </div>
        {delta_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_kpi_row(metrics: list[dict]) -> None:
    """Renders a responsive horizontal row of KPI cards."""
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            render_metric_card(
                label=m["label"],
                value=m["value"],
                delta=m.get("delta"),
                help_text=m.get("help"),
            )
