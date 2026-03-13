"""
charts.py
---------
Plotly visualisations for the quota tracker.
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd


def billing_vs_quota_chart(df: pd.DataFrame):
    """Grouped bar chart: Billing vs Quota per client."""
    st.subheader("📊 Client Billing vs Quota")

    if df.empty:
        st.info("No data to display.")
        return

    chart_df = df.groupby("Client Name", as_index=False).agg(
        {"Total Billing": "sum", "Quota": "sum"}
    ).sort_values("Total Billing", ascending=False)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=chart_df["Client Name"],
        y=chart_df["Total Billing"],
        name="Total Billing",
        marker_color="#636EFA",
    ))
    fig.add_trace(go.Bar(
        x=chart_df["Client Name"],
        y=chart_df["Quota"],
        name="Quota",
        marker_color="#EF553B",
    ))
    fig.update_layout(
        barmode="group",
        xaxis_title="Client",
        yaxis_title="Amount (₹)",
        legend_title="Metric",
        height=420,
        template="plotly_white",
    )
    st.plotly_chart(fig, width="stretch")


def salesperson_performance_chart(df: pd.DataFrame):
    """Horizontal bar chart showing billing per sales person."""
    st.subheader("👤 Sales Person Performance")

    if df.empty:
        st.info("No data to display.")
        return

    sp_df = df.groupby("Sales Person", as_index=False).agg(
        {"Total Billing": "sum"}
    ).sort_values("Total Billing", ascending=True)

    fig = px.bar(
        sp_df,
        x="Total Billing",
        y="Sales Person",
        orientation="h",
        color="Total Billing",
        color_continuous_scale="Teal",
        labels={"Total Billing": "Billing (₹)"},
        template="plotly_white",
        height=max(300, len(sp_df) * 40 + 100),
    )
    fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig, width="stretch")


def achievement_distribution_chart(df: pd.DataFrame):
    """Pie / donut chart showing distribution of achievement statuses."""
    st.subheader("🏆 Quota Achievement Distribution")

    if df.empty:
        st.info("No data to display.")
        return

    status_counts = df["Status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]

    color_map = {
        "✅ Achieved": "#2ecc71",
        "🟡 Almost Achieved": "#f1c40f",
        "❌ Not Achieved": "#e74c3c",
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
    """Line chart: billing trend over months."""
    st.subheader("📈 Monthly Billing Trend")

    if df.empty:
        st.info("No data to display.")
        return

    month_df = df.groupby("Month", as_index=False).agg(
        {"Total Billing": "sum", "Quota": "sum"}
    )

    # Ensure month ordering is chronological (e.g., Jan, Feb, Mar)
    try:
        month_df["_month_dt"] = pd.to_datetime(month_df["Month"], format="%b-%Y", errors="coerce")
        month_df = month_df.sort_values("_month_dt").drop(columns=["_month_dt"])
    except Exception:
        month_df = month_df.sort_values("Month")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=month_df["Month"], y=month_df["Total Billing"],
        mode="lines+markers", name="Billing",
        line=dict(color="#636EFA", width=3),
    ))
    fig.add_trace(go.Scatter(
        x=month_df["Month"], y=month_df["Quota"],
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
