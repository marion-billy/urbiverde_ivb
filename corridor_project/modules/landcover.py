import numpy as np
import xarray as xr
import geopandas as gpd
import pandas as pd
from rasterio import features
from typing import Dict, Any, Optional

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