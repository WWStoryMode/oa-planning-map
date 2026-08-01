#!/usr/bin/env python3
"""Tower Hamlets approved:rejected ratio by year and Opportunity Area status,
annotated with UK Prime Minister tenure and the 2021 London Plan.

A full-dataset (all application types, 2016-2026) counterpart to Sharuga's
contributed analysis in analysis/contributed/sharuga-pm-opportunity-summary/,
built on this repo's existing pipeline rather than a hand-compiled subset.

Usage
-----
    python scripts/build_pm_stats.py \\
        --nspl data/raw/ONSPD_FEB_2026/Data/ONSPD_FEB_2026_UK.csv \\
        --db ~/Downloads/housing_planning.sqlite
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from london_oa.applications import derive_rates, load_applications, raw_counts
from london_oa.constants import TOWER_HAMLETS
from london_oa.pm_terms import PM_TERMS, pm_for_date
from london_oa.postcodes import load_live_postcodes, normalize_postcode

DATA_DIR = Path("data")
OUT_CSV = DATA_DIR / "tower_hamlets_pm_opportunity_summary.csv"
OUT_CHART = Path("analysis/tower_hamlets_pm_opportunity_ratio.png")
DEFAULT_DB = "~/Downloads/housing_planning.sqlite"
MIN_YEAR, MAX_YEAR = 2016, 2026

# Validated (dataviz skill categorical slots 1/2, light mode) - passes
# CVD separation, normal-vision floor, and contrast checks for a 2-series chart.
COLOR_OA = "#2a78d6"
COLOR_NON_OA = "#eb6834"


def build_rows(db_path: str, nspl_csv: str) -> pd.DataFrame:
    th = load_live_postcodes(nspl_csv, lad_codes={TOWER_HAMLETS})
    th_set = set(th["pcds"].map(normalize_postcode))

    oa_lookup = pd.read_csv(DATA_DIR / "postcode_oa_lookup.csv")
    oa_set = set(oa_lookup["pcds"].map(normalize_postcode))

    apps = load_applications(db_path)
    apps["postcode_norm"] = apps["postcode"].map(normalize_postcode)
    apps = apps[apps["postcode_norm"].isin(th_set)].copy()
    apps["app_state"] = apps["app_state"].fillna("")
    apps["year"] = apps["start_date"].str.slice(0, 4)
    apps = apps[apps["year"].between(str(MIN_YEAR), str(MAX_YEAR))]
    apps["pm"] = apps["start_date"].map(pm_for_date)
    apps["in_oa"] = apps["postcode_norm"].isin(oa_set)

    rows = []
    for (year, pm, in_oa), group in apps.groupby(["year", "pm", "in_oa"]):
        counts = derive_rates(raw_counts(group))
        ratio = (
            f"{counts['approved'] / counts['rejected']:.2f}:1"
            if counts["rejected"]
            else "Undefined"
        )
        rows.append(
            {
                "Year": year,
                "Prime Minister": pm,
                "Opportunity_Area": "Yes" if in_oa else "No",
                "Approved": counts["approved"],
                "Rejected": counts["rejected"],
                "Excluded": counts["excluded"],
                "Approved_to_Rejected_Ratio": ratio,
            }
        )
    return pd.DataFrame(rows).sort_values(["Year", "Prime Minister", "Opportunity_Area"])


def write_chart(df: pd.DataFrame, out_path: Path) -> None:
    yearly = (
        df.assign(Year=df["Year"].astype(int))
        .groupby(["Year", "Opportunity_Area"])[["Approved", "Rejected"]]
        .sum()
        .reset_index()
    )
    # A handful of rejected==0 cells (e.g. 2026 is a partial year) give an
    # infinite ratio - drop those points rather than let one cell blow out
    # the y-axis; the underlying counts are still in the CSV.
    yearly["ratio"] = yearly["Approved"] / yearly["Rejected"]
    yearly["ratio"] = yearly["ratio"].replace([float("inf"), float("-inf")], float("nan"))

    fig, ax = plt.subplots(figsize=(10, 6))
    series = [("Yes", "Opportunity Area", COLOR_OA), ("No", "Rest of borough", COLOR_NON_OA)]
    for oa_value, label, color in series:
        sub = yearly[yearly["Opportunity_Area"] == oa_value].sort_values("Year")
        ax.plot(
            sub["Year"], sub["ratio"], color=color, linewidth=2,
            marker="o", markersize=8, label=label,
        )
        last = sub.dropna(subset=["ratio"]).iloc[-1]
        ax.annotate(
            f"{last['ratio']:.1f}:1", (last["Year"], last["ratio"]),
            textcoords="offset points", xytext=(8, 4), fontsize=9, color=color,
        )

    ymax = yearly["ratio"].max() * 1.3
    # Stagger label heights (two tiers) so closely-spaced PM transitions
    # (e.g. Truss -> Sunak, 7 weeks apart) don't overlap.
    tiers = [ymax, ymax * 0.85]
    for i, (name, start) in enumerate(t for t in PM_TERMS if t[1] is not None):
        year = int(start[:4]) + int(start[5:7]) / 12
        if MIN_YEAR <= year <= MAX_YEAR:
            ax.axvline(year, color="#c3c2b7", linewidth=1, linestyle="--", zorder=0)
            ax.text(
                year, tiers[i % 2], name, rotation=90, fontsize=8, color="#52514e",
                ha="right", va="top",
            )

    ax.axvline(2021.3, color="#0b0b0b", linewidth=1.5, linestyle=":", zorder=0)
    ax.text(2021.3, ymax, " 2021 London Plan", fontsize=8, color="#0b0b0b", va="top")

    ax.set_ylim(0, ymax * 1.05)
    ax.set_xlabel("Year (application submitted)")
    ax.set_ylabel("Approved : rejected ratio")
    ax.set_title(
        "Tower Hamlets planning approval ratio by year\n"
        "Opportunity Area vs. rest of borough, all application types"
    )
    ax.legend(loc="lower left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main(db_path: str, nspl_csv: str) -> None:
    df = build_rows(db_path, nspl_csv)
    df.to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_CSV} ({len(df)} rows)")

    overall = df.groupby("Opportunity_Area")[["Approved", "Rejected"]].sum()
    for oa_value in ["Yes", "No"]:
        a, r = overall.loc[oa_value, "Approved"], overall.loc[oa_value, "Rejected"]
        print(f"OA={oa_value}: approved={a} rejected={r} ratio={a / r:.2f}:1")
    total_a, total_r = overall["Approved"].sum(), overall["Rejected"].sum()
    print(f"overall: approved={total_a} rejected={total_r} ratio={total_a / total_r:.2f}:1")

    OUT_CHART.parent.mkdir(exist_ok=True)
    write_chart(df, OUT_CHART)
    print(f"wrote {OUT_CHART}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nspl", required=True, help="Path to the ONSPD/NSPL UK CSV")
    parser.add_argument("--db", default=DEFAULT_DB, help="Path to housing_planning.sqlite")
    args = parser.parse_args()
    main(str(Path(args.db).expanduser()), args.nspl)
