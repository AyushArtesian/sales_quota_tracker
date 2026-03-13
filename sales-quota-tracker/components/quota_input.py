"""
quota_input.py
--------------
UI section for target-based quota entry (Sales Rep or Sales Team).
"""

import streamlit as st
import pandas as pd

from utils.quota_manager import get_quotas, update_quotas


def _months_sorted(values) -> list[str]:
    months_list = [str(v) for v in values if str(v).strip()]
    months_dt = pd.to_datetime(months_list, format="%b-%Y", errors="coerce")
    parsed = [m for dt, m in sorted(zip(months_dt, months_list)) if pd.notna(dt)]
    remainder = [m for dt, m in zip(months_dt, months_list) if pd.isna(dt)]
    return parsed + sorted(set(remainder))


def render_quota_editor(raw_df: pd.DataFrame):
    """Render target quota editor and quick target creation form."""
    st.subheader("Manual Quota Entry")

    quotas = get_quotas()
    tab_table, tab_add = st.tabs(["Editable Table", "Add Target"])

    # ── Tab 1: Editable data-editor ────────────────────────────────────
    with tab_table:
        st.caption("Edit target rows directly, then click Save Quotas.")

        quotas_sorted = quotas.copy()
        if not quotas_sorted.empty and "Start Month" in quotas_sorted.columns:
            quotas_sorted["_month_dt"] = pd.to_datetime(quotas_sorted["Start Month"], format="%b-%Y", errors="coerce")
            quotas_sorted = quotas_sorted.sort_values(["_month_dt", "Entity Type", "Entity Name"]).drop(columns=["_month_dt"])

        edited = st.data_editor(
            quotas_sorted,
            column_config={
                "Entity Type": st.column_config.SelectboxColumn(options=["Sales Rep", "Sales Team"]),
                "Entity Name": st.column_config.TextColumn(),
                "Members": st.column_config.TextColumn(help="Comma-separated sales reps for team targets"),
                "Start Month": st.column_config.TextColumn(help="Format: Jan-2026"),
                "Duration Months": st.column_config.NumberColumn(min_value=1, step=1, format="%d"),
                "Quota": st.column_config.NumberColumn(
                    "Quota (₹)", min_value=0, step=1000, format="₹%d"
                ),
            },
            width="stretch",
            num_rows="dynamic",
            key="quota_editor",
        )

        if st.button("Save Quotas", key="save_table"):
            update_quotas(edited)
            st.success("Quotas saved successfully!")
            st.rerun()

    # ── Tab 2: Add target form ─────────────────────────────────────────
    with tab_add:
        st.caption("Create a target like: Hardik achieves ₹150000 within 3 months.")
        sales_reps = sorted(raw_df["Sales Person"].dropna().astype(str).unique()) if not raw_df.empty else []
        months = _months_sorted(raw_df["Month"].dropna().astype(str).unique()) if not raw_df.empty else []

        target_type = st.selectbox("Target Type", ["Sales Rep", "Sales Team"], key="target_type")
        if target_type == "Sales Rep":
            entity_name = st.selectbox("Sales Rep", sales_reps, key="target_entity_rep") if sales_reps else st.text_input("Sales Rep", key="target_entity_rep_text")
            members = entity_name
        else:
            entity_name = st.text_input("Sales Team Name", key="target_entity_team")
            selected_members = st.multiselect("Team Members", sales_reps, default=sales_reps[:1] if sales_reps else [])
            members = ", ".join(selected_members)

        start_month = st.selectbox("Start Month", months, key="target_start_month") if months else st.text_input("Start Month (e.g., Jan-2026)", key="target_start_month_text")
        duration_months = st.number_input("Duration (Months)", min_value=1, value=3, step=1)
        quota = st.number_input("Quota (₹)", min_value=0.0, value=150000.0, step=1000.0)

        if st.button("Add Target", key="add_target"):
            new_row = pd.DataFrame(
                [
                    {
                        "Entity Type": target_type,
                        "Entity Name": entity_name,
                        "Members": members,
                        "Start Month": start_month,
                        "Duration Months": int(duration_months),
                        "Quota": float(quota),
                    }
                ]
            )
            updated = pd.concat([quotas, new_row], ignore_index=True)
            update_quotas(updated)
            st.success("Target added successfully!")
            st.rerun()
