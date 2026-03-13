"""
tables.py
---------
Achievement table and leaderboard displays.
"""

import streamlit as st
import pandas as pd


def render_achievement_table(df: pd.DataFrame):
    """Show the detailed achievement table with colour-coded status."""
    st.subheader("📋 Quota Achievement Details")

    if df.empty:
        st.info("No data to display.")
        return

    display_cols = ["Client Name", "Month", "Sales Person", "Quota", "Total Billing", "Achievement %", "Status"]
    display = df[[c for c in display_cols if c in df.columns]].copy()

    # Colour styling
    def _highlight_status(row):
        if "Achieved" in str(row.get("Status", "")) and "Almost" not in str(row.get("Status", "")):
            return ["background-color: #d4edda"] * len(row)
        elif "Almost" in str(row.get("Status", "")):
            return ["background-color: #fff3cd"] * len(row)
        else:
            return ["background-color: #f8d7da"] * len(row)

    styled = display.style.apply(_highlight_status, axis=1).format(
        {"Quota": "₹{:,.2f}", "Total Billing": "₹{:,.2f}", "Achievement %": "{:.1f}%"}
    )

    st.dataframe(styled, use_container_width=True, height=min(600, 40 * len(display) + 60))


def render_leaderboard(df: pd.DataFrame):
    """Show top-performing clients and sales persons by billing."""
    st.subheader("🏅 Leaderboard")

    if df.empty:
        st.info("No data to display.")
        return

    col_client, col_sp = st.columns(2)

    with col_client:
        st.markdown("**Top Clients by Billing**")
        client_lb = (
            df.groupby("Client Name", as_index=False)
            .agg({"Total Billing": "sum", "Achievement %": "mean"})
            .sort_values("Total Billing", ascending=False)
            .head(10)
        )
        client_lb.index = range(1, len(client_lb) + 1)
        client_lb.index.name = "Rank"

        st.dataframe(
            client_lb.style.format({"Total Billing": "₹{:,.2f}", "Achievement %": "{:.1f}%"}),
            use_container_width=True,
        )

    with col_sp:
        st.markdown("**Top Sales Persons by Billing**")
        sp_lb = (
            df.groupby("Sales Person", as_index=False)
            .agg({"Total Billing": "sum", "Achievement %": "mean"})
            .sort_values("Total Billing", ascending=False)
            .head(10)
        )
        sp_lb.index = range(1, len(sp_lb) + 1)
        sp_lb.index.name = "Rank"

        st.dataframe(
            sp_lb.style.format({"Total Billing": "₹{:,.2f}", "Achievement %": "{:.1f}%"}),
            use_container_width=True,
        )


def render_raw_data(df: pd.DataFrame):
    """Show raw uploaded data in an expandable section."""
    with st.expander("📂 View Raw Uploaded Data"):
        st.dataframe(df, use_container_width=True, height=400)
