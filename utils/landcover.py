import sys
import numpy as np
import xarray as xr
import geopandas as gpd
import ee
import geemap
import osmnx as ox
import pandas as pd
from rasterio import features
from typing import Dict, Any, Optional
sys.path.insert(1, '../../Hugo/a_b_c_functions/gee_with_python/')
from utils_gee import prepare_ds_xarray_ee
sys.path.insert(1, '../../Hugo/a_b_c_functions/spatial_analysis/')
from utils_proj import get_utm_epsg
from utils_vector import gdf_to_bbox
from utils_raster import *

def setup_aoi(aoi_raw: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, ee.Geometry, str]:
    """
    Prepare every AOI representation needed from the raw GeoDataFrame.

    Parameters
    ----------
    aoi_raw : gpd.GeoDataFrame
        Study-area polygon in geographic coordinates.

    Returns
    -------
    tuple of (gpd.GeoDataFrame, ee.Geometry, str)
        The projected AOI, the Earth Engine AOI, and the UTM EPSG code.
    """
    utm_epsg = f"EPSG:{get_utm_epsg(gdf=aoi_raw)}"
    aoi_utm = aoi_raw.to_crs(utm_epsg)
    aoi_ee = geemap.gdf_to_ee(gdf_to_bbox(aoi_utm))

    return aoi_utm, aoi_ee, utm_epsg

