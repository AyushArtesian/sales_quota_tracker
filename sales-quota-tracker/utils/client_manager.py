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


def detect_new_clients(raw_df: pd.DataFrame) -> list:
    """Detect clients in raw_df that are not yet in the client master database."""
    if raw_df.empty or "Client Name" not in raw_df.columns:
        return []
    
    # Get unique client names from upload
    uploaded_clients = set(raw_df["Client Name"].dropna().astype(str).str.strip().str.lower().unique())
    
    # Get existing client names from database
    existing_clients = get_clients()
    if existing_clients.empty:
        existing_client_names = set()
    else:
        existing_client_names = set(
            existing_clients["Client Name"].astype(str).str.strip().str.lower().unique()
        )
    
    # Find new clients
    new_client_names = uploaded_clients - existing_client_names
    
    # Return sorted list of new client names (with proper casing from raw_df)
    new_clients = []
    for client in sorted(new_client_names):
        # Find the original casing from raw_df
        original_name = raw_df[
            raw_df["Client Name"].astype(str).str.strip().str.lower() == client
        ]["Client Name"].iloc[0]
        new_clients.append(original_name)
    
    return new_clients


def add_new_clients_with_dates(new_clients: list, acquisition_dates: dict):
    """Add new clients to the master with their acquisition dates."""
    existing = get_clients()
    
    # Get the next client ID
    if existing.empty:
        next_id = 1
    else:
        try:
            max_id = (
                existing["Client Id"]
                .str.extract(r"(\d+)", expand=False)
                .astype(int)
                .max()
            )
            next_id = max_id + 1
        except:
            next_id = len(existing) + 1
    
    # Create new client rows
    new_rows = []
    for client_name in new_clients:
        acq_date = acquisition_dates.get(client_name, "")
        new_rows.append({
            "Client Id": f"CL-{next_id:03d}",
            "Client Name": client_name,
            "Acquisition Date": acq_date,
            "Consideration Expiration Month": "",
        })
        next_id += 1
    
    # Append to existing and save
    new_df = pd.concat([
        existing,
        pd.DataFrame(new_rows)
    ], ignore_index=True)
    
    save_clients(new_df)


def update_clients(df: pd.DataFrame):
    save_clients(df)


def apply_client_master_to_raw(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Merge client master fields into raw billing rows by Client Name."""
    if raw_df is None or raw_df.empty:
        return raw_df

    clients = get_clients()
    if clients.empty:
        if "Client Onboarding Date" not in raw_df.columns:
            out = raw_df.copy()
            out["Client Onboarding Date"] = ""
            return out
        return raw_df

    out = raw_df.copy()
    # Drop Consideration Expiration Month from raw if it exists, to avoid duplicates on merge
    if "Consideration Expiration Month" in out.columns:
        out = out.drop(columns=["Consideration Expiration Month"])
    
    out["_client_key"] = out["Client Name"].fillna("").astype(str).str.strip().str.lower()

    lookup = clients.copy()
    lookup["_client_key"] = lookup["Client Name"].fillna("").astype(str).str.strip().str.lower()
    lookup = lookup.drop_duplicates(subset=["_client_key"], keep="last")

    merged = out.merge(
        lookup[["_client_key", "Acquisition Date", "Consideration Expiration Month"]],
        on="_client_key",
        how="left",
    )

    merged["Client Onboarding Date"] = merged["Acquisition Date"].fillna("").astype(str).str.strip()
    merged = merged.drop(columns=["_client_key", "Acquisition Date"])

    return merged
