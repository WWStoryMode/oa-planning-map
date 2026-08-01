#!/usr/bin/env python3
"""Tower Hamlets postcodes inside 'red' (adopted-boundary) Opportunity Areas,
using the LIVE layer behind https://apps.london.gov.uk/opportunity-areas/

Why this script exists: the GeoPackage from 2019 has only 28 adopted OAs and
no status field. The live service has all of them, split by status, so
'red only' is a real filter rather than an assumption.

Usage
-----
    python scripts/collect_oa_postcodes.py data/raw/ONSPD_FEB_2026/Data/ONSPD_FEB_2026_UK.csv
"""

import sys

import geopandas as gpd

from london_oa.arcgis import fetch_adopted_oas
from london_oa.constants import BNG, TH_BBOX, TOWER_HAMLETS
from london_oa.postcodes import load_live_postcodes


def main(nspl_csv: str) -> None:
    oa = fetch_adopted_oas(bbox=TH_BBOX)
    print(f"{len(oa)} adopted OAs intersect the Tower Hamlets envelope:")
    if "opportunityarea" in oa.columns:
        for n in sorted(oa["opportunityarea"].astype(str).unique()):
            print(f"   - {n}")

    pc = load_live_postcodes(nspl_csv, lad_codes={TOWER_HAMLETS})
    print(f"\n{len(pc):,} live Tower Hamlets postcodes")

    pts = gpd.GeoDataFrame(
        pc,
        geometry=gpd.points_from_xy(pc["east1m"], pc["north1m"]),
        crs=BNG,
    )

    hit = gpd.sjoin(pts, oa, how="inner", predicate="within")
    hit = hit.drop_duplicates(subset="pcds")      # OAs can overlap
    hit["postcode_district"] = hit["pcds"].str.split().str[0]
    hit = hit.sort_values("pcds")

    hit.drop(columns="geometry").to_csv(
        "tower_hamlets_red_oa_postcodes.csv", index=False
    )

    print(f"\n{len(hit):,} Tower Hamlets postcodes inside a RED (adopted) OA")
    print("\nBy district:")
    print(hit["postcode_district"].value_counts().to_string())
    print("\nwrote tower_hamlets_red_oa_postcodes.csv")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