def download_lc_data(
    aoi_ee: ee.Geometry,
    aoi_utm: gpd.GeoDataFrame,
    aoi_raw: gpd.GeoDataFrame,
    utm_epsg: str
) -> tuple[xr.DataArray, gpd.GeoDataFrame]:
    """
    Download WorldCover and prepare OSM vectors (highways, railways, buildings, waterways) on the maximum extent.

    Run this ONCE before the ecoprofil loop.

    Parameters
    ----------
    aoi_ee : ee.Geometry
        Extent for the Google Earth Engine extraction.
    aoi_utm : gpd.GeoDataFrame
        Projected study-area polygon in UTM (used for the clip).
    aoi_raw : gpd.GeoDataFrame
        Source polygon (its native CRS is used for the OSMnx query).
    utm_epsg : str
        Local projection code for distance computations and rasterization.

    Returns
    -------
    tuple of (xr.DataArray, gpd.GeoDataFrame)
        The merged raster reprojected to local UTM, and the prepared OSM vectors.
    """
    # --- 1. WorldCover extraction ---
    wc_img: ee.Image = ee.ImageCollection('ESA/WorldCover/v200').mosaic()
    wc_xr = prepare_ds_xarray_ee(wc_img, scale=10, geometry=aoi_ee, crs=utm_epsg).compute()
    wc_data: xr.DataArray = wc_xr['Map'].squeeze()
    wc_data.rio.write_crs(utm_epsg, inplace=True)
    wc_data = wc_data.rio.clip(aoi_utm.geometry, aoi_utm.crs, all_touched=True, drop=True)

    # --- 2. OSM processing ---
    # Overpass endpoint left at the osmnx default (overpass-api.de): the osmnx HTTP cache key includes
    # the endpoint URL, so pointing to a mirror would miss the responses already cached by the baseline
    # notebook runs (data/cache). With the pinned edge buffer, every sensitivity run issues the SAME
    # query as the baseline and reuses that cache instead of re-hitting Overpass. Override with the
    # OSMNX_OVERPASS_URL env var only if a fresh (uncached) fetch is genuinely needed.
    import os as _os
    if _os.environ.get("OSMNX_OVERPASS_URL"):
        ox.settings.overpass_url = _os.environ["OSMNX_OVERPASS_URL"]
    ox.settings.requests_timeout = 600
    ox.settings.use_cache = True
    # Keep the OSM HTTP cache in the project data/cache slot (convention: nothing at the project
    # root) instead of osmnx's default "./cache" in the current working directory.
    ox.settings.cache_folder = "/home/jovyan/work/team/marion/corridor_project/data/cache"

    accepted_highways = [
    'motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary', 'primary_link',
    'secondary', 'secondary_link', 'tertiary', 'tertiary_link', 'busway',
    'unclassified', 'road', 'residential',
    'pedestrian', 'path', 'footway', 'track', 'living_street', 'service'
    ]

    osm_features = ox.features_from_polygon(
        aoi_raw.geometry.union_all(),
        tags={
            "highway": accepted_highways, "railway": ["rail", "tram"], "building": True,
            "natural": ["water"], "landuse": ["reservoir"],
            "aeroway": ["aerodrome", "runway", "taxiway", "apron", "helipad"],
            "leisure": ["stadium", "pitch", "track", "sports_centre"],
        }
    )

    osm_proj = osm_features.to_crs(utm_epsg)

    for col in ['highway', 'railway', 'building', 'natural', 'landuse', 'aeroway', 'leisure']:
        if col not in osm_proj.columns:
            osm_proj[col] = None

    has_highway = 'highway' in osm_proj.columns and osm_proj['highway'].notna().any()
    has_railway = 'railway' in osm_proj.columns and osm_proj['railway'].notna().any()

    mask_lines = (
        ((osm_proj.get('highway').notna() if has_highway else False) |
         (osm_proj.get('railway').notna() if has_railway else False))
        & (osm_proj.geometry.type.isin(['LineString', 'MultiLineString']))
    )
    lines = osm_proj[mask_lines].copy()

    buildings = osm_proj[osm_proj['building'].notna()].copy() if 'building' in osm_proj.columns and osm_proj['building'].notna().any() else gpd.GeoDataFrame(columns=['geometry', 'wc_code'], crs=utm_epsg)

    waterways = osm_proj[
        ((osm_proj['natural'] == 'water') | (osm_proj['landuse'] == 'reservoir')) &
        (osm_proj.geometry.type.isin(['Polygon', 'MultiPolygon']))
    ].copy()

    # Artificial managed surfaces (airports, stadiums, sports pitches). WorldCover maps
    # their grass as grassland (habitat); burn them as built-up (code 50, non-habitat for
    # every ecoprofil) to avoid the false positive. Polygons only (line runways are skipped).
    artificial = osm_proj[
        (osm_proj['aeroway'].notna() | osm_proj['leisure'].notna()) &
        (osm_proj.geometry.type.isin(['Polygon', 'MultiPolygon']))
    ].copy()

    widths: Dict[str, int] = {
        'motorway': 30, 'motorway_link': 30, 'rail': 30,
        'trunk': 30, 'trunk_link': 30, 'tram': 30,
        'primary': 30, 'primary_link': 30,
        'secondary': 20, 'secondary_link': 20,
        'tertiary': 20, 'tertiary_link': 20, 'busway': 20,
        'unclassified': 20, 'road': 20, 'residential': 20,
        'pedestrian': 10, 'path': 10, 'footway': 10, 'track': 10, 'living_street': 10, 'service': 10
    }

    # Ground footprint computation
    lines['width'] = lines.apply(
        lambda row: widths.get(row.get('highway'), widths.get(row.get('railway'), 0)),
        axis=1
    )
    lines = lines[lines['width'] > 0].copy()
    lines['geometry'] = lines.geometry.buffer(lines['width'] / 2)

    # Code assignment
    def assign_line_code(row):
        hw, rw = row.get('highway'), row.get('railway')
        if hw in ['motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary', 'primary_link']: return 52
        if hw in ['secondary', 'secondary_link', 'tertiary', 'tertiary_link', 'unclassified', 'road', 'residential', 'busway']: return 53
        if hw in ['pedestrian', 'path', 'footway', 'track', 'living_street', 'service']: return 54
        if rw in ['rail', 'tram']: return 55
        return 0
    lines['wc_code'] = lines.apply(assign_line_code, axis=1)

    buildings['wc_code'] = 51
    waterways['wc_code'] = 80
    artificial['wc_code'] = 50

    for df in [waterways, buildings, lines, artificial]:
        if 'wc_code' not in df.columns:
            df['wc_code'] = 0
    all_features = pd.concat([waterways, buildings, lines, artificial])
    if all_features.empty:
        return wc_data, gpd.GeoDataFrame(crs=utm_epsg)

    # 50 (artificial) first = lowest priority: water/buildings/roads/rail/paths inside an
    # airport or stadium still win; only the managed grass becomes 50.
    custom_order = [50, 80, 51, 52, 53, 55, 54]
    all_features['wc_order'] = pd.Categorical(all_features['wc_code'], categories=custom_order, ordered=True)
    all_features = all_features.sort_values('wc_order')

    return wc_data, all_features

