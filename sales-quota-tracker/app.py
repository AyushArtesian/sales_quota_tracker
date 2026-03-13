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
from utils.aggregator import aggregate_billing
from utils.quota_manager import init_quota_state, get_quotas
from utils.calculations import compute_achievement, overall_metrics

# ── Component imports ──────────────────────────────────────────────────
from components.dashboard import render_metrics, render_sidebar_filters, apply_filters
from components.charts import (
    billing_vs_quota_chart,
    salesperson_performance_chart,
    achievement_distribution_chart,
    monthly_trend_chart,
)
from components.quota_input import render_quota_editor
from components.tables import render_achievement_table, render_leaderboard, render_raw_data


# ── Page config ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sales Quota Tracker",
    page_icon="📊",
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
    help="Columns required: Client Name, Month, Billing Amount, Freelancer, Sales Person",
)

# ── Main flow ──────────────────────────────────────────────────────────
if uploaded_file is not None:
    # 1. Read & validate
    raw_df = read_excel(uploaded_file)

    if raw_df is not None:
        # Store raw data in session state
        st.session_state["raw_df"] = raw_df

        # 2. Aggregate billing
        billing_agg = aggregate_billing(raw_df)
        st.session_state["billing_agg"] = billing_agg

        # 3. Initialise quotas (only adds new keys; keeps existing values)
        init_quota_state(billing_agg)

        # 4. Sidebar filters (based on raw data for full scope)
        filters = render_sidebar_filters(raw_df)

        # ── Quota editor section ───────────────────────────────────────
        with st.expander("✏️ Quota Management", expanded=False):
            render_quota_editor()

        # 5. Compute achievement
        quotas = get_quotas()
        achievement_df = compute_achievement(billing_agg, quotas)

        # 6. Apply filters
        filtered_df = apply_filters(achievement_df, filters)

        # 7. Overall metrics
        metrics = overall_metrics(filtered_df)

        # ── Layout ─────────────────────────────────────────────────────
        st.markdown("---")

        # Top metrics row
        render_metrics(metrics)

        st.markdown("---")

        # Charts row 1: Billing vs Quota & Sales Person
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            billing_vs_quota_chart(filtered_df)
        with chart_col2:
            salesperson_performance_chart(filtered_df)

        # Charts row 2: Achievement distribution & Monthly trend
        chart_col3, chart_col4 = st.columns(2)
        with chart_col3:
            achievement_distribution_chart(filtered_df)
        with chart_col4:
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
        ### 👋 Welcome!

        To get started, **upload a billing Excel file** using the sidebar.

        The file should contain the following columns:

        | Column | Description |
        |--------|-------------|
        | **Client Name** | Name of the client |
        | **Month** | Billing month (e.g., Jan-2026) |
        | **Billing Amount** | Amount billed (numeric) |
        | **Freelancer** | Name of the freelancer |
        | **Sales Person** | Responsible sales person |

        Once uploaded you can:
        - 📝 Set quotas per client × month
        - 📊 View interactive dashboards
        - 🏅 Track leaderboards
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
        }
    )
    st.download_button(
        "⬇️ Download Sample Template",
        data=sample.to_csv(index=False).encode(),
        file_name="billing_template.csv",
        mime="text/csv",
    )
