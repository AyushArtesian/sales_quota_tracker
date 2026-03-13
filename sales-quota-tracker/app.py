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
from utils.quota_manager import init_quota_state, get_quotas, update_quotas
from utils.client_manager import init_client_state
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
from components.client_master import render_client_master
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
    "Upload Billing File (Excel or CSV)",
    type=["xlsx", "xls", "csv"],
    help="Required columns: Date, Type, Description, Sales Person, Team, Amount (Team is treated as Client)",
)

# ── Main flow ──────────────────────────────────────────────────────────
if uploaded_file is not None:

    # Reset stage when a new file is uploaded
    if st.session_state.get("raw_file_name") != uploaded_file.name:
        st.session_state["stage"] = "quota"
        st.session_state["raw_file_name"] = uploaded_file.name

    # 1. Read & validate
    raw_df, file_type = read_excel(uploaded_file)

    if file_type == "error":
        st.stop()

    # If file is a quota-export table, load it as quotas and keep existing billing data
    if file_type == "quota" and raw_df is not None:
        update_quotas(raw_df)
        st.success("Loaded quotas from uploaded file.")
        raw_df = st.session_state.get("raw_df", pd.DataFrame())

    # If file is billing data, merge with existing data and de-duplicate
    if file_type == "billing" and raw_df is not None:
        existing_df = st.session_state.get("raw_df")
        if isinstance(existing_df, pd.DataFrame) and not existing_df.empty:
            merged = pd.concat([existing_df, raw_df], ignore_index=True)
            dup_subset = [
                "Client Name",
                "Month",
                "Billing Amount",
                "Sales Person",
                "Sales Team",
                "Type",
                "Date",
            ]
            before = len(merged)
            merged = merged.drop_duplicates(subset=dup_subset, keep="last").reset_index(drop=True)
            duplicates = before - len(merged)
            st.session_state["raw_df"] = merged
            raw_df = merged

            if duplicates > 0:
                st.info(f"Skipped {duplicates} duplicate row(s) while merging the new upload.")
        else:
            st.session_state["raw_df"] = raw_df

    # 2. Initialise quotas from available billing data
    if isinstance(raw_df, pd.DataFrame) and not raw_df.empty:
        init_quota_state(raw_df)
        init_client_state(raw_df)

    # 3. Stage flow: quota setup → dashboard
    stage = st.session_state.get("stage", "quota")

    if stage == "quota":
        if isinstance(raw_df, pd.DataFrame) and not raw_df.empty:
            st.info("Please define your target quotas before viewing the dashboard.")
            tab_targets, tab_clients = st.tabs(["Target Setup", "Client Master"])

            with tab_targets:
                render_quota_editor(raw_df)

            with tab_clients:
                render_client_master()

            if st.button("Proceed to Dashboard"):
                st.session_state["stage"] = "dashboard"
                if hasattr(st, "experimental_rerun"):
                    st.experimental_rerun()
        else:
            st.info("No billing data available yet. Upload a billing file to define targets and view dashboard.")
    else:
        if isinstance(raw_df, pd.DataFrame) and not raw_df.empty:
            quotas = get_quotas()
            achievement_df = compute_achievement(raw_df, quotas)
            filters = render_sidebar_filters(achievement_df)
            filtered_df = apply_filters(achievement_df, filters)
            metrics = overall_metrics(filtered_df)

            st.markdown("---")
            render_metrics(metrics)

            st.markdown("---")
            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                salesperson_quota_chart(filtered_df)
            with chart_col2:
                salesperson_achievement_chart(filtered_df)

            st.markdown("---")
            chart_col3, chart_col4 = st.columns(2)
            with chart_col3:
                achievement_status_chart(filtered_df)
            with chart_col4:
                monthly_trend_chart(filtered_df)

            st.markdown("---")
            render_achievement_table(filtered_df)
            st.markdown("---")
            render_leaderboard(filtered_df)
            render_raw_data(raw_df)
        else:
            st.info("No billing data available yet. Upload a billing file to view dashboards.")

else:
    # Landing state – no file uploaded yet
    st.markdown(
        """
        ### Welcome!

        To get started, **upload a billing Excel file** using the sidebar.

        The file should contain the following columns:

        | Column | Description |
        |--------|-------------|
        | **Date** | Date of billing (e.g., Feb 27, 2026) |
        | **Type** | Type of work (e.g., Hourly, Fixed, etc.) |
        | **Description** | Work description |
        | **Sales Person** | Name of the sales person (e.g., Hardik/Paras) |
        | **Team** | Client / account name |
        | **Amount** | Billing amount (numeric) |

        The system tracks target achievement for **Sales Persons** or **Sales Teams**
        over multi-month windows.

        Once uploaded you can:
        - Set target quotas for sales persons or sales teams
        - Add/edit client master details
        - View interactive dashboards
        - Track performance & leaderboards
        """
    )

    # Show a sample template download
    sample = pd.DataFrame(
        {
            "Date": ["Feb 27, 2026", "Feb 27, 2026", "Feb 28, 2026", "Feb 28, 2026"],
            "Type": ["Hourly", "Hourly", "Fixed", "Hourly"],
            "Description": ["Design Work", "Design Work", "Development", "QA Testing"],
            "Sales Person": ["Hardik", "Paras", "Hardik", "Paras"],
            "Team": ["Joshua M", "Joshua M", "Andrea Barbieri", "Andrea Barbieri"],
            "Amount": [195.835, 56.25, 112.5, 89.75],
        }
    )
    st.download_button(
        "Download Sample Template",
        data=sample.to_csv(index=False).encode(),
        file_name="billing_template.csv",
        mime="text/csv",
    )
