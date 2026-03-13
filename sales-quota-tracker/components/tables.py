"""
tables.py
---------
Achievement table and leaderboard displays.
"""

import streamlit as st
import pandas as pd


def render_achievement_table(df: pd.DataFrame):
    """Show the detailed achievement table with colour-coded status."""
    st.subheader("Quota Achievement Details")

    if df.empty:
        st.info("No data to display.")
        return

    display_cols = [
        "Entity Type",
        "Entity Name",
        "Start Month",
        "Duration Months",
        "Quota",
        "Total Billing",
        "New Client Billing",
        "Existing Client Billing",
        "Achievement %",
        "Status",
        "Clients Count",
    ]
    display = df[[c for c in display_cols if c in df.columns]].copy()

    # Convert month strings to datetimes for correct default sorting, and display as readable labels
    if "Start Month" in display.columns:
        display["_month_dt"] = pd.to_datetime(display["Start Month"], format="%b-%Y", errors="coerce")
        display = display.sort_values("_month_dt")
        display.loc[display["_month_dt"].notna(), "Start Month"] = (
            display.loc[display["_month_dt"].notna(), "_month_dt"].dt.strftime("%b-%Y")
        )
        display = display.drop(columns=["_month_dt"])

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
        .format(
            {

                "Quota": "₹{:,.2f}",
                "Total Billing": "₹{:,.2f}",
                "New Client Billing": "₹{:,.2f}",
                "Existing Client Billing": "₹{:,.2f}",
                "Achievement %": "{:.1f}%",
            }
        )
        .set_table_styles(
            [
                {"selector": "th", "props": [("background-color", "#f2f2f2"), ("color", "#333"), ("font-weight", "600")]},
                {"selector": "td", "props": [("padding", "8px")]} ,
            ]
        )
    )

    st.dataframe(styled, width="stretch", height=min(600, 40 * len(display) + 60))


def render_leaderboard(df: pd.DataFrame):
    """Show top-performing targets and sales persons by achievement and billing."""
    st.subheader("Leaderboard")

    if df.empty:
        st.info("No data to display.")
        return

    col_targets, col_reps = st.columns(2)

    with col_targets:
        st.markdown("**Top Targets by Achievement %**")
        target_achievement = (
            df.groupby(["Entity Type", "Entity Name"], as_index=False)
            .agg({
                "Total Billing": "sum",
                "Quota": "sum",
            })
        )
        target_achievement["Achievement %"] = target_achievement.apply(
            lambda r: round((r["Total Billing"] / r["Quota"]) * 100, 2) if r["Quota"] > 0 else 0,
            axis=1,
        )
        target_achievement["Target"] = target_achievement["Entity Type"] + " - " + target_achievement["Entity Name"]
        target_achievement = target_achievement.sort_values("Achievement %", ascending=False).head(10)
        target_achievement.index = range(1, len(target_achievement) + 1)
        target_achievement.index.name = "Rank"

        st.dataframe(
            target_achievement[["Target", "Total Billing", "Quota", "Achievement %"]].style.format({
                "Total Billing": "₹{:,.2f}",
                "Quota": "₹{:,.2f}",
                "Achievement %": "{:.1f}%",
            }),
            width="stretch",
        )

    with col_reps:
        st.markdown("**Sales Person Billing from Sales Person Targets**")
        rep_df = df[df["Entity Type"] == "Sales Person"].copy() if "Entity Type" in df.columns else df.iloc[0:0]
        rep_billing = (
            rep_df.groupby("Entity Name", as_index=False)
            .agg({"Total Billing": "sum", "Quota": "sum"})
        )
        rep_billing["Achievement %"] = rep_billing.apply(
            lambda r: round((r["Total Billing"] / r["Quota"]) * 100, 2) if r["Quota"] > 0 else 0,
            axis=1,
        )
        rep_billing = rep_billing.sort_values("Total Billing", ascending=False).head(10)
        rep_billing.index = range(1, len(rep_billing) + 1)
        rep_billing.index.name = "Rank"

        st.dataframe(
            rep_billing.style.format({"Total Billing": "₹{:,.2f}", "Quota": "₹{:,.2f}", "Achievement %": "{:.1f}%"}),
            width="stretch",
        )


def render_raw_data(df: pd.DataFrame):
    """Show raw uploaded data in an expandable section."""
    with st.expander("View Raw Uploaded Data"):
        st.dataframe(df, width="stretch", height=400)
