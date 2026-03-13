"""
dashboard.py
------------
Top-level KPI metric cards and sidebar filters.
"""

import streamlit as st
import pandas as pd


def render_metrics(metrics: dict):
    """Display three headline KPI cards at the top of the page."""
    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            label="Total Billing",
            value=f"₹{metrics['total_billing']:,.2f}",
        )

    with c2:
        st.metric(
            label="Total Quota",
            value=f"₹{metrics['total_quota']:,.2f}",
        )

    with c3:
        overall = metrics["overall_achievement"]
        delta_color = "normal" if overall >= 100 else ("off" if overall >= 80 else "inverse")
        st.metric(
            label="Overall Achievement",
            value=f"{overall:.1f}%",
            delta=f"{'On Track' if overall >= 80 else 'Behind Target'}",
            delta_color=delta_color,
        )


def render_sidebar_filters(df: pd.DataFrame) -> dict:
    """Render sidebar filter widgets and return selected values."""
    st.sidebar.header("Filters")

    # Chronological month sorting (for Start Month in target table)
    months_list = list(df["Start Month"].dropna().astype(str).unique()) if "Start Month" in df.columns else []
    try:
        month_order = (
            pd.to_datetime(months_list, format="%b-%Y", errors="coerce")
            .sort_values()
            .reset_index(drop=True)
        )
        months = [m for _, m in sorted(zip(month_order, months_list)) if pd.notna(_)]
    except Exception:
        months = sorted(months_list)

    entity_types = sorted(df["Entity Type"].dropna().astype(str).unique()) if "Entity Type" in df.columns else []
    entity_names = sorted(df["Entity Name"].dropna().astype(str).unique()) if "Entity Name" in df.columns else []
    statuses = sorted(df["Status"].dropna().astype(str).unique()) if "Status" in df.columns else []

    selected_months = st.sidebar.multiselect("Start Month", months, default=months)
    selected_entity_types = st.sidebar.multiselect("Target Type", entity_types, default=entity_types)
    selected_entity_names = st.sidebar.multiselect("Target Name", entity_names, default=entity_names)
    selected_statuses = st.sidebar.multiselect("Status", statuses, default=statuses)

    return {
        "months": selected_months,
        "entity_types": selected_entity_types,
        "entity_names": selected_entity_names,
        "statuses": selected_statuses,
    }


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Apply sidebar filter selections to the achievement dataframe."""
    mask = (
        df["Start Month"].isin(filters["months"])
        & df["Entity Type"].isin(filters["entity_types"])
        & df["Entity Name"].isin(filters["entity_names"])
        & df["Status"].isin(filters["statuses"])
    )
    return df[mask].reset_index(drop=True)
