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

    # Colour styling (subtle, to keep text readable)
    def _highlight_status(row):
        status = str(row.get("Status", ""))
        if "Achieved" in status and "Almost" not in status:
            return ["background-color: rgba(46, 204, 113, 0.25)"] * len(row)
        elif "Almost" in status:
            return ["background-color: rgba(241, 196, 15, 0.18)"] * len(row)
        else:
            return ["background-color: rgba(231, 76, 60, 0.2)"] * len(row)

    styled = (
        display.style
        .apply(_highlight_status, axis=1)
        .format({"Quota": "₹{:,.2f}", "Total Billing": "₹{:,.2f}", "Achievement %": "{:.1f}%"})
        .set_table_styles(
            [
                {"selector": "th", "props": [("background-color", "#f2f2f2"), ("color", "#333"), ("font-weight", "600")]},
                {"selector": "td", "props": [("padding", "8px")]} ,
            ]
        )
    )

    st.dataframe(styled, width="stretch", height=min(600, 40 * len(display) + 60))


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
            width="stretch",
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
            width="stretch",
        )


def render_raw_data(df: pd.DataFrame):
    """Show raw uploaded data in an expandable section."""
    with st.expander("📂 View Raw Uploaded Data"):
        st.dataframe(df, width="stretch", height=400)
