"""Loading and classifying planning applications from the housing_planning.sqlite export."""

import sqlite3

import pandas as pd

APPROVED_STATES = {"Permitted", "Conditions"}
REJECTED_STATES = {"Rejected"}


def load_applications(db_path: str, area_name: str | None = None) -> pd.DataFrame:
    """Load postcode + app_state for every application, optionally filtered by area_name.

    area_name matches the PlanIt scraper/portal name, not a borough - it's
    unreliable for area classification (missing boroughs, includes non-borough
    development corporations), so prefer joining the result against a
    postcode->area lookup instead of relying on this filter for anything but
    a quick single-area query.
    """
    query = (
        "SELECT json_extract(payload, '$.postcode') AS postcode, "
        "json_extract(payload, '$.app_state') AS app_state "
        "FROM applications"
    )
    params: tuple = ()
    if area_name is not None:
        query += " WHERE area_name = ?"
        params = (area_name,)

    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()
    return df


def summarize(df: pd.DataFrame) -> dict:
    """Approval summary for a DataFrame with an app_state column."""
    total = len(df)
    approved = int(df["app_state"].isin(APPROVED_STATES).sum())
    rejected = int(df["app_state"].isin(REJECTED_STATES).sum())
    excluded = total - approved - rejected
    decided = approved + rejected

    return {
        "total": total,
        "approved": approved,
        "rejected": rejected,
        "excluded": excluded,
        "decided": decided,
        "approval_rate_pct": round(approved / decided * 100, 1) if decided else None,
        "approved_rejected_ratio": round(approved / rejected, 2) if rejected else None,
    }
