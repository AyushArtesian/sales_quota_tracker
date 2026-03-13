"""
calculations.py
----------------
Quota-achievement calculations and status labelling.
"""

import pandas as pd


def compute_achievement(billing_agg: pd.DataFrame, quotas: pd.DataFrame) -> pd.DataFrame:
    """Merge billing aggregates with quotas and compute achievement metrics."""
    merged = billing_agg.merge(quotas, on=["Client Name", "Month"], how="left")
    merged["Quota"] = merged["Quota"].fillna(0)

    # Achievement %
    merged["Achievement %"] = merged.apply(
        lambda r: round((r["Total Billing"] / r["Quota"]) * 100, 2) if r["Quota"] > 0 else 0.0,
        axis=1,
    )

    # Status
    merged["Status"] = merged["Achievement %"].apply(_status_label)

    return merged


def _status_label(pct: float) -> str:
    if pct >= 100:
        return "✅ Achieved"
    elif pct >= 80:
        return "🟡 Almost Achieved"
    else:
        return "❌ Not Achieved"


def overall_metrics(achievement_df: pd.DataFrame) -> dict:
    """Return top-level KPIs."""
    total_billing = achievement_df["Total Billing"].sum()
    total_quota = achievement_df["Quota"].sum()
    overall_pct = round((total_billing / total_quota) * 100, 2) if total_quota > 0 else 0.0
    return {
        "total_billing": total_billing,
        "total_quota": total_quota,
        "overall_achievement": overall_pct,
    }
