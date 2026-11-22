"""
GarmentPulse Dashboard — Metric Card Components
Premium enterprise fashion-tech KPI display cards with high WCAG AA contrast,
gradient accent borders, subtle elevation shadows, and editorial typography.
"""

from typing import Any, Dict, List, Optional
import streamlit as st

# Color accents for cards in a row
ACCENT_PALETTES = [
    ("#2563EB", "#60A5FA", "#EFF6FF", "PORTFOLIO"),     # Blue
    ("#059669", "#34D399", "#ECFDF5", "REACH"),         # Emerald
    ("#7C3AED", "#A78BFA", "#F5F3FF", "ASSORTMENT"),    # Violet
    ("#D97706", "#FBBF24", "#FFFBEB", "INDEX"),         # Amber
    ("#0D9488", "#2DD4BF", "#F0FDFA", "EFFICIENCY"),    # Teal
    ("#475569", "#94A3B8", "#F8FAFC", "STATUS"),        # Slate
]


def render_metric_card(
    label: str,
    value: str,
    delta: Optional[str] = None,
    help_text: Optional[str] = None,
    accent_color: str = "#2563EB",
    accent_light: str = "#60A5FA",
    badge: Optional[str] = None,
    caption: Optional[str] = None,
) -> None:
    """Renders a sleek, editorial fashion-tech KPI card with top accent stripe."""
    delta_html = ""
    if delta:
        if delta.startswith("+") or "increase" in delta.lower() or "growth" in delta.lower():
            color = "#047857"  # Emerald green
            bg = "#ECFDF5"
            border = "#A7F3D0"
        elif delta.startswith("-") or "decrease" in delta.lower() or "decline" in delta.lower():
            color = "#B91C1C"  # Crimson red
            bg = "#FEF2F2"
            border = "#FECACA"
        else:
            color = "#475569"  # Slate
            bg = "#F1F5F9"
            border = "#E2E8F0"
        delta_html = f"""
        <div style="display: inline-flex; align-items: center; font-size: 0.72rem; font-weight: 600; color: {color}; background: {bg}; border: 1px solid {border}; padding: 2px 8px; border-radius: 9999px; margin-top: 6px;">
            {delta}
        </div>
        """

    caption_html = ""
    if caption:
        caption_html = f"""
        <div style="font-size: 0.73rem; color: #94A3B8; margin-top: 6px; font-weight: 500; display: flex; align-items: center; gap: 4px;">
            <span style="display: inline-block; width: 5px; height: 5px; border-radius: 50%; background: #CBD5E1;"></span>
            {caption}
        </div>
        """

    badge_html = ""
    if badge:
        badge_html = f"""
        <span style="font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: {accent_color}; background: rgba(37, 99, 235, 0.08); border: 1px solid rgba(37, 99, 235, 0.15); padding: 2px 7px; border-radius: 4px;">
            {badge}
        </span>
        """

    help_tooltip = f'title="{help_text}"' if help_text else ""

    card_html = f"""
    <div {help_tooltip} style="
        position: relative;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px 20px 16px 20px;
        box-shadow: 0 1px 3px 0 rgba(15, 23, 42, 0.04), 0 4px 10px -2px rgba(15, 23, 42, 0.03);
        margin-bottom: 12px;
        overflow: hidden;
        transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
    ">
        <!-- Accent top stripe -->
        <div style="
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, {accent_color} 0%, {accent_light} 100%);
        "></div>

        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div style="
                font-size: 0.72rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.06em;
                color: #64748B;
            ">
                {label}
            </div>
            {badge_html}
        </div>

        <div style="
            font-size: 1.95rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            color: #0F172A;
            line-height: 1.15;
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
        ">
            {value}
        </div>

        {delta_html}
        {caption_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_kpi_row(metrics: List[Dict[str, Any]]) -> None:
    """Renders a responsive horizontal grid of KPI cards with coordinated palette styling."""
    cols = st.columns(len(metrics))
    for i, (col, m) in zip(range(len(metrics)), zip(cols, metrics)):
        accent_color, accent_light, _, default_badge = ACCENT_PALETTES[i % len(ACCENT_PALETTES)]
        with col:
            render_metric_card(
                label=m["label"],
                value=m["value"],
                delta=m.get("delta"),
                help_text=m.get("help"),
                accent_color=m.get("accent_color", accent_color),
                accent_light=m.get("accent_light", accent_light),
                badge=m.get("badge", default_badge),
                caption=m.get("caption"),
            )
