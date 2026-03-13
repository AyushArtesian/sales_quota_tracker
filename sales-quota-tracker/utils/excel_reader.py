"""
excel_reader.py
---------------
Handles reading and validating uploaded Excel files containing billing records.
"""

import pandas as pd
import streamlit as st

REQUIRED_COLUMNS = {"Client Name", "Month", "Billing Amount", "Freelancer", "Sales Person"}
OPTIONAL_COLUMNS = {"Client Onboarding Date", "Sales Team"}


def read_excel(uploaded_file) -> pd.DataFrame | None:
    """Read an uploaded Excel file and return a validated DataFrame."""
    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl")
    except Exception as exc:
        st.error(f"Failed to read the Excel file: {exc}")
        return None

    # Normalize column names (strip whitespace)
    df.columns = df.columns.str.strip()

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        st.error(f"Missing required columns: {', '.join(sorted(missing))}")
        return None

    # Basic type coercion
    df["Billing Amount"] = pd.to_numeric(df["Billing Amount"], errors="coerce").fillna(0)

    # Parse month values in expected format (e.g. Jan-2026). Keep original if parsing fails.
    month_as_dt = pd.to_datetime(df["Month"], format="%b-%Y", errors="coerce")
    month_labels = month_as_dt.dt.strftime("%b-%Y")
    df["Month"] = month_labels.where(month_as_dt.notna(), df["Month"].astype(str)).astype(str).str.strip()

    df["Client Name"] = df["Client Name"].astype(str).str.strip()
    df["Sales Person"] = df["Sales Person"].astype(str).str.strip()
    df["Freelancer"] = df["Freelancer"].astype(str).str.strip()

    # Optional columns used by target analytics
    if "Client Onboarding Date" in df.columns:
        onboarding_dt = pd.to_datetime(df["Client Onboarding Date"], errors="coerce")
        df["Client Onboarding Date"] = onboarding_dt.dt.strftime("%Y-%m-%d")
    if "Sales Team" in df.columns:
        df["Sales Team"] = df["Sales Team"].fillna("").astype(str).str.strip()

    # Ensure optional columns exist to simplify downstream logic
    for col in OPTIONAL_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    return df
