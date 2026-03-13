"""
excel_reader.py
---------------
Handles reading and validating uploaded Excel files containing billing records.
"""

import pandas as pd
import streamlit as st

REQUIRED_COLUMNS = {"Client Name", "Month", "Billing Amount", "Freelancer", "Sales Person"}


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
    df["Month"] = df["Month"].astype(str).str.strip()
    df["Client Name"] = df["Client Name"].astype(str).str.strip()
    df["Sales Person"] = df["Sales Person"].astype(str).str.strip()
    df["Freelancer"] = df["Freelancer"].astype(str).str.strip()

    return df
