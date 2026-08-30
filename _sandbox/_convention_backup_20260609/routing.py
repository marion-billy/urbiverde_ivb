import numpy as np
import xarray as xr
import pandas as pd
import geopandas as gpd
from skimage.graph import MCP_Geometric
from shapely.geometry import LineString, MultiLineString, MultiPolygon
from shapely.validation import make_valid
from shapely import set_precision
from rasterio import features
from tqdm import tqdm
from typing import Dict, Any
import sys
# Smoothing dep. `geoai.smooth_vector` was only a thin wrapper around `smoothify`,
# so we depend on smoothify directly and drop the former 6.6 GB `my_custom_libs/`
# geoai (PyTorch/CUDA) stack. smoothify is installed under the project `libs/` on
# the NFS volume so it survives the ephemeral container.
custom_dir = '/home/jovyan/work/team/marion/corridor_project/libs'
if custom_dir not in sys.path:
    sys.path.insert(0, custom_dir)
from smoothify import smoothify
# NB: this module defines its own `safe_smooth` / `safe_smooth_lines` below; it no
# longer imports the geoai-dependent canonical `safe_smooth` from a_b_c_functions.

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
        max_cost_threshold (float): Max accumulated_cost in friction × metres.

    Returns:
        gpd.GeoDataFrame: Real paths (LineString) with 'real_dist' and 'accumulated_cost'.
    """

    # 1. Setup cost surface and MCP solver
    resistance_da = create_resistance_surface(raster_da, friction_dict) 
    transform = raster_da.rio.transform()
    pixel_size_x = abs(transform.a)
    pixel_size_y = abs(transform.e)
    mcp = MCP_Geometric(resistance_da.values, sampling=(pixel_size_y, pixel_size_x))
    
    # 2. Pre-calculate patch masks (Vector to Raster coordinates)
    patch_masks = {}
    for idx, row in tqdm(nodes_df.iterrows(), total=len(nodes_df), desc="Rasterizing patches"):
        mask = features.rasterize(
            [(row.geometry.boundary, 1)], 
            out_shape=raster_da.shape, 
            transform=transform,
            all_touched=True
        )
        coords = np.argwhere(mask == 1)

        # Sécurité : si le polygone passe entre les mailles du raster, on se rabat sur son centroïde.
        if len(coords) == 0:
            mask = features.rasterize([(row.geometry.centroid, 1)], out_shape=raster_da.shape, transform=transform)
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
                cumulative_costs, _ = mcp.find_costs(starts=starts, ends=ends, find_all_ends=False)
                costs_at_ends = cumulative_costs[ends[:, 0], ends[:, 1]]

                if np.all(costs_at_ends >= 1e9):
                    path_data['fail_reason'] = 'uncrossable_barrier'
                else:
                    cost_at_end = np.min(costs_at_ends)
                    best_end_idx = ends[np.argmin(costs_at_ends)]
                    path_pixels = mcp.traceback(best_end_idx)
                    path_coords = [transform * (c, r) for r, c in path_pixels]
                    
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

def safe_smooth(gdf, **kwargs):
    """
    Apply smoothing with strict sanitation to prevent 'ufunc create_collection' errors.
    Preserves original indices to prevent silent downstream graph mapping errors.
    Includes tqdm progress bar.
    """
    results = []
    
    # Wrap the iterator with tqdm for a progress bar
    # 'total' gives it the denominator for the percentage, 'desc' adds a label
    for idx, row in tqdm(gdf.iterrows(), total=len(gdf), desc="Smoothing nodes"):
        geom = row.geometry
        
        # --- Step 1: Sanitation Checks ---
        
        if geom is None or geom.is_empty:
            continue  # Skip empty geometries
            
        if not geom.is_valid:
            geom = make_valid(geom)
            
        try:
            if np.isnan(geom.bounds).any():
                # tqdm.write() prevents print statements from breaking the progress bar visually
                tqdm.write(f"Skipping ID {idx}: Geometry contains NaN coordinates.")
                continue
        except Exception:
            tqdm.write(f"Skipping ID {idx}: Geometry is deeply corrupt.")
            continue

        if geom.geom_type == 'GeometryCollection':
            parts = [g for g in geom.geoms if g.geom_type in ['Polygon', 'MultiPolygon']]
            if not parts:
                continue
            geom = MultiPolygon(parts) if len(parts) > 1 else parts[0]
        elif geom.geom_type not in ['Polygon', 'MultiPolygon']:
            continue

        # Update the row geometry with the sanitized version
        row_copy = row.copy()
        row_copy.geometry = geom
        
        # Explicitly pass the original index to retain it
        single_gdf = gpd.GeoDataFrame([row_copy], index=[idx], crs=gdf.crs)

        # --- Step 2: Attempt Smoothing ---
        try:
            # geoai.smooth_vector was a thin wrapper around smoothify (same defaults)
            smoothed = smoothify(geom=single_gdf, **kwargs)
            
            if not smoothed.empty and not smoothed.geometry.is_empty.all():
                smoothed.index = [idx] 
                results.append(smoothed)
            else:
                raise ValueError("Smoothing returned empty geometry")

        except Exception as e:
            tqdm.write(f"Warning: Could not smooth geometry {idx}. Error: {e}")
            
            try:
                row_copy.geometry = row_copy.geometry.buffer(0)
                results.append(gpd.GeoDataFrame([row_copy], index=[idx], crs=gdf.crs))
            except Exception:
                tqdm.write(f"Critical: Could not recover geometry {idx} even with fallback.")

    if not results:
        return gpd.GeoDataFrame(columns=gdf.columns, crs=gdf.crs)

    # Concatenate while keeping the original indices
    return pd.concat(results, ignore_index=False)

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

def anchor_endpoints(raw_geom, smooth_geom):
    """
    Forces the smoothed line to start and end exactly where the raw line did,
    restoring network connectivity at junctions and habitat borders.
    """
    try:
        if raw_geom.geom_type == 'LineString' and smooth_geom.geom_type == 'LineString':
            raw_coords = list(raw_geom.coords)
            smooth_coords = list(smooth_geom.coords)
            
            # Snap the first and last vertices back to their original positions
            smooth_coords[0] = raw_coords[0]
            smooth_coords[-1] = raw_coords[-1]
            
            return LineString(smooth_coords)
            
        elif raw_geom.geom_type == 'MultiLineString' and smooth_geom.geom_type == 'MultiLineString':
            # If it's a MultiLineString, try to anchor each part
            if len(raw_geom.geoms) == len(smooth_geom.geoms):
                anchored_parts = []
                for r_part, s_part in zip(raw_geom.geoms, smooth_geom.geoms):
                    r_coords = list(r_part.coords)
                    s_coords = list(s_part.coords)
                    s_coords[0] = r_coords[0]
                    s_coords[-1] = r_coords[-1]
                    anchored_parts.append(LineString(s_coords))
                return MultiLineString(anchored_parts)
    except Exception as e:
        print(f"Anchoring failed, falling back to raw smoothed geometry: {e}")
        
    return smooth_geom

def safe_smooth_lines(gdf, **kwargs):
    results = []
    
    for idx, row in tqdm(gdf.iterrows(), total=len(gdf), desc="Lissage des segments"):
        geom = row.geometry
        
        if geom is None or geom.is_empty:
            continue  
            
        if not geom.is_valid:
            geom = make_valid(geom)
            
        # 1. On extrait toutes les lignes simples pour éviter le crash de geoai
        lines_to_smooth = []
        if geom.geom_type == 'LineString':
            lines_to_smooth.append(geom)
        elif geom.geom_type == 'MultiLineString':
            lines_to_smooth.extend(list(geom.geoms))
        elif geom.geom_type == 'GeometryCollection':
            for g in geom.geoms:
                if g.geom_type == 'LineString':
                    lines_to_smooth.append(g)
                elif g.geom_type == 'MultiLineString':
                    lines_to_smooth.extend(list(g.geoms))
        
        if not lines_to_smooth:
            continue

        smoothed_sublines = []
        
        # 2. On lisse chaque branche UNE PAR UNE
        for line in lines_to_smooth:
            # Nettoyage topologique indispensable
            clean_line = set_precision(line, grid_size=0.01)
            clean_line = clean_line.simplify(tolerance=3.0, preserve_topology=True)
            
            # Si le nettoyage a détruit la ligne (ex: trop petite), on la garde brute
            if clean_line.geom_type != 'LineString':
                smoothed_sublines.append(line)
                continue

            tmp_gdf = gpd.GeoDataFrame([{'geometry': clean_line}], crs=gdf.crs)
            
            try:
                # Le lissage fonctionne enfin car ce n'est qu'une LineString simple !
                smoothed_tmp = smoothify(geom=tmp_gdf, **kwargs)
                if not smoothed_tmp.empty and not smoothed_tmp.geometry.is_empty.all():
                    sm_geom = smoothed_tmp.geometry.iloc[0]
                    anchored = anchor_endpoints(clean_line, sm_geom)
                    smoothed_sublines.append(anchored)
                else:
                    smoothed_sublines.append(clean_line)
            except Exception as e:
                # En cas de micro-échec, on garde au moins la branche brute
                smoothed_sublines.append(clean_line)
        
        # 3. On reconstruit l'objet géométrique final
        if len(smoothed_sublines) == 1:
            final_geom = smoothed_sublines[0]
        elif len(smoothed_sublines) > 1:
            final_geom = MultiLineString(smoothed_sublines)
        else:
            continue
            
        row_copy = row.copy()
        row_copy.geometry = final_geom
        results.append(gpd.GeoDataFrame([row_copy], crs=gdf.crs))

    if not results:
        return gpd.GeoDataFrame(columns=gdf.columns, crs=gdf.crs)

    return pd.concat(results, ignore_index=True)
    
# def safe_smooth_lines(gdf, **kwargs):
#     """
#     Apply smoothing with strict sanitation to prevent errors.
#     """
#     results = []
    
