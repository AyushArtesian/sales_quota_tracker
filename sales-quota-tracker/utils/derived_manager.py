"""Derived dataset persistence.

This module computes and persists derived tables (achievement, leaderboard, salesperson billing)
based on the current billing/quotas data. It is designed to be called whenever billing or quotas
change so the derived tables stay in sync.
"""

import pandas as pd

from .db import SessionLocal, init_db
from .models import Leaderboard, QuotaAchievement, SalespersonBilling
from .calculations import compute_achievement


def _write_table(session, model, rows: list[dict]):
    session.query(model).delete()
    for row in rows:
        session.add(model(**row))


def update_derived_tables(raw_df: pd.DataFrame, quotas_df: pd.DataFrame):
    """Recompute and persist derived tables based on the latest raw and quota data."""

    init_db()

    achievement_df = compute_achievement(raw_df, quotas_df)

    # Leaderboard: top targets by achievement %
    leaderboard = (
        achievement_df.sort_values(by=["Achievement %", "Total Billing"], ascending=[False, False])
        .reset_index(drop=True)
    )
    leaderboard_rows = []
    for idx, row in leaderboard.iterrows():
        leaderboard_rows.append(
            {
                "rank": int(idx + 1),
                "entity_type": row.get("Entity Type", ""),
                "entity_name": row.get("Entity Name", ""),
                "achievement_pct": float(row.get("Achievement %", 0.0) or 0.0),
                "total_billing": float(row.get("Total Billing", 0.0) or 0.0),
                "quota": float(row.get("Quota", 0.0) or 0.0),
                "status": row.get("Status", ""),
            }
        )

    # Salesperson billing summary (from raw billing data)
    if raw_df is None or raw_df.empty:
        sales_rows = []
    else:
        sales_summary = (
            raw_df.groupby("Sales Person")["Billing Amount"].agg(["sum", "count"]).reset_index()
        )
        sales_rows = []
        for _, row in sales_summary.iterrows():
            sales_rows.append(
                {
                    "sales_person": row["Sales Person"],
                    "total_billing": float(row["sum"] or 0.0),
                    "billing_count": int(row["count"] or 0),
                }
            )

    # Map achievement dataframe columns to model fields (SQLAlchemy requires snake_case args)
    qa_rows = []
    for row in achievement_df.to_dict("records"):
        qa_rows.append(
            {
                "entity_type": row.get("Entity Type", ""),
                "entity_name": row.get("Entity Name", ""),
                "members": row.get("Members", ""),
                "start_month": row.get("Start Month", ""),
                "duration_months": int(row.get("Duration Months", 1) or 1),
                "quota": float(row.get("Quota", 0) or 0.0),
                "total_billing": float(row.get("Total Billing", 0) or 0.0),
                "new_client_billing": float(row.get("New Client Billing", 0) or 0.0),
                "existing_client_billing": float(row.get("Existing Client Billing", 0) or 0.0),
                "achievement_pct": float(row.get("Achievement %", 0) or 0.0),
                "status": row.get("Status", ""),
                "clients_count": int(row.get("Clients Count", 0) or 0),
                "new_client_count": int(row.get("New Client Count", 0) or 0),
            }
        )

    with SessionLocal() as session:
        _write_table(session, QuotaAchievement, qa_rows)
        _write_table(session, Leaderboard, leaderboard_rows)
        _write_table(session, SalespersonBilling, sales_rows)
        session.commit()


def load_quota_achievement() -> pd.DataFrame:
    init_db()
    with SessionLocal() as session:
        rows = session.query(QuotaAchievement).all()
        return pd.DataFrame([r.__dict__ for r in rows]).drop(columns=["_sa_instance_state"], errors="ignore")


def load_leaderboard() -> pd.DataFrame:
    init_db()
    with SessionLocal() as session:
        rows = session.query(Leaderboard).order_by(Leaderboard.rank.asc()).all()
        return pd.DataFrame([r.__dict__ for r in rows]).drop(columns=["_sa_instance_state"], errors="ignore")


def load_salesperson_billing() -> pd.DataFrame:
    init_db()
    with SessionLocal() as session:
        rows = session.query(SalespersonBilling).all()
        return pd.DataFrame([r.__dict__ for r in rows]).drop(columns=["_sa_instance_state"], errors="ignore")
