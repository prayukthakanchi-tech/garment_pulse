"""
GarmentPulse Dashboard — Container & Card Framing Components
Provides elegant card frames, headers, and visual grouping for Plotly charts and tables.
"""

from typing import Optional
import streamlit as st


def render_card_header(
    title: str,
    subtitle: Optional[str] = None,
    badge: Optional[str] = None,
    action_note: Optional[str] = None,
) -> None:
    """Renders a refined header bar above charts or analytical tables."""
    badge_html = ""
    if badge:
        badge_html = f"""
        <span style="font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #2563EB; background: #EFF6FF; border: 1px solid #DBEAFE; padding: 2px 8px; border-radius: 9999px;">
            {badge}
        </span>
        """

    action_html = ""
    if action_note:
        action_html = f"""
        <span style="font-size: 0.72rem; color: #94A3B8; font-weight: 500;">
            {action_note}
        </span>
        """

    sub_html = f'<p style="font-size: 0.82rem; color: #64748B; margin: 3px 0 0 0; line-height: 1.35;">{subtitle}</p>' if subtitle else ""

    header_html = f"""
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #F1F5F9;">
        <div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <h3 style="font-size: 1.05rem; font-weight: 700; color: #0F172A; margin: 0; letter-spacing: -0.01em;">
                    {title}
                </h3>
                {badge_html}
            </div>
            {sub_html}
        </div>
        {action_html}
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)