#     for idx, row in gdf.iterrows():
#         geom = row.geometry
        
#         # --- Step 1: Sanitation Checks ---
#         if geom is None or geom.is_empty:
#             continue  
            
#         if not geom.is_valid:
#             geom = make_valid(geom)
            
#         try:
#             if np.isnan(geom.bounds).any():
#                 continue
#         except Exception:
#             continue

#         if geom.geom_type == 'GeometryCollection':
#             # Extract only lines
#             parts = [g for g in geom.geoms if g.geom_type in ['LineString', 'MultiLineString']]
#             if not parts:
#                 continue
#             geom = MultiLineString(parts) if len(parts) > 1 else parts[0]
#         elif geom.geom_type not in ['LineString', 'MultiLineString']:
#             continue

#         geom = set_precision(geom, grid_size=0.01)
#         geom = geom.simplify(tolerance=0.05, preserve_topology=True)

#         row_copy = row.copy()
#         row_copy.geometry = geom
#         single_gdf = gpd.GeoDataFrame([row_copy], crs=gdf.crs)

#         # --- Step 2: Attempt Smoothing ---
#         try:
#             smoothed = geoai.smooth_vector(single_gdf, **kwargs)
            
#             if not smoothed.empty and not smoothed.geometry.is_empty.all():
#                 smoothed_geom = smoothed.geometry.iloc[0]
#                 anchored_geom = anchor_endpoints(geom, smoothed_geom)
#                 # Update the smoothed geodataframe with the anchored geometry
#                 smoothed.loc[smoothed.index[0], 'geometry'] = anchored_geom
#                 results.append(smoothed)
#             else:
#                 raise ValueError("Smoothing returned empty geometry")

