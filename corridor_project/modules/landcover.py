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
    Prépare tous les formats d'AOI nécessaires à partir du GeoDataFrame brut.

    Args:
        aoi_raw (`gpd.GeoDataFrame`): Polygone de la zone d'étude en coordonnées géographiques).

    Returns:
        `tuple`: Contenant l'AOI projeté (`gpd.GeoDataFrame`), l'AOI Earth Engine (`ee.Geometry`) et l'EPSG (`str`).
    """
    utm_epsg = f"EPSG:{get_utm_epsg(gdf=aoi_raw)}"
    aoi_utm = aoi_raw.to_crs(utm_epsg)
    aoi_ee = geemap.gdf_to_ee(gdf_to_bbox(aoi_utm))
    
    return aoi_utm, aoi_ee, utm_epsg

def get_city_landcover(
    aoi_ee: ee.Geometry, 
    aoi_utm: gpd.GeoDataFrame,
    aoi_raw: gpd.GeoDataFrame,
    utm_epsg: str,
    habitat_codes: list
) -> xr.DataArray:
    """
    Génère une carte d'occupation du sol fusionnant ESA WorldCover et OSM Highways Railways + Buildings + Waterways
    
    Args:
        aoi_ee (`ee.Geometry`): Emprise pour l'extraction Google Earth Engine.
        aoi_utm (`gpd.GeoDataFrame`): Polygone de la zone projeté en UTM (utilisé pour le clip).
        aoi_raw (`gpd.GeoDataFrame`): Polygone source (utilisé pour son CRS natif lors de la requête OSMnx).
        utm_epsg (`str`): Code de projection locale pour les calculs de distance et la rasterisation.
        
    Returns:
        `xr.DataArray`: Raster fusionné projeté en UTM local.
    """
    # --- 1. Extraction WorldCover ---
    wc_img: ee.Image = ee.ImageCollection('ESA/WorldCover/v200').mosaic()
    wc_xr = prepare_ds_xarray_ee(wc_img, scale=10, geometry=aoi_ee, crs=utm_epsg).compute()
    wc_data: xr.DataArray = wc_xr['Map'].squeeze()
    wc_data.rio.write_crs(utm_epsg, inplace=True)
    wc_data = wc_data.rio.clip(aoi_utm.geometry, aoi_utm.crs, all_touched=True, drop=True)

    # --- 2. Traitement OSM ---
    ox.settings.requests_timeout = 600
    ox.settings.use_cache = True

    accepted_highways = [
    'motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary', 'primary_link', 
    'secondary', 'secondary_link', 'tertiary', 'tertiary_link', 'busway',
    'unclassified', 'road', 'residential',
    'pedestrian', 'path', 'footway', 'track', 'living_street', 'service'
    ]
    
    osm_features = ox.features_from_polygon(
        aoi_raw.geometry.union_all(), 
        tags={"highway": accepted_highways, "railway": ["rail", "tram"], "building": True, "natural": ["water"], "landuse": ["reservoir"]}
    )

    osm_proj = osm_features.to_crs(utm_epsg)
    
    lines = osm_proj[(osm_proj['highway'].notna() | osm_proj['railway'].notna()) & (osm_proj.geometry.type.isin(['LineString', 'MultiLineString']))].copy()
    buildings = osm_proj[osm_proj['building'].notna()].copy()
    waterways = osm_proj[
    ((osm_proj['natural'] == 'water') | (osm_proj['landuse'] == 'reservoir')) 
    & (osm_proj.geometry.type.isin(['Polygon', 'MultiPolygon']))
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
    
    # Calcul des emprises au sol
    lines['width'] = lines.apply(
        lambda row: widths.get(row.get('highway'), widths.get(row.get('railway'), 0)), 
        axis=1
    )
    lines = lines[lines['width'] > 0].copy()
    lines['geometry'] = lines.geometry.buffer(lines['width'] / 2)
    
    # Attribution des codes
    def assign_line_code(row):
        hw, rw = row.get('highway'), row.get('railway')
        if rw in ['rail', 'tram'] or hw in ['motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary', 'primary_link']: return 52
        if hw in ['secondary', 'secondary_link', 'tertiary', 'tertiary_link', 'unclassified', 'road', 'residential', 'busway']: return 53
        if hw in ['pedestrian', 'path', 'footway', 'track', 'living_street', 'service']: return 54
        return 0
    lines['wc_code'] = lines.apply(assign_line_code, axis=1)

    buildings['wc_code'] = 51

    waterways['wc_code'] = 80

    all_features = pd.concat([waterways, buildings, lines])
    custom_order = [80, 51, 52, 53, 54] 
    
    all_features['wc_order'] = pd.Categorical(
        all_features['wc_code'], 
        categories=custom_order, 
        ordered=True
    )
    all_features = all_features.sort_values('wc_order')

    # --- 3. Fusion Landcover ---
    da_osm_raster = rasterize_osm(wc_data, all_features)

    # 54 n'écrase que si ce n'est pas de l'habitat
    is_not_habitat = ~wc_data.isin(habitat_codes)
    # is_not_habitat = resample_raster(is_not_habitat, da_osm_raster)
    
    da_lc = xr.where((da_osm_raster == 54) & is_not_habitat, 54,
                xr.where(da_osm_raster == 53, 53,
                  xr.where(da_osm_raster == 52, 52,
                   xr.where(da_osm_raster == 51, 51, 
                    xr.where(da_osm_raster == 80, 80, 
                    wc_data)))))
    da_lc = da_lc.rio.write_crs(utm_epsg, inplace=True)
    
    return da_lc

def rasterize_osm(wc_da: xr.DataArray, osm_gdf: gpd.GeoDataFrame) -> xr.DataArray:
    """
    Creates a raster containing OSM Highways.

    Args:
        wc_da (xr.DataArray): Template for spatial alignment.
        osm_gdf (gpd.GeoDataFrame): Road network vectors.

    Returns:
        xr.DataArray: Rasterized roads with code 51 or 52.
    """
    shapes = [(geom, value) for geom, value in zip(osm_gdf.geometry, osm_gdf['wc_code'])]
    # raster_to_polygon
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
    Provides the translation table between CosIA strings and common codes.

    Returns:
        Dict[str, int]: CosIA class strings mapped to integer codes.
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
        'Broussaille': 30,        # Shrublands (20) not available, a perpi si!
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

def get_common_legend() -> Dict[int, str]:
    """
    Returns a standardized nomenclature to compare WorldCover and CosIA.
    Focuses on functional mobility classes for ecological connectivity.

    Returns:
        Dict[int, str]: Mapping of common landcover codes to class names.
    """
    return {
        10: "Trees",
        20: "Shrubland",
        30: "Grassland",
        40: "Agriculture",
        50: "Built-up",
        51: "Major roads",  # OSM
        52: "Minor roads",  # OSM
        60: "Bare soil/Impervious",  # Open/Ground-level surfaces
        80: "Water",
        90: "Wetlands",  # keep?
    }
    
def get_layer_priorities() -> Dict[int, int]:
    """
    Defines the stacking order for rasterization. 
    Higher values overwrite lower values.

    Returns:
        Dict[int, int]: Landcover codes mapped to their priority level.
    """
    return {
        60: 1, # Bare soil
        40: 2, # Cropland
        20: 3, # Shrubland
        30: 3, # Grassland
        10: 4, # Trees
        90: 5, # Wetlands to keep?
        80: 6, # Water
        50: 7, # Built-up
        52: 8, # Highways
        51: 9, # Highways
    }
    
def rasterize_cosia(wc_da: xr.DataArray, cosia_gdf: gpd.GeoDataFrame) -> xr.DataArray:
    """
    Creates a raster from CosIA data using WorldCover as a spatial template.

    Args:
        wc_da (xr.DataArray): The base WorldCover grid providing spatial metadata.
        cosia_gdf (gpd.GeoDataFrame): Vector data containing CosIA polygons.

    Returns:
        xr.DataArray: Rasterized CosIA data (pixels are 0 where no data exists).
    """
    mapping = get_cosia_mapping()
    priorities = get_layer_priorities()
    
    # Map, validate and sort by priority
    gdf = cosia_gdf.copy()
    gdf['wc_code'] = gdf['classe'].map(mapping)
    
    # Check for missing mappings
    if gdf['wc_code'].isnull().any():
        unmapped = gdf[gdf['wc_code'].isnull()]['classe'].unique()
        print(f"Warning: Classes not found in mapping: {unmapped}")

    gdf['priority'] = gdf['wc_code'].map(priorities)
    gdf = gdf.sort_values(by='priority')

    # Burn shapes into a numpy array
    shapes = [(geom, val) for geom, val in zip(gdf.geometry, gdf.wc_code)]
    rasterized = features.rasterize(
        shapes=shapes,
        out_shape=wc_da.shape,
        transform=wc_da.rio.transform(),
        fill=0,
        dtype='uint8'
    )
    
    return xr.DataArray(
        rasterized, 
        coords=wc_da.coords, 
        dims=wc_da.dims, 
        name="cosia_only"
    ).rio.write_crs(wc_da.rio.crs)

