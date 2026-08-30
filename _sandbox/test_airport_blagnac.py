"""
End-to-end sanity check: do airports come back from OSM and end up non-habitat?

Run this from a Jupyter kernel that already has Earth Engine initialized and the
project modules importable (i.e. any <city>_prod notebook). Paste the two cells
below into the notebook, or %run this file after the imports.

AOI = a ~5 km box around Toulouse-Blagnac airport (LFBO).
"""

# ---------------------------------------------------------------------------
# CELL 1 - OSM only (no Earth Engine needed): does OSMnx return the aerodrome?
# ---------------------------------------------------------------------------
import osmnx as ox
import geopandas as gpd
from shapely.geometry import box

# lon/lat box around Toulouse-Blagnac (LFBO)
aoi_raw = gpd.GeoDataFrame(geometry=[box(1.34, 43.61, 1.39, 43.65)], crs="EPSG:4326")

feats = ox.features_from_polygon(
    aoi_raw.geometry.union_all(),
    tags={
        "aeroway": ["aerodrome", "runway", "taxiway", "apron", "helipad"],
        "leisure": ["stadium", "pitch", "track", "sports_centre"],
    },
)
print("OSM features returned:", len(feats))
for col in ("aeroway", "leisure"):
    if col in feats.columns:
        print(f"\n{col} value_counts:")
        print(feats[col].value_counts(dropna=True))

aero_poly = feats[
    feats.get("aeroway").notna()
    & feats.geometry.type.isin(["Polygon", "MultiPolygon"])
]
print(f"\naeroway POLYGONS (what gets burned as code 50): {len(aero_poly)}")
# aero_poly.plot()  # uncomment to see the airport footprint


# ---------------------------------------------------------------------------
# CELL 2 - full pipeline slice (needs EE): airport -> code 50 -> NOT habitat
# ---------------------------------------------------------------------------
# import ee; ee.Initialize(project="YOUR-EE-PROJECT")   # already done in the notebook
import numpy as np
import landcover as lc
import connectivity as conn
import species_params as spp

aoi_utm, aoi_ee, utm_epsg = lc.setup_aoi(aoi_raw)
lc_wc, lc_osm = lc.download_lc_data(aoi_ee, aoi_utm, aoi_raw, utm_epsg)

n_airport = int((lc_osm["wc_code"] == 50).sum()) if "wc_code" in lc_osm.columns else 0
print(f"OSM artificial polygons burned as code 50: {n_airport}")

# open-ground guild (grass/bare-soil habitat) is the one that used to misclassify airports
habitat_codes = spp.SPECIES_CONFIG["ground_reptile"]["habitat_codes"]
da_lc = lc.generate_guild_landcover(lc_wc, lc_osm, aoi_raw, utm_epsg, habitat_codes)
binary = conn.get_binary_habitat(da_lc, habitat_codes)

# sample the runway centre (lon 1.3676, lat 43.6293) reprojected to the raster CRS
pt = gpd.GeoSeries.from_xy([1.3676], [43.6293], crs="EPSG:4326").to_crs(da_lc.rio.crs)
px, py = pt.x.iloc[0], pt.y.iloc[0]
code = int(da_lc.sel(x=px, y=py, method="nearest").item())
hab = int(binary.sel(x=px, y=py, method="nearest").item())
print(f"runway-centre pixel: land-cover code={code} (expect 50), habitat={hab} (expect 0)")

vals, cnts = np.unique(da_lc.values, return_counts=True)
print("land-cover histogram:", dict(zip(vals.tolist(), cnts.tolist())))
print("code 50 pixels:", int((da_lc.values == 50).sum()))
assert code == 50, "airport not burned as 50 - check OSM coverage / tags"
assert hab == 0, "airport still counted as habitat!"
print("OK: airport is land-cover 50 and excluded from habitat.")
