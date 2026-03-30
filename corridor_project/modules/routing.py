import numpy as np
import xarray as xr
import pandas as pd
import geopandas as gpd
from skimage.graph import MCP_Geometric
from shapely.geometry import LineString
from tqdm import tqdm
from typing import Dict, Any

def create_resistance_surface(
    raster_da: xr.DataArray, 
    friction_dict: dict[int, float], 
    default_cost: int = 1000
) -> np.ndarray:
    """
    Translates a LandCover DataArray into a cost surface (friction map).
    
    Args:
        raster_da (xr.DataArray): The augmented landcover grid (georeferenced).
        friction_dict (dict[int, float]): Mapping of landcover codes to travel costs.
        default_cost (int, optional): Cost for undefined or NaN pixels. Defaults to 1000.
    
    Returns:
        np.ndarray: A 2D friction matrix compatible with MCP algorithms.
    """
    # Initialize with default high cost (impassable)
    cost_matrix = np.full(raster_da.shape, default_cost, dtype=np.float32)
    
    # Map each landcover code to its friction value
    for code, cost in friction_dict.items():
        mask = (raster_da.values == code)
        cost_matrix[mask] = cost
        
    # Handle NaNs and 0 (no data) as impassable
    cost_matrix[np.isnan(raster_da.values) | (raster_da.values == 0)] = default_cost
    
    return cost_matrix

def compute_lcp_network(
    corridors_gdf: gpd.GeoDataFrame, 
    nodes_df: pd.DataFrame, 
    raster_da: xr.DataArray, 
    friction_dict: Dict[int, float]
) -> gpd.GeoDataFrame:
    """
    Computes the Least Cost Path (LCP) for a set of priority corridors.

    Args:
        corridors_gdf (gpd.GeoDataFrame): Priority corridors (theoretical straight lines).
        nodes_df (pd.DataFrame): Patch centroids with 'x' and 'y' coordinates.
        raster_da (xr.DataArray): Georeferenced landcover grid used as a friction base.
        friction_dict (Dict[int, float]): Mapping of landcover codes to travel costs.

    Returns:
        gpd.GeoDataFrame: Real paths (LineString) with 'real_dist' and 'importance_score'.
    """
    # 1. Prepare cost surface
    cost_matrix = create_resistance_surface(raster_da, friction_dict)
    # MCP_Geometric allows diagonal movement with correct distance weighting
    mcp = MCP_Geometric(cost_matrix)
    
    # 2. Setup coordinate transformation (UTM -> Pixel)
    inv_transform = ~raster_da.rio.transform()
    
    lcp_results = []

    # Iteration over priority corridors
    for _, row in tqdm(corridors_gdf.iterrows(), total=len(corridors_gdf), desc="Tracing LCPs"):
        u, v = int(row['node_1']), int(row['node_2'])

        try:
            # Get centroids from nodes_df
            p1_utm = (nodes_df.loc[u, 'x'], nodes_df.loc[u, 'y'])
            p2_utm = (nodes_df.loc[v, 'x'], nodes_df.loc[v, 'y'])
   
            # Transform UTM to Pixel (Col, Row)
            start_px = inv_transform * p1_utm
            end_px = inv_transform * p2_utm
            
            # MCP expects integer indices (Row, Col)
            start_idx = (int(start_px[1]), int(start_px[0]))
            end_idx = (int(end_px[1]), int(end_px[0]))
            
            # Compute path
            mcp.find_costs(starts=[start_idx], ends=[end_idx])
            path_pixels = mcp.traceback(end_idx) # Returns list of (row, col)
            
            # Transform back to UTM for GeoDataFrame
            path_utm = [raster_da.rio.transform() * (c, r) for r, c in path_pixels]
            
            # Create geometry and calculate real length
            path_geom = LineString(path_utm)
            
            lcp_results.append({
                'node_1': u,
                'node_2': v,
                'importance_score': row['importance_score'],
                'theoretical_dist': row['dist_m'],
                'real_dist': path_geom.length,
                'geometry': path_geom
            })
            
        except Exception:
            # Safety if points fall outside the raster bounds
            continue

    return gpd.GeoDataFrame(lcp_results, crs=raster_da.rio.crs)

def calculate_tortuosity(lcp_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Calculates the Tortuosity Index: Ratio of Real Distance / Theoretical Distance.
    A value of 1.0 means a straight path. Higher values indicate constraints.

    Args:
        lcp_gdf (gpd.GeoDataFrame): GeoDataFrame containing 'real_dist' and 'theoretical_dist'.

    Returns:
        gpd.GeoDataFrame: Input GeoDataFrame with an additional 'tortuosity' column.
    """
    lcp_gdf['tortuosity'] = lcp_gdf['real_dist'] / lcp_gdf['theoretical_dist']
    return lcp_gdf