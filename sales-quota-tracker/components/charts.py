"""
charts.py
---------
Plotly visualisations for the quota tracker (Sales Person focused).
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd


def salesperson_quota_chart(df: pd.DataFrame):
    """Grouped bar chart: Target Billing vs Quota."""
    st.subheader("Target Billing vs Quota")

    if df.empty:
        st.info("No data to display.")
        return

    chart_df = df.groupby(["Entity Type", "Entity Name"], as_index=False).agg(
        {"Total Billing": "sum", "Quota": "sum"}
    ).sort_values("Total Billing", ascending=False)
    chart_df["Target"] = chart_df["Entity Type"] + " - " + chart_df["Entity Name"]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=chart_df["Target"],
        y=chart_df["Total Billing"],
        name="Total Billing",
        marker_color="#636EFA",
    ))
    fig.add_trace(go.Bar(
        x=chart_df["Target"],
        y=chart_df["Quota"],
        name="Quota",
        marker_color="#EF553B",
    ))
    fig.update_layout(
        barmode="group",
        xaxis_title="Target",
        yaxis_title="Amount (₹)",
        legend_title="Metric",
        height=420,
        template="plotly_white",
    )
    st.plotly_chart(fig, width="stretch")


def achievement_status_chart(df: pd.DataFrame):
    """Pie / donut chart showing distribution of achievement statuses."""
    st.subheader("Quota Achievement Distribution")

    if df.empty:
        st.info("No data to display.")
        return

    status_counts = df["Status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]

    color_map = {
        "Achieved": "#2ecc71",
        "Almost Achieved": "#f1c40f",
        "Not Achieved": "#e74c3c",
    }

    fig = px.pie(
        status_counts,
        values="Count",
        names="Status",
        color="Status",
        color_discrete_map=color_map,
        hole=0.45,
        template="plotly_white",
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(height=400)
    st.plotly_chart(fig, width="stretch")


def monthly_trend_chart(df: pd.DataFrame):
    """Line chart: billing trend over calendar months."""
    st.subheader("Monthly Billing Trend")

    if df.empty:
        st.info("No data to display.")
        return

    # Prefer actual billing month field if provided, otherwise fall back to start month
    month_field = "Month" if "Month" in df.columns else "Start Month"

    month_df = df.groupby(month_field, as_index=False).agg(
        {"Total Billing": "sum", "Quota": "sum"}
    )

    # Ensure month ordering is chronological (e.g., Jan, Feb, Mar)
    try:
        month_df["_month_dt"] = pd.to_datetime(month_df[month_field], format="%b-%Y", errors="coerce")
        month_df = month_df.sort_values("_month_dt").drop(columns=["_month_dt"])
    except Exception:
        month_df = month_df.sort_values(month_field)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=month_df["Start Month"], y=month_df["Total Billing"],
        mode="lines+markers", name="Billing",
        line=dict(color="#636EFA", width=3),
    ))
    fig.add_trace(go.Scatter(
        x=month_df["Start Month"], y=month_df["Quota"],
        mode="lines+markers", name="Quota",
        line=dict(color="#EF553B", width=3, dash="dash"),
    ))
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Amount (₹)",
        template="plotly_white",
        height=380,
    )
    st.plotly_chart(fig, width="stretch")


def salesperson_achievement_chart(df: pd.DataFrame):
    """Horizontal bar chart: Achievement % per target."""
    st.subheader("Target Achievement %")

    if df.empty:
        st.info("No data to display.")
        return

    sp_df = (
        df.groupby(["Entity Type", "Entity Name"], as_index=False)
        .agg(
            Total_Billing=("Total Billing", "sum"),
            Quota=("Quota", "sum"),
        )
    )
    sp_df["Achievement %"] = sp_df.apply(
            lambda r: round((r["Total_Billing"] / r["Quota"]) * 100, 2) if r["Quota"] > 0 else 0,
            axis=1,
    )
    sp_df["Target"] = sp_df["Entity Type"] + " - " + sp_df["Entity Name"]
    sp_df = sp_df.sort_values("Achievement %", ascending=True)

    fig = px.bar(
        sp_df,
        x="Achievement %",
        y="Target",
        orientation="h",
        color="Achievement %",
        color_continuous_scale="RdYlGn",
        labels={"Achievement %": "Achievement %"},
        template="plotly_white",
        height=max(300, len(sp_df) * 40 + 100),
    )
    fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig, width="stretch")
