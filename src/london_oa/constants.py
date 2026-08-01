"""Shared constants: coordinate systems, GSS codes, and GIS service endpoints."""

BNG = "EPSG:27700"
WGS84 = "EPSG:4326"

TOWER_HAMLETS = "E09000030"

# Greater London borough LAD (GSS) codes all start with this prefix.
LONDON_LAD_PREFIX = "E09"

OA_MAPSERVER = (
    "https://gis.london.gov.uk/arcgis/rest/services/apps/"
    "opportunity_areas_webmap/MapServer"
)
OA_ADOPTED_LAYER = 20  # OA_adopted -> the RED (formally adopted) polygons
OA_EMERGING_LAYER = 21
OA_TO_BE_DEFINED_LAYER = 22

BOROUGH_FEATURESERVER = (
    "https://services5.arcgis.com/1ZHcUS1lwPTg4ms0/arcgis/rest/services/"
    "London_Borough_Excluding_MHW/FeatureServer/0"
)

# Generous envelope around Tower Hamlets in British National Grid.
TH_BBOX = (532500, 178000, 541500, 185500)
