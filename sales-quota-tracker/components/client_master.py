"""
client_master.py
----------------
UI for client master add/edit management.
"""

import pandas as pd
import streamlit as st

from utils.client_manager import get_clients, update_clients, apply_client_master_to_raw
from utils.billing_manager import save_billing_data
from utils.quota_manager import load_quotas
from utils.derived_manager import update_derived_tables


def render_client_master():
    st.subheader("Client Master")
    st.caption("Add or edit clients used for sales tracking.")

    clients = get_clients().copy()

    edited = st.data_editor(
        clients,
        column_config={
            "Client Id": st.column_config.TextColumn(required=True),
            "Client Name": st.column_config.TextColumn(required=True),
            "Acquisition Date": st.column_config.TextColumn(help="Format: YYYY-MM-DD"),
            "Consideration Expiration Month": st.column_config.TextColumn(help="Format: Jan-2026"),
            "Excluded": st.column_config.CheckboxColumn(help="Check to exclude this client from analysis"),
        },
        num_rows="dynamic",
        width="stretch",
        key="client_master_editor",
    )

    if st.button("Save Clients", key="save_clients"):
        update_clients(edited)
        
        # Re-apply exclusions to original data and re-save billing data + derived tables
        original_df = st.session_state.get("raw_df_original")
        if original_df is not None and not original_df.empty:
            # Re-apply latest exclusion rules to the original unfiltered data
            filtered_df = apply_client_master_to_raw(original_df)
            st.session_state["raw_df"] = filtered_df
            
            # Re-persist the newly filtered data
            save_billing_data(filtered_df)
            
            # Re-calculate derived tables with newly filtered data
            try:
                quotas_df = load_quotas()
                update_derived_tables(filtered_df, quotas_df)
            except Exception:
                pass
        
        st.success("Client master saved successfully. Exclusions applied!")

    st.markdown("---")
    st.caption("Quick Add Client")

    col1, col2 = st.columns(2)
    with col1:
        client_id = st.text_input("Client Id", key="new_client_id")
        client_name = st.text_input("Client Name", key="new_client_name")
    with col2:
        acquisition_date = st.text_input("Acquisition Date (YYYY-MM-DD)", key="new_client_acq_date")
        expiration_month = st.text_input("Consideration Expiration Month (e.g., Jan-2026)", key="new_client_exp_month")

    excluded = st.checkbox("Exclude Client", key="new_client_excluded", value=False)

    if st.button("Add Client", key="add_client"):
        if not client_id.strip() or not client_name.strip():
            st.warning("Client Id and Client Name are required.")
        else:
            duplicate = (clients["Client Id"].astype(str).str.strip() == client_id.strip()).any() if not clients.empty else False
            if duplicate:
                st.warning("Client Id already exists. Use a unique Client Id.")
            else:
                new_row = pd.DataFrame(
                    [
                        {
                            "Client Id": client_id.strip(),
                            "Client Name": client_name.strip(),
                            "Acquisition Date": acquisition_date.strip(),
                            "Consideration Expiration Month": expiration_month.strip(),
                            "Excluded": excluded,
                        }
                    ]
                )
                updated = pd.concat([clients, new_row], ignore_index=True)
                update_clients(updated)
                st.success(f"Added client '{client_name.strip()}'.")
