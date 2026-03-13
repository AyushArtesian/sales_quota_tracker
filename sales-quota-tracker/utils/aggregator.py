"""
aggregator.py
-------------
Aggregation helpers for billing data.
"""

import pandas as pd


def aggregate_billing(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate total billing per Client + Month, preserving Sales Person."""
    agg = (
        df.groupby(["Client Name", "Month"], as_index=False)
        .agg(
            **{
                "Total Billing": ("Billing Amount", "sum"),
                "Sales Person": ("Sales Person", "first"),
                "Freelancer": ("Freelancer", lambda x: ", ".join(sorted(x.unique()))),
            }
        )
    )
    return agg


def aggregate_by_salesperson(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate billing per Sales Person."""
    return (
        df.groupby("Sales Person", as_index=False)
        .agg(**{"Total Billing": ("Billing Amount", "sum")})
        .sort_values("Total Billing", ascending=False)
    )


def aggregate_by_month(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate billing per Month."""
    return (
        df.groupby("Month", as_index=False)
        .agg(**{"Total Billing": ("Billing Amount", "sum")})
        .sort_values("Month")
    )
