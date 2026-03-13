"""
calculations.py
----------------
Quota-achievement calculations and status labelling (target based).
"""

import pandas as pd


def _parse_members(members_text: str) -> list[str]:
    if not members_text:
        return []
    return [part.strip() for part in str(members_text).split(",") if part.strip()]


def _window_end(start_dt: pd.Timestamp, duration_months: int) -> pd.Timestamp:
    return start_dt + pd.DateOffset(months=max(int(duration_months), 1) - 1)


def compute_achievement(raw_df: pd.DataFrame, quotas: pd.DataFrame) -> pd.DataFrame:
    """Compute achievement for each quota target row."""
    if quotas.empty:
        return pd.DataFrame(
            columns=[
                "Entity Type",
                "Entity Name",
                "Members",
                "Start Month",
                "Duration Months",
                "Quota",
                "Total Billing",
                "New Client Billing",
                "Existing Client Billing",
                "Achievement %",
                "Status",
                "Clients Count",
            ]
        )

    base = raw_df.copy()
    base["Month Date"] = pd.to_datetime(base["Month"], format="%b-%Y", errors="coerce")
    onboarding_col = "Client Onboarding Date" if "Client Onboarding Date" in base.columns else None
    if onboarding_col:
        base["Onboarding Date"] = pd.to_datetime(base[onboarding_col], errors="coerce")
        base["Onboarding Month"] = base["Onboarding Date"].dt.to_period("M").dt.to_timestamp()
    else:
        base["Onboarding Month"] = pd.NaT

    rows: list[dict] = []
    for target in quotas.to_dict("records"):
        entity_type = str(target.get("Entity Type", "Sales Person")).strip() or "Sales Person"
        entity_name = str(target.get("Entity Name", "")).strip()
        members_text = str(target.get("Members", "")).strip()
        start_month = str(target.get("Start Month", "")).strip()
        duration = int(pd.to_numeric(target.get("Duration Months", 1), errors="coerce") or 1)
        quota = float(pd.to_numeric(target.get("Quota", 0), errors="coerce") or 0)

        start_dt = pd.to_datetime(start_month, format="%b-%Y", errors="coerce")
        if pd.isna(start_dt):
            total_billing = 0.0
            new_billing = 0.0
            existing_billing = 0.0
            clients_count = 0
        else:
            end_dt = _window_end(start_dt, duration)
            in_window = base[(base["Month Date"] >= start_dt) & (base["Month Date"] <= end_dt)]

            if entity_type == "Sales Team":
                members = _parse_members(members_text)
                if members:
                    scoped = in_window[in_window["Sales Person"].isin(members)]
                elif "Sales Team" in in_window.columns:
                    scoped = in_window[in_window["Sales Team"].astype(str).str.strip() == entity_name]
                else:
                    scoped = in_window.iloc[0:0]
            else:
                scoped = in_window[in_window["Sales Person"].astype(str).str.strip() == entity_name]

            total_billing = float(scoped["Billing Amount"].sum())
            new_mask = scoped["Onboarding Month"].notna() & (scoped["Onboarding Month"] >= start_dt) & (scoped["Onboarding Month"] <= end_dt)
            new_billing = float(scoped.loc[new_mask, "Billing Amount"].sum())
            existing_billing = total_billing - new_billing
            clients_count = int(scoped["Client Name"].nunique()) if "Client Name" in scoped.columns else 0

        achievement_pct = round((total_billing / quota) * 100, 2) if quota > 0 else 0.0
        rows.append(
            {
                "Entity Type": entity_type,
                "Entity Name": entity_name,
                "Members": members_text,
                "Start Month": start_month,
                "Duration Months": duration,
                "Quota": quota,
                "Total Billing": total_billing,
                "New Client Billing": new_billing,
                "Existing Client Billing": existing_billing,
                "Achievement %": achievement_pct,
                "Status": _status_label(achievement_pct),
                "Clients Count": clients_count,
            }
        )

    return pd.DataFrame(rows)


def _status_label(pct: float) -> str:
    if pct >= 100:
        return "Achieved"
    elif pct >= 80:
        return "Almost Achieved"
    else:
        return "Not Achieved"


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
