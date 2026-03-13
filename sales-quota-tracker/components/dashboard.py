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
            label="💰 Total Billing",
            value=f"₹{metrics['total_billing']:,.2f}",
        )

    with c2:
        st.metric(
            label="🎯 Total Quota",
            value=f"₹{metrics['total_quota']:,.2f}",
        )

    with c3:
        overall = metrics["overall_achievement"]
        delta_color = "normal" if overall >= 100 else ("off" if overall >= 80 else "inverse")
        st.metric(
            label="📊 Overall Achievement",
            value=f"{overall:.1f}%",
            delta=f"{'On Track' if overall >= 80 else 'Behind Target'}",
            delta_color=delta_color,
        )


def render_sidebar_filters(df: pd.DataFrame) -> dict:
    """Render sidebar filter widgets and return selected values."""
    st.sidebar.header("🔎 Filters")

    months = sorted(df["Month"].unique())
    clients = sorted(df["Client Name"].unique())
    salespersons = sorted(df["Sales Person"].unique())

    selected_months = st.sidebar.multiselect("Month", months, default=months)
    selected_clients = st.sidebar.multiselect("Client", clients, default=clients)
    selected_salespersons = st.sidebar.multiselect("Sales Person", salespersons, default=salespersons)

    return {
        "months": selected_months,
        "clients": selected_clients,
        "salespersons": selected_salespersons,
    }


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Apply sidebar filter selections to the achievement dataframe."""
    mask = (
        df["Month"].isin(filters["months"])
        & df["Client Name"].isin(filters["clients"])
        & df["Sales Person"].isin(filters["salespersons"])
    )
    return df[mask].reset_index(drop=True)
