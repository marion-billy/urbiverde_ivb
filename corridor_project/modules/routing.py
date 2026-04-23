import numpy as np
import xarray as xr
import pandas as pd
import geopandas as gpd
from skimage.graph import MCP_Geometric
from shapely.geometry import LineString
from rasterio import features
from tqdm import tqdm
from typing import Dict, Any

def create_resistance_surface(
    raster_da: xr.DataArray, 
    friction_dict: dict[int, float], 
    default_cost: float = 100.0
    ) -> np.ndarray:
    """
    Traduit un raster d'occupation du sol en surface de coût pour MCP_Geometric.

    Les barrières imperméables sont encodées comme np.nan dans friction_dict :
        friction[xx] = np.nan  →  cost_matrix[raster == xx] = np.inf
    MCP_Geometric ne peut pas traverser np.inf.

    Args:
        raster_da    (xr.DataArray)    : raster d'occupation du sol georéférencé
        friction_dict (dict[int,float]): code → coût (np.nan pour barrières)
        default_cost (float)           : coût pour codes non définis (défaut 100)

    Returns:
        np.ndarray float32 : surface de coût (np.inf pour barrières et hors-AOI)
    """
    cost_matrix = np.full(raster_da.shape, default_cost, dtype=np.float32)

    for code, cost in friction_dict.items():
        mask = raster_da.values == code
        if pd.isna(cost):
            cost_matrix[mask] = np.inf
        else:
            cost_matrix[mask] = float(cost)

    # Hors AOI (NaN ou 0 dans le raster) → imperméable
    cost_matrix[np.isnan(raster_da.values) | (raster_da.values == 0)] = np.inf

    return cost_matrix
    
def compute_lcp_network(
    corridors_gdf: gpd.GeoDataFrame, 
    nodes_df: gpd.GeoDataFrame,
    raster_da: xr.DataArray, 
    friction_dict: Dict[int, float]
) -> gpd.GeoDataFrame:
    """
    Computes the Least Cost Path (LCP) between habitat patches.

    Args:
        corridors_gdf (gpd.GeoDataFrame): Corridors (theoretical straight lines).
        nodes_df (pd.DataFrame): Contain the 'geometry' column.
        raster_da (xr.DataArray): Georeferenced landcover grid used as a friction base.
        friction_dict (Dict[int, float]): Mapping of landcover codes to travel costs.

    Returns:
        gpd.GeoDataFrame: Real paths (LineString) with 'real_dist' and 'importance_score'.
    """
    
    # 1. Setup cost surface and MCP solver
    cost_matrix = create_resistance_surface(raster_da, friction_dict)
    mcp = MCP_Geometric(cost_matrix)
    affine_transform = raster_da.rio.transform()
    
    # 2. Pre-calculate patch masks (Vector to Raster coordinates)
    patch_masks = {}
    for idx, row in nodes_df.iterrows():
        mask = features.rasterize([(row.geometry, 1)], 
                                  out_shape=raster_da.shape, 
                                  transform=affine_transform)
        coords = np.argwhere(mask == 1)
        if len(coords) > 0:
            patch_masks[idx] = coords
            
    # 3. Trace LCPs
    lcp_results = []
    failed_links = 0

    for _, row in tqdm(corridors_gdf.iterrows(), total=len(corridors_gdf), desc="Tracing LCPs"):
        u, v = int(row['node_1']), int(row['node_2'])
        
        if u not in patch_masks or v not in patch_masks:
            failed_links += 1
            continue

        try:
            starts, ends = patch_masks[u], patch_masks[v]
            
            # Compute cumulative costs from all potential start pixels
            cumulative_costs, _ = mcp.find_costs(starts=starts, ends=ends)
            # Extract costs at destination pixels
            costs_at_ends = cumulative_costs[ends[:, 0], ends[:, 1]]
            # Connectivity check (threshold for unreachable areas)
            if np.all(costs_at_ends >= 1e9):
                failed_links += 1
                continue
            cost_at_end = np.min(costs_at_ends)

            # Identify best entry point in patch V and traceback
            best_end_idx = ends[np.argmin(costs_at_ends)]
            path_pixels = mcp.traceback(best_end_idx)
            
            path_coords = [affine_transform * (c, r) for r, c in path_pixels]
            
            if len(path_coords) >= 2:
                path_geom = LineString(path_coords)
                lcp_results.append({
                    'node_1': u,
                    'node_2': v,
                    'theoretical_dist': row['dist_m'],
                    'real_dist': path_geom.length,
                    'accumulated_cost': cost_at_end,
                    'efficiency': path_geom.length / cost_at_end if cost_at_end > 0 else 0, 
                    'geometry': path_geom
                })
            
        except Exception as e:
            print(f"Critical error on link {u}-{v}: {e}")
            raise e
            
    if not lcp_results:
        print(f"Failure: No LCPs could be traced out of {len(corridors_gdf)} attempts.")
        return gpd.GeoDataFrame(columns=['node_1', 'node_2', 'geometry'], crs=raster_da.rio.crs)

    print(f"Success: {len(lcp_results)} corridors traced ({failed_links} failed).")
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