"""
quota_manager.py
----------------
Manage quota entries via SQLAlchemy (SQLite) persistence.
Targets can be for Sales Person or Sales Team.
"""

import pandas as pd
import streamlit as st

from .db import SessionLocal, init_db
from .models import QuotaTarget

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
    """Load saved quotas from the database (or return empty frame)."""
    init_db()
    with SessionLocal() as session:
        rows = session.query(QuotaTarget).all()
        data = [
            {
                "Entity Type": r.entity_type,
                "Entity Name": r.entity_name,
                "Members": r.members or "",
                "Start Month": r.start_month,
                "Duration Months": r.duration_months,
                "Quota": r.quota,
            }
            for r in rows
        ]
    return pd.DataFrame(data, columns=REQUIRED_COLUMNS)


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
    """Persist quotas to the SQLite database."""
    init_db()
    with SessionLocal() as session:
        session.query(QuotaTarget).delete()
        for _, row in df.iterrows():
            session.add(
                QuotaTarget(
                    entity_type=str(row.get("Entity Type", "") or "").strip(),
                    entity_name=str(row.get("Entity Name", "") or "").strip(),
                    members=str(row.get("Members", "") or "").strip(),
                    start_month=str(row.get("Start Month", "") or "").strip(),
                    duration_months=int(row.get("Duration Months", 1) or 1),
                    quota=float(row.get("Quota", 0) or 0),
                )
            )
        session.commit()

    # Keep derived tables (achievement/leaderboard/salesperson billing) in sync.
    try:
        from .derived_manager import update_derived_tables
        from .billing_manager import load_billing_data

        raw = load_billing_data()
        update_derived_tables(raw, df)
    except Exception:
        # Ensure quota updates are not blocked by derived table issues.
        pass


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
                    "Entity Type": "Sales Person",
                    "Entity Name": first_rep,
                    "Members": first_rep,
                    "Start Month": first_month,
                    "Duration Months": 1,
                    "Quota": 0.0,
                }
            ]
        )
        normalized = _normalize_quota_schema(starter)
        save_quotas(normalized)
        st.session_state["quotas"] = normalized
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
