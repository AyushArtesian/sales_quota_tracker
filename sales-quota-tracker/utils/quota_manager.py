"""
quota_manager.py
----------------
Manage quota entries: load / save / update via session state + CSV persistence.
(Target based quotas: Sales Rep or Sales Team)
"""

from pathlib import Path

import pandas as pd
import streamlit as st

QUOTA_CSV = Path(__file__).resolve().parent.parent / "data" / "quota_data.csv"

REQUIRED_COLUMNS = [
    "Entity Type",
    "Entity Name",
    "Members",
    "Start Month",
    "Duration Months",
    "Quota",
]


def _ensure_dir():
    QUOTA_CSV.parent.mkdir(parents=True, exist_ok=True)


def load_quotas() -> pd.DataFrame:
    """Load saved quotas from CSV (or return empty frame)."""
    if QUOTA_CSV.exists():
        df = pd.read_csv(QUOTA_CSV)
        df.columns = df.columns.str.strip()
        return _normalize_quota_schema(df)
    return pd.DataFrame(columns=REQUIRED_COLUMNS)


def _normalize_quota_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize any saved quota data to target schema."""
    if df.empty:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    # Already in target schema
    if all(col in df.columns for col in REQUIRED_COLUMNS):
        out = df[REQUIRED_COLUMNS].copy()
        out["Entity Type"] = out["Entity Type"].astype(str).str.strip()
        out["Entity Name"] = out["Entity Name"].astype(str).str.strip()
        out["Members"] = out["Members"].fillna("").astype(str).str.strip()
        out["Start Month"] = out["Start Month"].astype(str).str.strip()
        out["Duration Months"] = pd.to_numeric(out["Duration Months"], errors="coerce").fillna(1).clip(lower=1).astype(int)
        out["Quota"] = pd.to_numeric(out["Quota"], errors="coerce").fillna(0.0)
        return out

    # Legacy schema cannot be mapped reliably to targets. Start fresh.
    return pd.DataFrame(columns=REQUIRED_COLUMNS)


def save_quotas(df: pd.DataFrame):
    """Persist quota dataframe to CSV."""
    _ensure_dir()
    df.to_csv(QUOTA_CSV, index=False)


def init_quota_state(raw_df: pd.DataFrame):
    """Initialise session-state target quota frame."""
    saved = load_quotas()

    if saved.empty:
        # Add a sensible starter row for quick data entry
        first_rep = str(raw_df["Sales Person"].dropna().astype(str).iloc[0]) if not raw_df.empty else ""
        first_month = str(raw_df["Month"].dropna().astype(str).iloc[0]) if not raw_df.empty else ""
        starter = pd.DataFrame(
            [
                {
                    "Entity Type": "Sales Rep",
                    "Entity Name": first_rep,
                    "Members": first_rep,
                    "Start Month": first_month,
                    "Duration Months": 1,
                    "Quota": 0.0,
                }
            ]
        )
        st.session_state["quotas"] = _normalize_quota_schema(starter)
        return

    st.session_state["quotas"] = _normalize_quota_schema(saved).reset_index(drop=True)


def get_quotas() -> pd.DataFrame:
    """Return current quota dataframe from session state."""
    return st.session_state.get("quotas", pd.DataFrame(columns=REQUIRED_COLUMNS))


def update_quotas(df: pd.DataFrame):
    """Update session state and persist."""
    normalized = _normalize_quota_schema(df)
    st.session_state["quotas"] = normalized.reset_index(drop=True)
    save_quotas(normalized)
