#!/usr/bin/env python3
"""Static map of City Fringe/Tech City postcodes with the adopted OA boundary."""

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

from london_oa.arcgis import fetch_adopted_oas
from london_oa.constants import BNG, TH_BBOX

OA_NAME = "City Fringe/Tech City"
POSTCODES_CSV = "tower_hamlets_red_oa_postcodes.csv"
OUT_PNG = "city_fringe_oa_map.png"


def main() -> None:
    oa = fetch_adopted_oas(bbox=TH_BBOX)
    oa = oa[oa["opportunityarea"] == OA_NAME]

    pc = pd.read_csv(POSTCODES_CSV)
    pc = pc[pc["opportunityarea"] == OA_NAME]
    pts = gpd.GeoDataFrame(
        pc,
        geometry=gpd.points_from_xy(pc["east1m"], pc["north1m"]),
        crs=BNG,
    )

    fig, ax = plt.subplots(figsize=(10, 10))
    oa.boundary.plot(ax=ax, color="crimson", linewidth=2)
    pts.plot(ax=ax, color="steelblue", markersize=6, alpha=0.6)

    ax.set_aspect("equal")
    ax.set_title(f"{OA_NAME} — Tower Hamlets Opportunity Area postcodes\n({len(pts):,} postcodes)")
    ax.set_xlabel("Easting (BNG, m)")
    ax.set_ylabel("Northing (BNG, m)")

    fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
