"""
Sales Quota Tracker – Streamlit Application
============================================
Upload billing Excel data, set quotas manually, and track quota achievement
with interactive dashboards, charts, tables, and leaderboards.

Run:  streamlit run app.py
"""

import os
import sys

# Ensure the local package folders are on the import path (useful on some deployment platforms)
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd

# ── Utility imports ────────────────────────────────────────────────────
from utils.excel_reader import read_excel
from utils.quota_manager import init_quota_state, get_quotas
from utils.calculations import compute_achievement, overall_metrics

# ── Component imports ──────────────────────────────────────────────────
from components.dashboard import render_metrics, render_sidebar_filters, apply_filters
from components.charts import (
    salesperson_quota_chart,
    achievement_status_chart,
    monthly_trend_chart,
    salesperson_achievement_chart,
)
from components.quota_input import render_quota_editor
from components.tables import render_achievement_table, render_leaderboard, render_raw_data


# ── Page config ────────────────────────────────────────────────────────
# Use a local favicon (base64 embedded) to customize the Streamlit tab icon
ICON_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAAgElEQVR4nOXOQQEAIBCAMCSISQxme41x"
    "D5Zga5/7CJM4iZM4iZM4iZM4iZM4iZM4iZM4iZM4iZM4iZM4iZM4iZM4iZM4iZM4iZM4iZM4iZM4iZM4"
    "iZM4iZM4iZM4iZM4iZM4iZM4iZM4iZM4iZM4iZM4iZM4iZM4iZM4iZM4iZM4iZM4iZM4iXM6MO0DBlECUa"
    "B2VeIAAAAASUVORK5CYII="
)

st.set_page_config(
    page_title="Sales Quota Tracker",
    page_icon=f"data:image/png;base64,{ICON_BASE64}",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for polish
st.markdown(
    """
    <style>
    /* Card-style metrics */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem 1.2rem;
        border-radius: 0.75rem;
        color: white !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    }
    [data-testid="stMetric"] label,
    [data-testid="stMetric"] [data-testid="stMetricValue"],
    [data-testid="stMetric"] [data-testid="stMetricDelta"] {
        color: white !important;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fc !important;
        color: #0b1a2a !important;
    }
    section[data-testid="stSidebar"] *,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown {
        color: #0b1a2a !important;
    }

    /* Sidebar widgets: enforce light backgrounds so text is readable */
    section[data-testid="stSidebar"] .stFileUploader,
    section[data-testid="stSidebar"] .stSelectbox,
    section[data-testid="stSidebar"] .stMultiSelect,
    section[data-testid="stSidebar"] .stTextInput,
    section[data-testid="stSidebar"] .stMultiSelect > div {
        background: rgba(255,255,255,0.95) !important;
        border-radius: 0.55rem !important;
        border: 1px solid rgba(0,0,0,0.12) !important;
    }

    /* Sidebar multiselect tag styling */
    section[data-testid="stSidebar"] .stMultiSelect button {
        background: rgba(255,255,255,0.95) !important;
    }

    /* Force the upload box to be light for readability */
    section[data-testid="stSidebar"] .stFileUploader > div {
        background: rgba(255,255,255,0.95) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ─────────────────────────────────────────────────────────────
st.title("Sales Quota Tracker")
st.caption("Upload billing data · Set quotas · Track achievement in real time")

# ── Sidebar: File upload ───────────────────────────────────────────────
st.sidebar.title("Upload Data")
uploaded_file = st.sidebar.file_uploader(
    "Upload Billing Excel",
    type=["xlsx", "xls"],
    help="Required: Client Name, Month, Billing Amount, Freelancer, Sales Person. Optional: Client Onboarding Date, Sales Team",
)

# ── Main flow ──────────────────────────────────────────────────────────
if uploaded_file is not None:
    # 1. Read & validate
    raw_df = read_excel(uploaded_file)

    if raw_df is not None:
        # Store raw data in session state
        st.session_state["raw_df"] = raw_df

        # 2. Initialise target quotas
        init_quota_state(raw_df)

        # ── Quota editor section ───────────────────────────────────────
        with st.expander("Quota Management", expanded=False):
            render_quota_editor(raw_df)

        # 3. Compute achievement for target windows
        quotas = get_quotas()
        achievement_df = compute_achievement(raw_df, quotas)

        # 4. Sidebar filters (target-level)
        filters = render_sidebar_filters(achievement_df)

        # 5. Apply filters
        filtered_df = apply_filters(achievement_df, filters)

        # 6. Overall metrics
        metrics = overall_metrics(filtered_df)

        # ── Layout ─────────────────────────────────────────────────────
        st.markdown("---")

        # Top metrics row
        render_metrics(metrics)

        st.markdown("---")

        # Charts row 1: Sales Person Quota & Achievement %
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            salesperson_quota_chart(filtered_df)
        with chart_col2:
            salesperson_achievement_chart(filtered_df)

        # Charts row 2: Achievement distribution & Monthly trend
        chart_col3, chart_col4 = st.columns(2)
        with chart_col3:
            achievement_status_chart(filtered_df)
        with chart_col4:
            # Use the computed achievement dataset (includes Total Billing and Quota)
            monthly_trend_chart(filtered_df)

        st.markdown("---")

        # Achievement table
        render_achievement_table(filtered_df)

        st.markdown("---")

        # Leaderboard
        render_leaderboard(filtered_df)

        # Raw data expandable
        render_raw_data(raw_df)

else:
    # Landing state – no file uploaded yet
    st.markdown(
        """
        ### Welcome!

        To get started, **upload a billing Excel file** using the sidebar.

        The file should contain the following columns:

        | Column | Description |
        |--------|-------------|
        | **Client Name** | Name of the client |
        | **Month** | Billing month (e.g., Jan-2026) |
        | **Billing Amount** | Amount billed (numeric) |
        | **Freelancer** | Name of the freelancer |
        | **Sales Person** | Responsible sales person |
        | **Client Onboarding Date** | (Optional) Client start date |
        | **Sales Team** | (Optional) Team name |

        The system tracks target achievement for **Sales Rep** or **Sales Team**
        over multi-month windows.

        Once uploaded you can:
        - Set target quotas for sales reps or sales teams
        - View interactive dashboards
        - Track sales person performance & leaderboards
        """
    )

    # Show a sample template download
    sample = pd.DataFrame(
        {
            "Client Name": ["Acme Corp", "Acme Corp", "BetaTech", "BetaTech"],
            "Month": ["Jan-2026", "Feb-2026", "Jan-2026", "Feb-2026"],
            "Billing Amount": [50000, 62000, 45000, 38000],
            "Freelancer": ["Alice", "Alice", "Bob", "Bob"],
            "Sales Person": ["Rahul", "Rahul", "Priya", "Priya"],
            "Client Onboarding Date": ["2025-12-15", "2025-12-15", "2026-01-10", "2026-01-10"],
            "Sales Team": ["Team A", "Team A", "Team B", "Team B"],
        }
    )
    st.download_button(
        "Download Sample Template",
        data=sample.to_csv(index=False).encode(),
        file_name="billing_template.csv",
        mime="text/csv",
    )
