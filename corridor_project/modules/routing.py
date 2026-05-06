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
    ) -> xr.DataArray:  
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
        DataArray : surface de coût (np.inf pour barrières et hors-AOI)
    """
    
    # 1. Création de la matrice de coût
    cost_matrix = np.full(raster_da.shape, default_cost, dtype=np.float32)

    for code, cost in friction_dict.items():
        mask = raster_da.values == code
        if pd.isna(cost):
            cost_matrix[mask] = np.inf
        else:
            cost_matrix[mask] = float(cost)

    # Hors AOI (NaN ou 0 dans le raster) → imperméable
    cost_matrix[np.isnan(raster_da.values) | (raster_da.values == 0)] = np.inf

    # 2. Conversion en xarray (Spatialisant le résultat)
    resistance_da = xr.DataArray(
        cost_matrix,
        coords=raster_da.coords,
        dims=raster_da.dims,
        name="resistance_surface",
        attrs=raster_da.attrs
    )
    
    # On force l'écriture du CRS pour être sûr qu'il est bien conservé
    resistance_da = resistance_da.rio.write_crs(raster_da.rio.crs)
    
    return resistance_da

def compute_lcp_network(
    corridors_gdf: gpd.GeoDataFrame, 
    nodes_df: gpd.GeoDataFrame,
    raster_da: xr.DataArray, 
    friction_dict: Dict[int, float],
    max_cost_threshold: float = None
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
    resistance_da = create_resistance_surface(raster_da, friction_dict) 
    mcp = MCP_Geometric(resistance_da.values) 
    affine_transform = raster_da.rio.transform()
    
    # 2. Pre-calculate patch masks (Vector to Raster coordinates)
    patch_masks = {}
    for idx, row in tqdm(nodes_df.iterrows(), total=len(nodes_df), desc="Rasterizing patches"):
        mask = features.rasterize([(row.geometry, 1)], 
                                  out_shape=raster_da.shape, 
                                  transform=affine_transform)
        coords = np.argwhere(mask == 1)
        if len(coords) > 0:
            patch_masks[idx] = coords
            
    # 3. Trace LCPs
    all_paths = []

    for _, row in tqdm(corridors_gdf.iterrows(), total=len(corridors_gdf), desc="Tracing LCPs"):
        u, v = int(row['node_1']), int(row['node_2'])
        
        # Initialisation par défaut (échec)
        path_data = {
            'node_1': u, 'node_2': v,
            'theoretical_dist': row['dist_m'],
            'geometry': row['geometry'], # La ligne droite théorique
            'status': 'failed',
            'fail_reason': 'node_not_found', # Raison par défaut
            'real_dist': np.nan,
            'accumulated_cost': np.nan,
            'efficiency': np.nan
        }
        
        # Tentative de calcul
        if u in patch_masks and v in patch_masks:
            try:
                starts, ends = patch_masks[u], patch_masks[v]
                cumulative_costs, _ = mcp.find_costs(starts=starts, ends=ends)
                costs_at_ends = cumulative_costs[ends[:, 0], ends[:, 1]]

                if np.all(costs_at_ends >= 1e9):
                    path_data['fail_reason'] = 'uncrossable_barrier'
                else:
                    cost_at_end = np.min(costs_at_ends)
                    best_end_idx = ends[np.argmin(costs_at_ends)]
                    path_pixels = mcp.traceback(best_end_idx)
                    path_coords = [affine_transform * (c, r) for r, c in path_pixels]
                    
                    if len(path_coords) >= 2:
                        path_geom = LineString(path_coords)
                        path_data.update({
                            'real_dist': path_geom.length,
                            'accumulated_cost': cost_at_end,
                            'efficiency': path_geom.length / cost_at_end if cost_at_end > 0 else 0,
                            'geometry': path_geom,
                            'status': 'success',
                            'fail_reason': None
                        })
            except Exception as e:
                path_data['fail_reason'] = f'error: {str(e)}'
        
        all_paths.append(path_data)

    gdf_final = gpd.GeoDataFrame(all_paths, crs=raster_da.rio.crs)

    if max_cost_threshold is not None:
        too_expensive_mask = (gdf_final['status'] == 'success') & \
                             (gdf_final['accumulated_cost'] > max_cost_threshold)
        gdf_final.loc[too_expensive_mask, 'status'] = 'failed'
        gdf_final.loc[too_expensive_mask, 'fail_reason'] = 'cost_threshold_exceeded'
        
    success_count = len(gdf_final[gdf_final['status'] == 'success'])
    print(f"Terminé: {success_count} success, {len(gdf_final) - success_count} failed.")
    if 'fail_reason' in gdf_final.columns:
        print(gdf_final[gdf_final['status'] == 'failed']['fail_reason'].value_counts())
        
    return gdf_final

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