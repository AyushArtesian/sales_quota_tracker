"""
excel_reader.py
---------------
Handles reading and validating uploaded billing files (Excel/CSV).
"""

import pandas as pd
import streamlit as st

REQUIRED_BILLING_COLUMNS = {"Date", "Type", "Description", "Team", "Amount"}
OPTIONAL_BILLING_COLUMNS = {"Sales Person"}
QUOTA_COLUMNS = {"Entity Type", "Entity Name", "Members", "Start Month", "Duration Months", "Quota"}
DEFAULT_SALES_PERSON = "Paras and Hardik"


def _is_quota_schema(df: pd.DataFrame) -> bool:
    """Return True if the dataframe looks like a quota export (quota table columns)."""
    return QUOTA_COLUMNS.issubset(set(df.columns))


def read_excel(uploaded_file) -> tuple[pd.DataFrame | None, str]:
    """Read an uploaded Excel or CSV file and return a (df, type) tuple.

    Returns:
        (df, "billing") if it is billing data (expected columns).
        (df, "quota") if it looks like a quota export.
        (None, "error") if the file is invalid.
    """
    try:
        if uploaded_file.name.endswith(".csv"):
            # For CSV, use quoting to handle quoted fields properly
            df = pd.read_csv(uploaded_file, quotechar='"')
        else:
            df = pd.read_excel(uploaded_file, engine="openpyxl")
    except Exception as exc:
        st.error(f"Failed to read the file: {exc}")
        return None, "error"

    # Normalize column names: strip whitespace, quotes, BOMs
    df.columns = (
        df.columns
        .str.strip()
        .str.strip('"')
        .str.lstrip("\ufeff")
    )

    # If the file is a quota export, return as quota data (no billing parsing)
    if _is_quota_schema(df):
        return df, "quota"

    missing = REQUIRED_BILLING_COLUMNS - set(df.columns)
    if missing:
        st.error(
            f"Missing required columns: {', '.join(sorted(missing))}\n\nDetected columns: {', '.join(sorted(df.columns))}"
        )
        return None, "error"

    if "Sales Person" not in df.columns:
        df["Sales Person"] = DEFAULT_SALES_PERSON

    # Basic type coercion
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)

    # Parse Date with flexible format handling
    # Try multiple date formats: "Feb 27, 2026", "Feb-27-2026", "2026-02-27", etc.
    date_parsed = pd.to_datetime(df["Date"], format="%b %d, %Y", errors="coerce")

    # If some dates failed to parse, try other formats
    failed_mask = date_parsed.isna()
    if failed_mask.any():
        date_parsed.loc[failed_mask] = pd.to_datetime(df.loc[failed_mask, "Date"], errors="coerce")

    df["Month"] = date_parsed.dt.strftime("%b-%Y")

    # If still some failed, try one more time with flexible parsing
    still_failed = df["Month"].isna()
    if still_failed.any():
        df.loc[still_failed, "Month"] = pd.to_datetime(
            df.loc[still_failed, "Date"], infer_datetime_format=True, errors="coerce"
        ).dt.strftime("%b-%Y")

    # Normalize text columns
    df["Description"] = df["Description"].astype(str).str.strip().str.strip('"')
    df["Type"] = df["Type"].astype(str).str.strip().str.strip('"')
    df["Sales Person"] = (
        df["Sales Person"].astype(str).str.strip().str.strip('"').replace("", DEFAULT_SALES_PERSON)
    )
    df["Team"] = df["Team"].astype(str).str.strip().str.strip('"')
    df["Date"] = df["Date"].astype(str).str.strip().str.strip('"')

    # Business mapping for this organization:
    # - Team (in source CSV) = Client/Account Name
    # - Sales Team (internal) is a single working team by default
    df["Client Name"] = df["Team"]
    df["Sales Team"] = "Sales Team"

    # Rename for downstream compatibility with aggregation and dashboard
    df.rename(
        columns={
            "Amount": "Billing Amount",
        },
        inplace=True,
    )

    # Add optional columns if missing (for compatibility)
    if "Client Onboarding Date" not in df.columns:
        df["Client Onboarding Date"] = ""

    return df, "billing"
