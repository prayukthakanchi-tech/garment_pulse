"""
GarmentPulse Dashboard — Metric Card Components
Premium enterprise fashion-tech KPI display cards with high WCAG AA contrast and elegant typography.
"""

from typing import Any, Dict, List, Optional
import streamlit as st


def render_metric_card(
    label: str,
    value: str,
    delta: Optional[str] = None,
    help_text: Optional[str] = None,
) -> None:
    """Renders a sleek, editorial fashion-tech KPI card."""
    delta_html = ""
    if delta:
        if delta.startswith("+") or "increase" in delta.lower() or "growth" in delta.lower():
            color = "#059669"  # Emerald green
            bg = "#ECFDF5"
        elif delta.startswith("-") or "decrease" in delta.lower() or "decline" in delta.lower():
            color = "#DC2626"  # Crimson red
            bg = "#FEF2F2"
        else:
            color = "#475569"  # Slate
            bg = "#F1F5F9"
        delta_html = f"""
        <div style="display: inline-block; font-size: 0.75rem; font-weight: 600; color: {color}; background: {bg}; padding: 3px 8px; border-radius: 9999px; margin-top: 6px;">
            {delta}
        </div>
        """

    help_tooltip = f'title="{help_text}"' if help_text else ""

    card_html = f"""
    <div {help_tooltip} style="
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 18px 20px;
        box-shadow: 0 1px 3px 0 rgba(15, 23, 42, 0.05);
        margin-bottom: 12px;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    ">
        <div style="
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748B;
            margin-bottom: 6px;
        ">
            {label}
        </div>
        <div style="
            font-size: 1.85rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: #0F172A;
            line-height: 1.15;
        ">
            {value}
        </div>
        {delta_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_kpi_row(metrics: List[Dict[str, Any]]) -> None:
    """Renders a responsive horizontal grid of KPI cards."""
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            render_metric_card(
                label=m["label"],
                value=m["value"],
                delta=m.get("delta"),
                help_text=m.get("help"),
            )
