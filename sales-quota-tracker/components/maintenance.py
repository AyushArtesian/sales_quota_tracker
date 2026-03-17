"""Maintenance UI helpers (danger zone + client acquisition modal).

This module holds helper functions to keep app.py lean and modular.
"""

import pandas as pd
import streamlit as st

from utils.billing_manager import (
    clear_billing_data,
    delete_billing_data_by_month,
)
from utils.client_manager import add_new_clients_with_dates, update_clients
from utils.quota_manager import update_quotas
from utils.stage_cache import save_stage_cache


def render_danger_zone(raw_df: pd.DataFrame):
    """Render delete options for the app (clients/targets/transactions)."""

    st.sidebar.markdown("---")
    st.sidebar.subheader("Danger Zone")
    st.sidebar.warning("This will permanently delete data. Use with caution.")

    delete_mode = st.sidebar.selectbox(
        "What do you want to delete?",
        [
            "-- Select action --",
            "All data (clients/targets/transactions)",
            "All clients",
            "All targets",
            "All transactions",
            "Transactions by month",
        ],
        key="delete_mode",
    )

    months = []
    if not raw_df.empty and "Month" in raw_df.columns:
        months = sorted(raw_df["Month"].dropna().astype(str).unique())

    month_to_delete = None
    if delete_mode == "Transactions by month":
        month_to_delete = st.sidebar.selectbox(
            "Month to delete",
            ["-- Select month --"] + months,
            key="delete_month",
        )

    confirm = st.sidebar.checkbox(
        "Yes, I understand this cannot be undone", key="confirm_delete"
    )

    if st.sidebar.button("Delete", key="confirm_delete_button"):
        if not confirm:
            st.sidebar.warning("Please confirm the action by checking the box.")
            return

        if delete_mode == "All data (clients/targets/transactions)":
            clear_billing_data()
            update_quotas(pd.DataFrame())
            update_clients(pd.DataFrame())
            for key in ["raw_df", "quotas", "clients", "stage", "raw_file_name"]:
                if key in st.session_state:
                    del st.session_state[key]
            save_stage_cache("quota")
            st.sidebar.success("All data cleared. Please re-upload a billing file to continue.")
            st.rerun()

        elif delete_mode == "All clients":
            update_clients(pd.DataFrame())
            if "clients" in st.session_state:
                del st.session_state["clients"]
            st.sidebar.success("All clients deleted.")

        elif delete_mode == "All targets":
            update_quotas(pd.DataFrame())
            if "quotas" in st.session_state:
                del st.session_state["quotas"]
            st.sidebar.success("All targets deleted.")

        elif delete_mode == "All transactions":
            clear_billing_data()
            if "raw_df" in st.session_state:
                del st.session_state["raw_df"]
            st.sidebar.success("All transactions deleted.")

        elif delete_mode == "Transactions by month":
            if month_to_delete and month_to_delete != "-- Select month --":
                deleted = delete_billing_data_by_month(month_to_delete)
                if "raw_df" in st.session_state:
                    st.session_state["raw_df"] = st.session_state["raw_df"][
                        st.session_state["raw_df"]["Month"] != month_to_delete
                    ]
                st.sidebar.success(f"Deleted {deleted} transactions for {month_to_delete}.")
            else:
                st.sidebar.warning("Please select a month before deleting.")

        else:
            st.sidebar.info("Select an action to perform.")


def render_client_acquisition_modal(raw_df: pd.DataFrame, new_clients: list[str]):
    """Render the modal that requires acquisition dates before continuing."""

    st.markdown("---")
    st.warning("New clients detected! Please provide acquisition dates for each new client before continuing.")

    acquisition_dates = {}

    # Determine first transaction date per client (used to validate acquisition date)
    earliest_by_client = {}
    if not raw_df.empty and "Date" in raw_df.columns:
        df_dates = raw_df.copy()
        df_dates["_parsed_date"] = pd.to_datetime(df_dates["Date"], errors="coerce")

        for client_name in new_clients:
            mask = df_dates["Client Name"].astype(str).str.strip() == str(client_name)
            if mask.any():
                min_dt = df_dates.loc[mask, "_parsed_date"].min()
                if pd.notna(min_dt):
                    earliest_by_client[client_name] = min_dt.date()

    for client_name in new_clients:
        st.markdown(f"##### {client_name}")

        max_date = earliest_by_client.get(client_name)
        date_help = (
            "Enter when this client was acquired (must be on or before the first transaction date)."
            if max_date
            else "Enter when this client was acquired."
        )

        acq_date = st.date_input(
            f"Acquisition Date for {client_name}:",
            key=f"acq_date_{client_name}",
            help=date_help,
            max_value=max_date,
        )

        acquisition_dates[client_name] = acq_date.strftime("%Y-%m-%d") if acq_date else ""

        if max_date and acq_date and acq_date > max_date:
            st.error(
                f"Acquisition date cannot be after first transaction date ({max_date.isoformat()})."
            )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Client Dates", key="save_new_clients", use_container_width=True):
            add_new_clients_with_dates(new_clients, acquisition_dates)
            st.session_state["show_new_client_modal"] = False
            st.session_state["new_clients"] = []
            st.success("New clients added successfully!")
            st.rerun()

    with col2:
        if st.button("Skip for Now", key="skip_new_clients", use_container_width=True):
            st.session_state["show_new_client_modal"] = False
            st.session_state["new_clients"] = []
            st.info("You can edit client dates anytime in the Client Master section.")
            st.rerun()

    st.stop()
