from __future__ import annotations

import streamlit as st

PRIMARY = "#6366F1"
SECONDARY = "#8B5CF6"
SUCCESS = "#10B981"
WARNING = "#F59E0B"
DANGER = "#EF4444"
INFO = "#3B82F6"
DARK = "#0F172A"
GRAY = "#64748B"
LIGHT_GRAY = "#F1F5F9"
BORDER = "#E2E8F0"
BG = "#F8FAFC"
CARD_BG = "#FFFFFF"
SIDEBAR_BG = "#0F172A"
SIDEBAR_TEXT = "#CBD5E1"
SIDEBAR_HEADING = "#F1F5F9"

COLORS: dict[str, str] = {
    "billing": PRIMARY,
    "technical": SUCCESS,
    "shipping": WARNING,
    "account": INFO,
    "product": SECONDARY,
    "other": GRAY,
}


def inject_css() -> None:
    st.markdown(
        f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    * {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }}

    .main > div {{ background: {BG}; }}

    .block-container {{
        padding: 1.25rem 2rem 2rem !important;
        max-width: 1440px;
    }}

    .main-header {{
        margin-bottom: 1.25rem;
    }}

    .main-header h1 {{
        font-size: 1.65rem;
        font-weight: 700;
        color: {DARK};
        margin: 0;
        padding: 0;
        line-height: 1.3;
        letter-spacing: -0.02em;
    }}

    .main-header .subtitle {{
        font-size: 0.85rem;
        color: {GRAY};
        margin-top: 0.1rem;
        font-weight: 400;
    }}

    .header-meta {{
        display: flex;
        gap: 1.75rem;
        flex-wrap: wrap;
        margin-top: 0.6rem;
        padding: 0.75rem 0 0.5rem;
        border-top: 1px solid {BORDER};
    }}

    .header-meta .meta-item {{
        font-size: 0.78rem;
        color: {GRAY};
        white-space: nowrap;
        display: flex;
        align-items: center;
        gap: 0.35rem;
    }}

    .header-meta .meta-item strong {{
        color: {DARK};
        font-weight: 600;
    }}

    .header-meta .meta-dot {{
        display: inline-block;
        width: 5px;
        height: 5px;
        border-radius: 50%;
        background: {BORDER};
        margin: 0 0.1rem;
    }}

    .kpi-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
        gap: 0.85rem;
        margin-bottom: 1.5rem;
    }}

    .kpi-card {{
        background: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 0.65rem;
        padding: 1rem 1.1rem;
        transition: box-shadow 0.15s ease, border-color 0.15s ease;
        height: 100%;
    }}

    .kpi-card:hover {{
        border-color: {PRIMARY}40;
        box-shadow: 0 4px 16px rgba(99,102,241,0.08);
    }}

    .kpi-card .kpi-top {{
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        margin-bottom: 0.4rem;
    }}

    .kpi-card .kpi-icon {{
        font-size: 1.3rem;
        line-height: 1;
        opacity: 0.85;
    }}

    .kpi-card .kpi-value {{
        font-size: 1.6rem;
        font-weight: 700;
        color: {DARK};
        line-height: 1.15;
        letter-spacing: -0.01em;
    }}

    .kpi-card .kpi-label {{
        font-size: 0.7rem;
        color: {GRAY};
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
        margin-bottom: 0.2rem;
    }}

    .kpi-card .kpi-desc {{
        font-size: 0.72rem;
        color: {GRAY};
        line-height: 1.35;
        margin-top: 0.1rem;
    }}

    .kpi-card .kpi-footer {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-top: 0.4rem;
        padding-top: 0.4rem;
        border-top: 1px solid {LIGHT_GRAY};
    }}

    .kpi-card .kpi-delta {{
        font-size: 0.72rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 0.2rem;
    }}

    .kpi-card .kpi-delta.positive {{ color: {SUCCESS}; }}
    .kpi-card .kpi-delta.negative {{ color: {DANGER}; }}
    .kpi-card .kpi-delta.neutral {{ color: {GRAY}; }}

    section[data-testid="stSidebar"] {{
        background: {SIDEBAR_BG};
    }}

    section[data-testid="stSidebar"] * {{
        color: {SIDEBAR_TEXT} !important;
    }}

    section[data-testid="stSidebar"] .stSidebarContent {{
        padding: 1.25rem 1rem;
    }}

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4 {{
        color: {SIDEBAR_HEADING} !important;
        font-weight: 600;
        letter-spacing: -0.01em;
    }}

    section[data-testid="stSidebar"] label {{
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.04em !important;
        color: {GRAY} !important;
        margin-top: 0.4rem;
    }}

    section[data-testid="stSidebar"] hr {{
        margin: 0.75rem 0;
        border-color: rgba(255,255,255,0.08);
    }}

    section[data-testid="stSidebar"] .stSelectbox,
    section[data-testid="stSidebar"] .stMultiSelect,
    section[data-testid="stSidebar"] .stSlider,
    section[data-testid="stSidebar"] .stTextInput,
    section[data-testid="stSidebar"] .stDateInput {{
        margin-bottom: 0.35rem;
    }}

    section[data-testid="stSidebar"] .stSelectbox > div > div,
    section[data-testid="stSidebar"] .stMultiSelect > div > div,
    section[data-testid="stSidebar"] .stTextInput > div > div > input {{
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 0.45rem !important;
        color: {SIDEBAR_HEADING} !important;
        font-size: 0.82rem !important;
    }}

    section[data-testid="stSidebar"] .stSlider > div > div {{
        color: {SIDEBAR_HEADING} !important;
    }}

    section[data-testid="stSidebar"] div.stButton > button {{
        background: {PRIMARY} !important;
        color: white !important;
        border: none !important;
        border-radius: 0.5rem !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        padding: 0.4rem 1rem !important;
        transition: opacity 0.15s ease;
    }}

    section[data-testid="stSidebar"] div.stButton > button:hover {{
        opacity: 0.9;
    }}

    section[data-testid="stSidebar"] .stCheckbox {{
        margin-top: 0.25rem;
    }}

    section[data-testid="stSidebar"] .stCheckbox label {{
        font-size: 0.8rem !important;
        text-transform: none !important;
        letter-spacing: 0 !important;
    }}

    .stPlotlyChart {{
        background: transparent;
    }}

    div[data-testid="stDataFrameContainer"] > div {{
        border: 1px solid {BORDER};
        border-radius: 0.65rem;
        overflow: hidden;
    }}

    div[data-testid="stDataFrameContainer"] th {{
        background: {LIGHT_GRAY};
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: {GRAY};
        padding: 0.55rem 0.75rem;
    }}

    div[data-testid="stDataFrameContainer"] td {{
        font-size: 0.82rem;
        padding: 0.4rem 0.75rem;
    }}

    div.stMarkdown h2,
    div.stMarkdown h3 {{
        font-weight: 600;
        color: {DARK};
        letter-spacing: -0.01em;
        margin-top: 0;
    }}

    div.stMarkdown h3 {{
        font-size: 1.1rem;
    }}

    div.stAlert {{
        border-radius: 0.5rem;
        border: none;
    }}

    div.stAlert > div {{
        font-size: 0.85rem;
    }}

    .exec-summary {{
        display: flex;
        flex-wrap: wrap;
        gap: 0;
        background: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 0.65rem;
        padding: 0.6rem 0;
        margin-bottom: 1.25rem;
    }}

    .exec-summary .exec-item {{
        flex: 1 0 0;
        min-width: 110px;
        padding: 0.3rem 1rem;
        text-align: center;
        border-right: 1px solid {LIGHT_GRAY};
    }}

    .exec-summary .exec-item:last-child {{
        border-right: none;
    }}

    .exec-summary .exec-label {{
        font-size: 0.62rem;
        color: {GRAY};
        text-transform: uppercase;
        letter-spacing: 0.04em;
        font-weight: 600;
        margin-bottom: 0.15rem;
    }}

    .exec-summary .exec-value {{
        font-size: 1rem;
        font-weight: 700;
        color: {DARK};
        line-height: 1.3;
    }}

    .insight-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.75rem;
        margin-bottom: 1.25rem;
    }}

    .insight-card {{
        background: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 0.55rem;
        padding: 0.7rem 0.9rem;
    }}

    .insight-card .insight-label {{
        font-size: 0.62rem;
        color: {GRAY};
        text-transform: uppercase;
        letter-spacing: 0.04em;
        font-weight: 600;
        margin-bottom: 0.15rem;
    }}

    .insight-card .insight-value {{
        font-size: 0.85rem;
        font-weight: 600;
        color: {DARK};
        word-break: break-all;
    }}

    .insight-card .insight-detail {{
        font-size: 0.72rem;
        color: {GRAY};
        margin-top: 0.1rem;
    }}

    @media (max-width: 768px) {{
        .block-container {{ padding: 1rem !important; }}
        .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
        .insight-grid {{ grid-template-columns: repeat(2, 1fr); }}
        .header-meta {{ gap: 0.75rem; }}
    }}
</style>
""",
        unsafe_allow_html=True,
    )