#         except Exception as e:
#             print(f"ÉCHEC Lissage sur le segment_id {row.get('segment_id', idx)} - Erreur : {e}")
#             results.append(gpd.GeoDataFrame([row_copy], crs=gdf.crs))

#     if not results:
#         return gpd.GeoDataFrame(columns=gdf.columns, crs=gdf.crs)

#     return pd.concat(results, ignore_index=True)

def compute_dispersal_surface(
    raster_da: xr.DataArray,
    source_gdf: gpd.GeoDataFrame,
    friction_dict: dict[int, float],
    mask_beyond: float | None = None,
) -> xr.DataArray:
    """
    Continuous dispersal cost surface ("carte de dispersion", CEREMA Phase 3).

    Floods accumulated least-cost distance from every source patch across the
    friction surface. Output is continuous; no thresholding unless requested.

    Parameters
    ----------
    raster_da : xr.DataArray
        Land-cover raster, same grid as the friction surface.
    source_gdf : gpd.GeoDataFrame
        Source patches (origins of the spread). Reprojected internally.
    friction_dict : dict of {int : float}
        Land-cover code -> friction. ``np.nan`` -> barrier (``np.inf``).
    mask_beyond : float or None, default None
        If given, pixels with cost above this value are set to ``np.nan``.
        Purely a display/classification aid (e.g. ``2 * d0 * f_fav``); leave
        ``None`` for the raw continuous field.

    Returns
    -------
    xr.DataArray
        Accumulated dispersal cost (friction x metres), CRS-aligned. Unreachable
        pixels are ``inf``.
    """
    transform = raster_da.rio.transform()
    mcp = MCP_Geometric(
        create_resistance_surface(raster_da, friction_dict).values,
        sampling=(abs(transform.e), abs(transform.a)),
    )

    sources = source_gdf.to_crs(raster_da.rio.crs)
    source_mask = features.rasterize(
        ((geom, 1) for geom in sources.geometry),
        out_shape=raster_da.shape, transform=transform, fill=0, dtype="uint8",
    )
    starts = np.argwhere(source_mask == 1)
    if starts.size == 0:
        raise ValueError("No source pixel rasterized: check CRS / geometries.")

    cumulative_costs, _ = mcp.find_costs(starts=starts)

    if mask_beyond is not None:
        cumulative_costs = np.where(cumulative_costs <= mask_beyond, cumulative_costs, np.nan)

    return xr.DataArray(
        cumulative_costs.astype("float32"),
        coords=raster_da.coords, dims=raster_da.dims, name="dispersal_cost",
    ).rio.write_crs(raster_da.rio.crs)