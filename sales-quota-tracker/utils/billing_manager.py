"""
billing_manager.py
------------------
Manage billing data persistence via SQLAlchemy (SQLite).
"""

import pandas as pd
import streamlit as st

from .db import SessionLocal, init_db
from .models import BillingData


def save_billing_data(df: pd.DataFrame):
    """Persist the raw billing dataframe to the database."""
    if df.empty:
        return

    init_db()
    with SessionLocal() as session:
        # Clear existing billing data
        session.query(BillingData).delete()

        # Insert new data
        for _, row in df.iterrows():
            session.add(
                BillingData(
                    date=str(row.get("Date", "")),
                    type=str(row.get("Type", "")),
                    description=str(row.get("Description", "")),
                    sales_person=str(row.get("Sales Person", "")),
                    sales_team=str(row.get("Sales Team", "")),
                    billing_amount=float(row.get("Billing Amount", 0) or 0),
                    month=str(row.get("Month", "")),
                    client_name=str(row.get("Client Name", "")),
                    client_onboarding_date=str(row.get("Client Onboarding Date", "") or ""),
                    consideration_expiration_month=str(row.get("Consideration Expiration Month", "") or ""),
                )
            )
        session.commit()

    # Keep derived tables (achievement/leaderboard/salesperson billing) in sync.
    try:
        from .derived_manager import update_derived_tables
        from .quota_manager import load_quotas

        quotas = load_quotas()
        update_derived_tables(df, quotas)
    except Exception:
        # Guard against derived table errors; core billing save should not fail.
        pass


def load_billing_data() -> pd.DataFrame:
    """Load the raw billing dataframe from the database."""
    init_db()
    with SessionLocal() as session:
        rows = session.query(BillingData).all()
        if not rows:
            return pd.DataFrame()
        
        data = [
            {
                "Date": r.date,
                "Type": r.type,
                "Description": r.description,
                "Sales Person": r.sales_person,
                "Sales Team": r.sales_team,
                "Billing Amount": r.billing_amount,
                "Month": r.month,
                "Client Name": r.client_name,
                "Client Onboarding Date": r.client_onboarding_date or "",
                "Consideration Expiration Month": r.consideration_expiration_month or "",
            }
            for r in rows
        ]
    
    return pd.DataFrame(data)


def clear_billing_data():
    """Clear all billing data from the database."""
    init_db()
    with SessionLocal() as session:
        session.query(BillingData).delete()
        session.commit()


def delete_billing_data_by_month(month: str) -> int:
    """Delete billing rows for a specific month.

    Returns:
        int: number of rows deleted.
    """
    if not month:
        return 0

    init_db()
    with SessionLocal() as session:
        rows = session.query(BillingData).filter(BillingData.month == month)
        count = rows.count()
        if count:
            rows.delete(synchronize_session=False)
            session.commit()
        return count
