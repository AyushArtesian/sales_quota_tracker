"""
aggregator.py
-------------
Aggregation helpers for billing data (Sales Person focused).
"""

import pandas as pd


def aggregate_billing(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate total billing per Sales Person + Month."""
    agg = (
        df.groupby(["Sales Person", "Month"], as_index=False)
        .agg(
            **{
                "Total Billing": ("Billing Amount", "sum"),
                "Clients": ("Client Name", lambda x: ", ".join(sorted(x.unique()))),
            }
        )
    )
    return agg


def aggregate_by_salesperson(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate total billing per Sales Person (all months)."""
    return (
        df.groupby("Sales Person", as_index=False)
        .agg(**{"Total Billing": ("Billing Amount", "sum")})
        .sort_values("Total Billing", ascending=False)
    )


def aggregate_by_month(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate billing per Month (all sales persons)."""
    return (
        df.groupby("Month", as_index=False)
        .agg(**{"Total Billing": ("Billing Amount", "sum")})
        .sort_values("Month")
    )
