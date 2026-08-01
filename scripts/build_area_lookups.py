#!/usr/bin/env python3
"""Offline data prep: postcode -> borough / postcode -> Opportunity Area lookups
and simplified WGS84 boundary GeoJSONs for the static London planning map.

Usage
-----
    python scripts/build_area_lookups.py data/raw/ONSPD_FEB_2026/Data/ONSPD_FEB_2026_UK.csv
"""

import sys
from pathlib import Path

import geopandas as gpd

from london_oa.arcgis import fetch_adopted_oas, fetch_borough_boundaries
from london_oa.constants import BNG, LONDON_LAD_PREFIX, WGS84
from london_oa.postcodes import load_live_postcodes

DATA_DIR = Path("data")
SIMPLIFY_TOLERANCE_M = 10  # metres, in BNG - keeps the map snappy without visible distortion


def main(nspl_csv: str) -> None:
    print("fetching London borough boundaries...")
    boroughs = fetch_borough_boundaries()
    print(f"  {len(boroughs)} boroughs")

    print("fetching adopted Opportunity Area boundaries (London-wide)...")
    oas = fetch_adopted_oas(bbox=None)
    print(f"  {len(oas)} OA polygons, {oas['opportunityarea'].nunique()} distinct OAs")

    print("loading live London postcodes...")
    pc = load_live_postcodes(nspl_csv, lad_prefix=LONDON_LAD_PREFIX)
    print(f"  {len(pc):,} live postcodes")

    pts = gpd.GeoDataFrame(
        pc,
        geometry=gpd.points_from_xy(pc["east1m"], pc["north1m"]),
        crs=BNG,
    )

    name_by_code = dict(zip(boroughs["GSS_CODE"], boroughs["NAME"]))
    borough_lookup = pts[["pcds", "lad25cd"]].copy()
    borough_lookup["borough_name"] = borough_lookup["lad25cd"].map(name_by_code)
    borough_lookup = borough_lookup.dropna(subset=["borough_name"])
    borough_lookup.to_csv(DATA_DIR / "postcode_borough_lookup.csv", index=False)
    print(f"wrote postcode_borough_lookup.csv ({len(borough_lookup):,} rows)")

    hit = gpd.sjoin(
        pts[["pcds", "geometry"]],
        oas[["opportunityarea", "geometry"]],
        how="inner",
        predicate="within",
    )
    hit = hit.drop_duplicates(subset="pcds")
    oa_lookup = hit[["pcds", "opportunityarea"]]
    oa_lookup.to_csv(DATA_DIR / "postcode_oa_lookup.csv", index=False)
    print(f"wrote postcode_oa_lookup.csv ({len(oa_lookup):,} rows)")

    boroughs_out = boroughs.copy()
    boroughs_out["geometry"] = boroughs_out.geometry.simplify(SIMPLIFY_TOLERANCE_M)
    boroughs_out = boroughs_out.to_crs(WGS84)
    boroughs_out[["NAME", "GSS_CODE", "geometry"]].to_file(
        DATA_DIR / "london_borough_boundaries.geojson", driver="GeoJSON"
    )
    print("wrote london_borough_boundaries.geojson")

    oas_out = oas.copy()
    oas_out["geometry"] = oas_out.geometry.simplify(SIMPLIFY_TOLERANCE_M)
    oas_out = oas_out.to_crs(WGS84)
    keep_cols = [c for c in ["opportunityarea", "boroughs", "geometry"] if c in oas_out.columns]
    oas_out[keep_cols].to_file(DATA_DIR / "london_oa_boundaries.geojson", driver="GeoJSON")
    print("wrote london_oa_boundaries.geojson")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
