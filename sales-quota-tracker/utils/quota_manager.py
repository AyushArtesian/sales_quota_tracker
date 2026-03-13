"""
quota_manager.py
----------------
Manage quota entries: load / save / update via session state + CSV persistence.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

QUOTA_CSV = Path(__file__).resolve().parent.parent / "data" / "quota_data.csv"


def _ensure_dir():
    QUOTA_CSV.parent.mkdir(parents=True, exist_ok=True)


def load_quotas() -> pd.DataFrame:
    """Load saved quotas from CSV (or return empty frame)."""
    if QUOTA_CSV.exists():
        df = pd.read_csv(QUOTA_CSV)
        df.columns = df.columns.str.strip()
        return df
    return pd.DataFrame(columns=["Client Name", "Month", "Quota"])


def save_quotas(df: pd.DataFrame):
    """Persist quota dataframe to CSV."""
    _ensure_dir()
    df.to_csv(QUOTA_CSV, index=False)


def init_quota_state(billing_agg: pd.DataFrame):
    """Initialise session-state quota frame from aggregated billing keys."""
    saved = load_quotas()

    # Build a key-set from billing
    keys = billing_agg[["Client Name", "Month"]].drop_duplicates()

    if saved.empty:
        keys["Quota"] = 0.0
        st.session_state["quotas"] = keys.reset_index(drop=True)
    else:
        # Merge: keep existing quotas and add any new client-month combos
        merged = keys.merge(saved, on=["Client Name", "Month"], how="left")
        merged["Quota"] = merged["Quota"].fillna(0.0)
        st.session_state["quotas"] = merged.reset_index(drop=True)


def get_quotas() -> pd.DataFrame:
    """Return current quota dataframe from session state."""
    return st.session_state.get("quotas", pd.DataFrame(columns=["Client Name", "Month", "Quota"]))


def update_quotas(df: pd.DataFrame):
    """Update session state and persist."""
    st.session_state["quotas"] = df.reset_index(drop=True)
    save_quotas(df)
