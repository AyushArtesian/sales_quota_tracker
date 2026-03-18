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
from utils.client_manager import (
    init_client_state,
    apply_client_master_to_raw,
    detect_new_clients,
    detect_clients_missing_acquisition,
    update_clients,
)
from utils.billing_manager import (
    save_billing_data,
    load_billing_data,
    clear_billing_data,
    delete_billing_data_by_month,
)
from utils.calculations import compute_achievement, overall_metrics
from utils.derived_manager import update_derived_tables

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
from components.chatbot import render_chatbot
from components.maintenance import render_danger_zone, render_client_acquisition_modal


# ── Stage persistence (UI navigation state) ────────────────────────────
from utils.stage_cache import load_stage_cache, save_stage_cache

# ── Azure AD Authentication ────────────────────────────────────────────
from auth_manager import check_authentication, show_logout_button

# ✅ AUTHENTICATION CHECK - User must be logged in to access the app
if not check_authentication():
    st.stop()


# ── Page config ────────────────────────────────────────────────────────
# Initialize tab tracking (for Target Setup vs Client Master navigation)
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = 0  # 0 = Target Setup, 1 = Client Master

# Initialize theme preference
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"  # Default theme: light

if "theme_changed" not in st.session_state:
    st.session_state["theme_changed"] = 0  # Counter to force CSS re-render

def toggle_theme():
    """Toggle between light and dark theme"""
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
    st.session_state.theme_changed += 1  # Force CSS refresh

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

# Custom CSS for polish (theme-aware)
theme = st.session_state.get("theme", "light")
theme_counter = st.session_state.get("theme_changed", 0)

