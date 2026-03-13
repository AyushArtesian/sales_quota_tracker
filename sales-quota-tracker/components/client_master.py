"""
client_master.py
----------------
UI for client master add/edit management.
"""

import pandas as pd
import streamlit as st

from utils.client_manager import get_clients, update_clients


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
        },
        num_rows="dynamic",
        width="stretch",
        key="client_master_editor",
    )

    if st.button("Save Clients", key="save_clients"):
        update_clients(edited)
        st.success("Client master saved successfully.")

    st.markdown("---")
    st.caption("Quick Add Client")

    col1, col2 = st.columns(2)
    with col1:
        client_id = st.text_input("Client Id", key="new_client_id")
        client_name = st.text_input("Client Name", key="new_client_name")
    with col2:
        acquisition_date = st.text_input("Acquisition Date (YYYY-MM-DD)", key="new_client_acq_date")
        expiration_month = st.text_input("Consideration Expiration Month (e.g., Jan-2026)", key="new_client_exp_month")

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
                        }
                    ]
                )
                updated = pd.concat([clients, new_row], ignore_index=True)
                update_clients(updated)
                st.success(f"Added client '{client_name.strip()}'.")
