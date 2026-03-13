"""
quota_input.py
--------------
UI section for manually entering / editing quotas per Client + Month.
"""

import streamlit as st
import pandas as pd

from utils.quota_manager import get_quotas, update_quotas


def render_quota_editor():
    """Render the editable quota table and individual number inputs."""
    st.subheader("✏️ Manual Quota Entry")

    quotas = get_quotas()
    if quotas.empty:
        st.info("Upload billing data first to populate Client × Month combinations.")
        return

    tab_table, tab_individual = st.tabs(["📋 Editable Table", "🔢 Individual Input"])

    # ── Tab 1: Editable data-editor ────────────────────────────────────
    with tab_table:
        st.caption("Edit the **Quota** column directly, then click **Save Quotas**.")
        
        # Sort quotas chronologically by month for better readability
        quotas_sorted = quotas.copy()
        quotas_sorted["_month_dt"] = pd.to_datetime(quotas_sorted["Month"], format="%b-%Y", errors="coerce")
        quotas_sorted = quotas_sorted.sort_values(["_month_dt", "Client Name"])
        quotas_display = quotas_sorted.drop(columns=["_month_dt"])
        
        edited = st.data_editor(
            quotas_display,
            column_config={
                "Client Name": st.column_config.TextColumn(disabled=True),
                "Month": st.column_config.TextColumn(disabled=True),
                "Quota": st.column_config.NumberColumn(
                    "Quota (₹)", min_value=0, step=1000, format="₹%d"
                ),
            },
            width="stretch",
            num_rows="fixed",
            key="quota_editor",
        )

        if st.button("💾 Save Quotas", key="save_table"):
            update_quotas(edited)
            st.success("Quotas saved successfully!")
            st.rerun()

    # ── Tab 2: Individual number_input per row ─────────────────────────
    with tab_individual:
        st.caption("Set quota for a specific Client × Month.")
        clients = sorted(quotas["Client Name"].unique())
        
        # Sort months chronologically instead of alphabetically
        months_list = quotas["Month"].unique()
        months_dt = pd.to_datetime(months_list, format="%b-%Y", errors="coerce")
        months = [m for dt, m in sorted(zip(months_dt, months_list)) if pd.notna(dt)]

        sel_client = st.selectbox("Client", clients, key="qi_client")
        sel_month = st.selectbox("Month", months, key="qi_month")

        current_row = quotas[
            (quotas["Client Name"] == sel_client) & (quotas["Month"] == sel_month)
        ]
        current_val = float(current_row["Quota"].iloc[0]) if not current_row.empty else 0.0

        new_val = st.number_input(
            "Quota (₹)",
            min_value=0.0,
            value=current_val,
            step=1000.0,
            key="qi_value",
        )

        if st.button("💾 Save", key="save_individual"):
            idx = quotas[
                (quotas["Client Name"] == sel_client) & (quotas["Month"] == sel_month)
            ].index
            if not idx.empty:
                quotas.loc[idx, "Quota"] = new_val
            else:
                quotas = pd.concat(
                    [quotas, pd.DataFrame([{"Client Name": sel_client, "Month": sel_month, "Quota": new_val}])],
                    ignore_index=True,
                )
            update_quotas(quotas)
            st.success(f"Quota for **{sel_client}** – {sel_month} set to ₹{new_val:,.0f}")
            st.rerun()
