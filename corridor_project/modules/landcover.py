import sys
import numpy as np
import xarray as xr
import geopandas as gpd
import ee
import osmnx as ox
import pandas as pd
from rasterio import features
from typing import Dict, Any, Optional
sys.path.insert(1, '../../Hugo/a_b_c_functions/gee_with_python/')
from utils_gee import prepare_ds_xarray_ee

def get_city_landcover(
    aoi_ee: ee.Geometry, 
    aoi_raw: gpd.GeoDataFrame
) -> xr.DataArray:
    """
    Génère une carte d'occupation du sol fusionnant ESA WorldCover et OSM Highways.
    
    Args:
        aoi_ee (`ee.Geometry`): Emprise pour l'extraction Google Earth Engine.
        aoi_raw (`gpd.GeoDataFrame`): Polygone de la zone (utilisé pour l'EPSG et OSMnx).
        
    Returns:
        `xr.DataArray`: Raster fusionné projeté en UTM local.
    """

    # --- 0. Détermination de la projection locale ---
    # On utilise estimate_utm_crs() pour automatiser le choix de l'EPSG
    local_utm_crs = aoi_raw.estimate_utm_crs()
    utm_epsg: str = str(local_utm_crs)
    aoi_utm = aoi_raw.to_crs(utm_epsg)
    
    # --- 1. Extraction WorldCover ---
    wc_img: ee.Image = ee.ImageCollection('ESA/WorldCover/v200').mosaic()
    
    # Utilisation de la fonction de Hugo
    wc_xr: xr.Dataset = prepare_ds_xarray_ee(
        wc_img, 
        scale=10, 
        geometry=aoi_ee, 
        crs=utm_epsg
    ).compute()
    
    wc_data: xr.DataArray = wc_xr['Map'].squeeze()
    wc_data.rio.write_crs(utm_epsg, inplace=True)
    wc_data = wc_data.rio.clip(aoi_utm.geometry, aoi_utm.crs, all_touched=True, drop=True)

    # --- 2. Traitement Highways OSM ---
    # On utilise l'union_all() de aoi_raw pour OSMnx
    highways: gpd.GeoDataFrame = ox.features_from_polygon(
        aoi_raw.geometry.union_all(), 
        tags={"highway": True}
    )
    
    # Filtrage et reprojection en mètres (UTM) pour les buffers
    highways = highways[highways.geometry.type.isin(['LineString', 'MultiLineString'])].to_crs(utm_epsg)
    
    widths: Dict[str, int] = {
        'motorway': 20, 
        'trunk': 18, 
        'primary': 15, 
        'secondary': 12, 
        'tertiary': 10, 
        'residential': 8
    }
    
    # Calcul des emprises au sol
    highways['width'] = highways['highway'].apply(lambda x: widths.get(x, 4))
    highways['geometry'] = highways.geometry.buffer(highways['width'] / 2)
    
    # Préparation pour la rasterisation (code 51)
    highways_final = highways[['geometry']].copy()
    highways_final['wc_code'] = 51

    # --- 3. Fusion Landcover ---
    # Rasterisation des routes sur la grille WorldCover
    # On appelle rasterize_osm (qui doit être dans ton module lc)
    da_osm_raster: xr.DataArray = rasterize_osm(wc_data, highways_final)
    
    # Fusion finale : priorité aux routes (51)
    da_lc: xr.DataArray = xr.where(da_osm_raster == 51, 51, wc_data)
    da_lc.rio.write_crs(utm_epsg, inplace=True)
    
    return da_lc

def get_common_legend() -> Dict[int, str]:
    """
    Returns a standardized nomenclature to compare WorldCover and CosIA.
    Focuses on functional mobility classes for ecological connectivity.

    Returns:
        Dict[int, str]: Mapping of common landcover codes to class names.
    """
    return {
        10: "Trees",
        30: "Grassland/Shrub",
        40: "Agriculture",
        50: "Built-up",
        51: "Highways",  # OSM
        60: "Bare soil/Impervious",  # Open/Ground-level surfaces
        80: "Water"
    }

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
        'Broussaille': 30,        # Shrublands (20) not available
        'Pelouse': 30,            
        
        # --- Agriculture ---
        'Culture': 40,            
        'Terre labourée': 40,     
        'Vigne': 40,              
        
        # --- Water ---
        'Surface eau': 80,        
        'Piscine': 80,            
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
        30: 3, # Grassland
        10: 4, # Trees
        80: 5, # Water
        50: 6, # Built-up
        51: 7  # Highways
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

def rasterize_osm(wc_da: xr.DataArray, osm_gdf: gpd.GeoDataFrame) -> xr.DataArray:
    """
    Creates a raster containing OSM Highways.

    Args:
        wc_da (xr.DataArray): Template for spatial alignment.
        osm_gdf (gpd.GeoDataFrame): Road network vectors.

    Returns:
        xr.DataArray: Rasterized roads with code 51.
    """
    shapes = [(geom, 51) for geom in osm_gdf.geometry]
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
        name="osm_only"
    ).rio.write_crs(wc_da.rio.crs)

def compute_landcover_stats(
    da: xr.DataArray, 
    labels_map: Dict[int, str], 
    aoi_mask: Optional[xr.DataArray] = None
) -> pd.DataFrame:
    """
    Calculates surface areas (km2) for each landcover class.

    Args:
        da (xr.DataArray): Raster data to analyze.
        labels_map (Dict[int, str]): Legend for mapping codes to names.
        aoi_mask (Optional[xr.DataArray]): Optional mask to restrict analysis area.

    Returns:
        pd.DataFrame: Sorted table with pixel counts and area in km2.
    """
    if aoi_mask is not None:
        da = da.where(aoi_mask > 0)
        
    res_x, res_y = da.rio.resolution()
    pixel_area_km2 = abs(res_x * res_y) / 1e6
    
    # Calculate frequency
    counts = da.to_series().value_counts()
    stats = pd.DataFrame(counts).rename(columns={0: 'pixels', 'count': 'pixels'})
    stats['area_km2'] = stats['pixels'] * pixel_area_km2
    
    # Map index to class labels
    stats.index = stats.index.map(labels_map)
    
    return stats.drop(index=[np.nan], errors='ignore').sort_values(by='area_km2', ascending=False)