def generate_ecoprofil_landcover(
    lc_wc: xr.DataArray,
    lc_osm: gpd.GeoDataFrame,
    aoi_buffered: gpd.GeoDataFrame,
    utm_epsg: str,
    habitat_codes: list
) -> xr.DataArray:
    """
    Clip the maximum-buffer land cover to the ecoprofil extent and burn the OSM vectors onto it.

    Parameters
    ----------
    lc_wc : xr.DataArray
        WorldCover raster extracted on the maximum buffer extent.
    lc_osm : gpd.GeoDataFrame
        OSM vectors (roads, rail, buildings, water) on the maximum extent.
    aoi_buffered : gpd.GeoDataFrame
        Ecoprofil buffer used to clip the land cover.
    utm_epsg : str
        Local UTM projection code.
    habitat_codes : list
        Land-cover codes considered as habitat for the ecoprofil.

    Returns
    -------
    xr.DataArray
        Ecoprofil-specific land-cover raster (WorldCover with OSM infrastructure burned in).
    """
    aoi_utm = aoi_buffered.to_crs(utm_epsg)
    wc_clipped = lc_wc.rio.clip(aoi_utm.geometry.values, aoi_utm.crs, all_touched=True, drop=True)
    if lc_osm.empty:
        return wc_clipped
    osm_clipped = gpd.clip(lc_osm, aoi_utm)
    osm_clipped = osm_clipped.sort_values('wc_order')
    da_osm_raster = rasterize_osm(wc_clipped, osm_clipped)

    # Code 54 only overwrites when the pixel is not habitat
    is_not_habitat = ~wc_clipped.isin(habitat_codes)

    da_lc = xr.where((da_osm_raster == 54) & is_not_habitat, 54,
                xr.where(da_osm_raster == 55, 55,
                    xr.where(da_osm_raster == 53, 53,
                      xr.where(da_osm_raster == 52, 52,
                       xr.where(da_osm_raster == 51, 51,
                        xr.where(da_osm_raster == 80, 80,
                         xr.where(da_osm_raster == 50, 50,
                    wc_clipped)))))))

    da_lc = da_lc.rio.write_crs(utm_epsg, inplace=True)
    return da_lc

def rasterize_osm(wc_da: xr.DataArray, osm_gdf: gpd.GeoDataFrame) -> xr.DataArray:
    """
    Create a raster containing OSM infrastructure.

    Parameters
    ----------
    wc_da : xr.DataArray
        Template for spatial alignment.
    osm_gdf : gpd.GeoDataFrame
        Infrastructure vectors carrying a `wc_code` column.

    Returns
    -------
    xr.DataArray
        Rasterized infrastructure (values from `wc_code`).
    """
    shapes = [(geom, value) for geom, value in zip(osm_gdf.geometry, osm_gdf['wc_code'])]
    rasterized = features.rasterize(
        shapes=shapes,
        out_shape=wc_da.shape,
        transform=wc_da.rio.transform(),
        fill=0,
        dtype='uint8',
    )
    return xr.DataArray(
        rasterized,
        coords=wc_da.coords,
        dims=wc_da.dims
    ).rio.write_crs(wc_da.rio.crs)

#######################################
#######################################
## RESEARCH AND LANDCOVER COMPARISON ##
#######################################
#######################################

def get_cosia_mapping() -> Dict[str, int]:
    """
    Provide the translation table between CosIA strings and common codes.

    Note: dictionary keys are the verbatim CosIA class labels (data values), so
    they are kept in their original language.

    Returns
    -------
    Dict[str, int]
        CosIA class strings mapped to integer codes.
    """
    return {
        # --- Built Environment ---
        'Bâtiment': 50,
        'Serre': 50,
        'Highway': 51,

        # --- Open / Bare Soil ---
        'Zone imperméable': 60,   # Categorized as Bare Soil for friction purposes, but 50 is also an option ?
        'Zone perméable': 60,
        'Sol nu': 60,
        'Neige': 60,

        # --- Vegetation ---
        'Conifère': 10,
        'Feuillu': 10,
        'Broussaille': 20,
        'Pelouse': 30,

        # --- Agriculture ---
        'Culture': 40,
        'Terre labourée': 40,
        'Vigne': 40,

        # --- Water ---
        'Surface eau': 80,
        'Piscine': 80,

        # --- Wetlands 90 ---
    }
