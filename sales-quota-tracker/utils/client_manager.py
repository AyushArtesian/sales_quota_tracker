"""
client_manager.py
-----------------
Manage client master data via SQLAlchemy (SQLite) persistence.
"""

import pandas as pd
import streamlit as st

from .db import SessionLocal, init_db
from .models import ClientMaster

CLIENT_COLUMNS = [
    "Client Id",
    "Client Name",
    "Acquisition Date",
    "Consideration Expiration Month",
]


def _normalize_client_schema(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=CLIENT_COLUMNS)

    out = df.copy()
    for col in CLIENT_COLUMNS:
        if col not in out.columns:
            out[col] = ""

    out = out[CLIENT_COLUMNS].copy()
    out["Client Id"] = out["Client Id"].fillna("").astype(str).str.strip()
    out["Client Name"] = out["Client Name"].fillna("").astype(str).str.strip()
    out["Acquisition Date"] = out["Acquisition Date"].fillna("").astype(str).str.strip()
    out["Consideration Expiration Month"] = out["Consideration Expiration Month"].fillna("").astype(str).str.strip()

    out = out[out["Client Id"] != ""].copy()
    out = out.drop_duplicates(subset=["Client Id"], keep="last").reset_index(drop=True)
    return out


def load_clients() -> pd.DataFrame:
    init_db()
    with SessionLocal() as session:
        rows = session.query(ClientMaster).all()
        data = [
            {
                "Client Id": r.client_id,
                "Client Name": r.client_name,
                "Acquisition Date": r.acquisition_date or "",
                "Consideration Expiration Month": r.consideration_expiration_month or "",
            }
            for r in rows
        ]
    return pd.DataFrame(data, columns=CLIENT_COLUMNS)


def save_clients(df: pd.DataFrame):
    normalized = _normalize_client_schema(df)

    init_db()
    with SessionLocal() as session:
        session.query(ClientMaster).delete()
        for _, row in normalized.iterrows():
            session.add(
                ClientMaster(
                    client_id=row["Client Id"],
                    client_name=row["Client Name"],
                    acquisition_date=row["Acquisition Date"],
                    consideration_expiration_month=row["Consideration Expiration Month"],
                )
            )
        session.commit()

    st.session_state["clients"] = normalized


def init_client_state(raw_df: pd.DataFrame):
    saved = load_clients()
    if not saved.empty:
        st.session_state["clients"] = saved
        return

    if raw_df.empty or "Client Name" not in raw_df.columns:
        st.session_state["clients"] = pd.DataFrame(columns=CLIENT_COLUMNS)
        return

    unique_clients = sorted(raw_df["Client Name"].dropna().astype(str).str.strip().unique())
    starter = pd.DataFrame(
        [
            {
                "Client Id": f"CL-{index + 1:03d}",
                "Client Name": name,
                "Acquisition Date": "",
                "Consideration Expiration Month": "",
            }
            for index, name in enumerate(unique_clients)
        ]
    )

    normalized = _normalize_client_schema(starter)
    save_clients(normalized)


def get_clients() -> pd.DataFrame:
    return st.session_state.get("clients", pd.DataFrame(columns=CLIENT_COLUMNS))


def update_clients(df: pd.DataFrame):
    save_clients(df)