if theme == "dark":
    # Dark theme
    st.markdown(
        f"""
        <style>
        /* Dark Theme | Counter: {theme_counter} */
        :root {{
            --primary-bg: #0e1117;
            --secondary-bg: #161b22;
            --text-color: #e6edf3;
            --border-color: #30363d;
        }}
        
        body {{
            background-color: #0e1117 !important;
            color: #e6edf3 !important;
        }}
        
        /* Main content area dark theme */
        .main {{
            background-color: #0e1117 !important;
        }}
        
        /* Card-style metrics - dark */
        [data-testid="stMetric"] {{
            background: #161b22 !important;
            padding: 1rem 1.2rem;
            border-radius: 0.5rem;
            border: 1px solid #30363d !important;
            color: #e6edf3 !important;
        }}
        [data-testid="stMetric"] label,
        [data-testid="stMetric"] [data-testid="stMetricValue"],
        [data-testid="stMetric"] [data-testid="stMetricDelta"] {{
            color: #e6edf3 !important;
        }}

        /* Sidebar dark theme */
        section[data-testid="stSidebar"] {{
            background-color: #161b22 !important;
            color: #e6edf3 !important;
        }}
        section[data-testid="stSidebar"] *,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stMarkdown {{
            color: #e6edf3 !important;
        }}

        /* Sidebar widgets dark theme */
        section[data-testid="stSidebar"] .stFileUploader,
        section[data-testid="stSidebar"] .stSelectbox,
        section[data-testid="stSidebar"] .stMultiSelect,
        section[data-testid="stSidebar"] .stTextInput,
        section[data-testid="stSidebar"] .stMultiSelect > div {{
            background: #0e1117 !important;
            border-radius: 0.55rem !important;
            border: 1px solid #30363d !important;
        }}

        section[data-testid="stSidebar"] .stMultiSelect button {{
            background: #0e1117 !important;
        }}

        section[data-testid="stSidebar"] .stFileUploader > div {{
            background: #0e1117 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    # Light theme (default)
    st.markdown(
        f"""
        <style>
        /* Light Theme | Counter: {theme_counter} */
        :root {{
            --primary-bg: #ffffff;
            --secondary-bg: #f8f9fa;
            --text-color: #0b1a2a;
            --border-color: #e0e0e0;
        }}
        
        /* Card-style metrics - light */
        [data-testid="stMetric"] {{
            background: #f8f9fa;
            padding: 1rem 1.2rem;
            border-radius: 0.5rem;
            border: 1px solid #e0e0e0;
            color: #333 !important;
        }}
        [data-testid="stMetric"] label,
        [data-testid="stMetric"] [data-testid="stMetricValue"],
        [data-testid="stMetric"] [data-testid="stMetricDelta"] {{
            color: #333 !important;
        }}

        /* Sidebar light theme */
        section[data-testid="stSidebar"] {{
            background-color: #f8f9fc !important;
            color: #0b1a2a !important;
        }}
        section[data-testid="stSidebar"] *,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stMarkdown {{
            color: #0b1a2a !important;
        }}

        /* Sidebar widgets light theme */
        section[data-testid="stSidebar"] .stFileUploader,
        section[data-testid="stSidebar"] .stSelectbox,
        section[data-testid="stSidebar"] .stMultiSelect,
        section[data-testid="stSidebar"] .stTextInput,
        section[data-testid="stSidebar"] .stMultiSelect > div {{
            background: rgba(255,255,255,0.95) !important;
            border-radius: 0.55rem !important;
            border: 1px solid rgba(0,0,0,0.12) !important;
        }}

        section[data-testid="stSidebar"] .stMultiSelect button {{
            background: rgba(255,255,255,0.95) !important;
        }}

        section[data-testid="stSidebar"] .stFileUploader > div {{
            background: rgba(255,255,255,0.95) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# ── Header ─────────────────────────────────────────────────────────────
st.title("Sales Quota Tracker")
st.caption("Upload billing data · Set quotas · Track achievement in real time")

# ── Show user info and logout button in sidebar ─────────────────────────
show_logout_button()

# ── Theme toggle button ────────────────────────────────────────────────
st.sidebar.markdown("---")
theme_icon = "🌙" if st.session_state.theme == "light" else "☀️"
theme_label = "Dark Mode" if st.session_state.theme == "light" else "Light Mode"
if st.sidebar.button(f"{theme_icon} {theme_label}", use_container_width=True):
    toggle_theme()
    st.rerun()

# ── Sidebar: File upload ───────────────────────────────────────────────
st.sidebar.title("Upload Data")
uploaded_file = st.sidebar.file_uploader(
    "Upload Billing File (Excel or CSV)",
    type=["xlsx", "xls", "csv"],
    help="Required columns: Date, Type, Description, Sales Person, Team, Amount (Team is treated as Client)",
)

# INITIALIZATION: Load from database if session state is empty
if "raw_df" not in st.session_state:
    loaded_df = load_billing_data()
    if not loaded_df.empty:
        st.session_state["raw_df"] = loaded_df
        st.session_state["stage"] = load_stage_cache()
        # Reinitialize quotas and clients from their database sources
        init_quota_state(loaded_df)
        init_client_state(loaded_df)
        st.sidebar.success("✓ Loaded data from database")

        # Ensure derived tables are populated based on the latest billing + quotas.
        try:
            from utils.quota_manager import load_quotas

            quotas_df = load_quotas()
            update_derived_tables(loaded_df, quotas_df)
        except Exception:
            pass

# Get raw_df and stage from session state
raw_df = st.session_state.get("raw_df", pd.DataFrame())

# Sidebar maintenance / delete options
render_danger_zone(raw_df)

stage = st.session_state.get("stage", "quota")

# PROCESS FILE UPLOAD if present
if uploaded_file is not None:

    # Reset stage and clear cache when a new file is uploaded
    if st.session_state.get("raw_file_name") != uploaded_file.name:
        st.session_state["stage"] = "quota"
        st.session_state["raw_file_name"] = uploaded_file.name
        clear_billing_data()
        save_stage_cache("quota")

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

    # 2. Initialize quotas and clients from billing data
    if isinstance(raw_df, pd.DataFrame) and not raw_df.empty:
        init_quota_state(raw_df)
        init_client_state(raw_df)
        
        # Detect new clients and/or clients missing acquisition dates; show modal to collect dates
        new_clients = detect_new_clients(raw_df)
        missing_acq_clients = detect_clients_missing_acquisition(raw_df)

        if new_clients:
            st.session_state["show_new_client_modal"] = True
            st.session_state["new_clients"] = new_clients
        elif missing_acq_clients:
            st.session_state["show_new_client_modal"] = True
            st.session_state["new_clients"] = missing_acq_clients

        raw_df = apply_client_master_to_raw(raw_df)
        st.session_state["raw_df"] = raw_df
        save_billing_data(raw_df)  # Persist to database for next refresh

# After file upload processing, refresh raw_df and stage from session state
raw_df = st.session_state.get("raw_df", pd.DataFrame())
stage = st.session_state.get("stage", "quota")

# 3. RENDER: Display quota setup or dashboard
if isinstance(raw_df, pd.DataFrame) and not raw_df.empty:

    if stage == "quota":
        st.info("Please define your target quotas before viewing the dashboard.")
        
        # Use radio buttons for section selection
        active_tab = st.session_state.get("active_tab", 0)
        selected_section = st.radio(
            "Choose section to edit:",
            ["Target Setup", "Client Master"],
            index=active_tab,
            horizontal=True,
            label_visibility="collapsed"
        )
        
        # Update session state based on selection
        if "Target Setup" in selected_section:
            st.session_state["active_tab"] = 0
            render_quota_editor(raw_df)
        else:
            st.session_state["active_tab"] = 1
            render_client_master()

        st.markdown("---")
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("Back to Dashboard", key="btn_back_to_dashboard", use_container_width=True):
                st.session_state["stage"] = "dashboard"
                save_stage_cache("dashboard")
                st.rerun()
        with btn_col2:
            if st.button("Save & View Dashboard", key="btn_proceed_dashboard", use_container_width=True):
                st.session_state["stage"] = "dashboard"
                save_stage_cache("dashboard")
                st.rerun()
    else:
        quotas = get_quotas()
        achievement_df = compute_achievement(raw_df, quotas)
        filters = render_sidebar_filters(achievement_df)
        filtered_df = apply_filters(achievement_df, filters)
        metrics = overall_metrics(filtered_df)

        # Navigation actions
        st.markdown("---")
        nav_col1, nav_col2 = st.columns(2, gap="medium")
        with nav_col1:
            if st.button("Edit Target Setup", key="btn_target_setup", use_container_width=True):
                st.session_state["active_tab"] = 0
                st.session_state["stage"] = "quota"
                save_stage_cache("quota")
                st.rerun()

        with nav_col2:
            if st.button("Edit Client Master", key="btn_client_master", use_container_width=True):
                st.session_state["active_tab"] = 1
                st.session_state["stage"] = "quota"
                save_stage_cache("quota")
                st.rerun()

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
        st.markdown("---")
        render_chatbot()
        render_raw_data(raw_df)
else:
    # No billing data available - show landing page
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

# ── Modal dialog for new clients ─────────────────────────────────────
if st.session_state.get("show_new_client_modal"):
    render_client_acquisition_modal(raw_df, st.session_state.get("new_clients", []))
