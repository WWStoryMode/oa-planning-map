"""Fetchers for the live GLA/London Datastore ArcGIS services."""

import geopandas as gpd
import requests

from .constants import BNG, BOROUGH_FEATURESERVER, OA_ADOPTED_LAYER, OA_MAPSERVER


def fetch_adopted_oas(bbox: tuple[float, float, float, float] | None = None) -> gpd.GeoDataFrame:
    """Pull adopted (red) Opportunity Area polygons.

    bbox is an (xmin, ymin, xmax, ymax) envelope in British National Grid.
    Pass None (default) to fetch every adopted OA across London.
    """
    params = {
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "f": "geojson",
    }
    if bbox is not None:
        params.update(
            {
                "geometry": ",".join(str(v) for v in bbox),
                "geometryType": "esriGeometryEnvelope",
                "inSR": "27700",
                "outSR": "27700",
                "spatialRel": "esriSpatialRelIntersects",
            }
        )
    else:
        params["outSR"] = "27700"

    r = requests.get(f"{OA_MAPSERVER}/{OA_ADOPTED_LAYER}/query", params=params, timeout=120)
    r.raise_for_status()
    gj = r.json()

    if "features" not in gj:
        raise RuntimeError(f"Unexpected response: {gj}")

    return gpd.GeoDataFrame.from_features(gj["features"], crs=BNG)


def fetch_borough_boundaries() -> gpd.GeoDataFrame:
    """Pull all 33 London borough boundary polygons (NAME, GSS_CODE + geometry)."""
    params = {
        "where": "1=1",
        "outFields": "NAME,GSS_CODE",
        "returnGeometry": "true",
        "outSR": "27700",
        "f": "geojson",
    }
    r = requests.get(f"{BOROUGH_FEATURESERVER}/query", params=params, timeout=120)
    r.raise_for_status()
    gj = r.json()

    if "features" not in gj:
        raise RuntimeError(f"Unexpected response: {gj}")

    return gpd.GeoDataFrame.from_features(gj["features"], crs=BNG)
