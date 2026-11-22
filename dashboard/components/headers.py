"""
GarmentPulse Dashboard — Executive Page Header Component
Renders a world-class, Fortune 500 SaaS hero banner with breadcrumbs,
status indicators, and analytical metadata badges.
"""

from typing import List, Optional, Tuple
import streamlit as st


def render_page_header(
    title: str,
    subtitle: str,
    breadcrumb: str = "EXECUTIVE INTELLIGENCE",
    badges: Optional[List[Tuple[str, str]]] = None,
) -> None:
    """Renders a sleek executive page hero header with breadcrumbs and audit pills."""
    badge_colors = {
        "blue": ("#EFF6FF", "#1D4ED8", "#DBEAFE"),
        "green": ("#ECFDF5", "#047857", "#A7F3D0"),
        "violet": ("#F5F3FF", "#6D28D9", "#DDD6FE"),
        "amber": ("#FFFBEB", "#B45309", "#FDE68A"),
        "slate": ("#F8FAFC", "#475569", "#E2E8F0"),
    }

    if badges is None:
        badges = [
            ("31.8M Lines Audited", "blue"),
            ("DuckDB OLAP", "green"),
            ("Zero Synthetic Data", "slate"),
        ]

    badge_html_items = []
    for text, btype in badges:
        bg, text_color, border = badge_colors.get(btype, badge_colors["slate"])
        badge_html_items.append(
            f'<span style="display:inline-flex;align-items:center;background:{bg};color:{text_color};'
            f'border:1px solid {border};font-size:0.72rem;font-weight:600;'
            f'padding:3px 10px;border-radius:9999px;letter-spacing:0.03em;white-space:nowrap;">'
            f'{text}</span>'
        )
    badges_rendered = "".join(badge_html_items)

    header_html = (
        f'<div style="margin-bottom:24px;padding-bottom:18px;border-bottom:1px solid #E2E8F0;">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">'
        f'<div>'
        f'<div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#2563EB;margin-bottom:4px;">'
        f'GARMENTPULSE / {breadcrumb}</div>'
        f'<h1 style="font-size:1.85rem;font-weight:800;letter-spacing:-0.03em;color:#0F172A;margin:0 0 6px 0;line-height:1.2;">'
        f'{title}</h1>'
        f'<p style="font-size:0.92rem;color:#64748B;margin:0;line-height:1.45;max-width:820px;">'
        f'{subtitle}</p>'
        f'</div>'
        f'<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding-top:6px;">'
        f'{badges_rendered}</div>'
        f'</div></div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)
