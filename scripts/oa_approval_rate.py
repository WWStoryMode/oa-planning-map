#!/usr/bin/env python3
"""Planning-application approval rate inside Tower Hamlets Opportunity Areas
vs. the rest of the borough.

Usage
-----
    python scripts/oa_approval_rate.py \\
        --nspl data/raw/ONSPD_FEB_2026/Data/ONSPD_FEB_2026_UK.csv \\
        --db ~/Downloads/housing_planning.sqlite
"""

import argparse
from pathlib import Path

import pandas as pd

from london_oa.applications import load_applications, summarize
from london_oa.constants import TOWER_HAMLETS
from london_oa.postcodes import load_live_postcodes, normalize_postcode

DEFAULT_DB = "~/Downloads/housing_planning.sqlite"
OA_POSTCODES_CSV = "tower_hamlets_red_oa_postcodes.csv"


def classify_group(postcode: str, oa_set: set, non_oa_set: set) -> str:
    if postcode in oa_set:
        return "OA"
    if postcode in non_oa_set:
        return "non_OA"
    return "unmatched"


def summarize_group(df: pd.DataFrame, label: str) -> None:
    stats = summarize(df)
    print(f"\n=== {label} ===")
    print(f"total applications:        {stats['total']:,}")
    print(f"  approved (Permitted/Conditions): {stats['approved']:,}")
    print(f"  rejected:                        {stats['rejected']:,}")
    print(f"  excluded (non-final state):      {stats['excluded']:,}")
    print(f"decided (approved+rejected): {stats['decided']:,}")
    print(f"approval rate:              {stats['approval_rate_pct']}%")
    if stats["approved_rejected_ratio"] is not None:
        print(f"approved:rejected ratio:    {stats['approved_rejected_ratio']}:1")


def main(nspl_csv: str, db_path: str) -> None:
    oa_df = pd.read_csv(OA_POSTCODES_CSV, usecols=["pcds"])
    oa_set = set(oa_df["pcds"].map(normalize_postcode))

    th_df = load_live_postcodes(nspl_csv, lad_codes={TOWER_HAMLETS})
    th_set = set(th_df["pcds"].map(normalize_postcode))
    non_oa_set = th_set - oa_set

    print(f"OA postcodes: {len(oa_set):,}")
    print(f"live Tower Hamlets postcodes: {len(th_set):,}")
    print(f"non-OA Tower Hamlets postcodes: {len(non_oa_set):,}")

    apps = load_applications(db_path, area_name="Tower Hamlets")
    apps["postcode_norm"] = apps["postcode"].map(normalize_postcode)
    apps["app_state"] = apps["app_state"].fillna("")
    apps["group"] = apps["postcode_norm"].apply(
        lambda pc: classify_group(pc, oa_set, non_oa_set)
    )

    print(f"\nraw Tower Hamlets applications: {len(apps):,}")
    print(apps["group"].value_counts().to_string())

    unmatched = apps[apps["group"] == "unmatched"]
    blank_pc = (unmatched["postcode_norm"] == "").sum()
    print(f"\nunmatched breakdown: blank/null postcode = {blank_pc:,}, "
          f"non-blank but unrecognized postcode = {len(unmatched) - blank_pc:,}")

    summarize_group(apps[apps["group"] == "OA"], "Opportunity Areas (all 3, Tower Hamlets)")
    summarize_group(apps[apps["group"] == "non_OA"], "Rest of Tower Hamlets (non-OA)")

    apps[["postcode", "app_state", "group"]].to_csv(
        "oa_approval_detail.csv", index=False
    )
    print("\nwrote oa_approval_detail.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nspl", required=True, help="Path to the ONSPD/NSPL UK CSV")
    parser.add_argument("--db", default=DEFAULT_DB, help="Path to housing_planning.sqlite")
    args = parser.parse_args()
    main(args.nspl, str(Path(args.db).expanduser()))
