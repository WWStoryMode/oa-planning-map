#!/usr/bin/env python3
"""Single batch query against housing_planning.sqlite + precompute approval stats
for every London borough and adopted Opportunity Area.

Usage
-----
    python scripts/build_stats.py --db ~/Downloads/housing_planning.sqlite
"""

import argparse
import json
from pathlib import Path

import pandas as pd

from london_oa.applications import load_applications, raw_counts
from london_oa.postcodes import normalize_postcode

DATA_DIR = Path("data")
DEFAULT_DB = "~/Downloads/housing_planning.sqlite"

# start_date is complete (zero nulls) and spans this range across the whole
# table; decided_date has ~7.7% nulls (undecided/withdrawn) plus a handful
# of pre-2016 outliers, so the year filter is keyed on submission year.
MIN_YEAR = 2016
MAX_YEAR = 2026


def build_group_year_stats(apps: pd.DataFrame, lookup: pd.DataFrame, key_col: str) -> dict:
    merged = apps.merge(lookup, on="postcode_norm", how="inner")
    stats: dict = {name: {} for name in lookup[key_col].unique()}
    for (name, year), group in merged.groupby([key_col, "year"]):
        stats.setdefault(name, {})[year] = raw_counts(group)
    return stats


def main(db_path: str) -> None:
    print("running single batch query against applications table...")
    apps = load_applications(db_path)
    print(f"  {len(apps):,} applications")
    apps["postcode_norm"] = apps["postcode"].map(normalize_postcode)
    apps["app_state"] = apps["app_state"].fillna("")
    apps["year"] = apps["start_date"].str.slice(0, 4)
    apps = apps[apps["year"].between(str(MIN_YEAR), str(MAX_YEAR))]

    borough_lookup = pd.read_csv(DATA_DIR / "postcode_borough_lookup.csv")
    borough_lookup["postcode_norm"] = borough_lookup["pcds"].map(normalize_postcode)

    oa_lookup = pd.read_csv(DATA_DIR / "postcode_oa_lookup.csv")
    oa_lookup["postcode_norm"] = oa_lookup["pcds"].map(normalize_postcode)

    print("computing borough stats by year...")
    borough_stats = build_group_year_stats(apps, borough_lookup, "borough_name")

    print("computing Opportunity Area stats by year...")
    oa_stats = build_group_year_stats(apps, oa_lookup, "opportunityarea")

    out = {
        "min_year": MIN_YEAR,
        "max_year": MAX_YEAR,
        "boroughs": borough_stats,
        "opportunity_areas": oa_stats,
    }
    with open(DATA_DIR / "area_stats.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote area_stats.json ({len(borough_stats)} boroughs, {len(oa_stats)} OAs, "
          f"years {MIN_YEAR}-{MAX_YEAR})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=DEFAULT_DB, help="Path to housing_planning.sqlite")
    args = parser.parse_args()
    main(str(Path(args.db).expanduser()))
