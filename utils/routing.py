import numpy as np
import xarray as xr
import pandas as pd
import geopandas as gpd
from skimage.graph import MCP_Geometric
from shapely.geometry import LineString, MultiLineString, MultiPolygon
from shapely.validation import make_valid
import shapely
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
    Translate a land-cover raster into a cost surface for MCP_Geometric.

    Impermeable barriers are encoded as np.nan in friction_dict:
        friction[xx] = np.nan  ->  cost_matrix[raster == xx] = np.inf
    MCP_Geometric cannot cross np.inf.

    Parameters
    ----------
    raster_da : xr.DataArray
        Georeferenced land-cover raster.
    friction_dict : dict[int, float]
        Land-cover code -> cost (np.nan for barriers).
    default_cost : float, default 100.0
        Cost for codes not defined in friction_dict.

    Returns
    -------
    xr.DataArray
        Cost surface (np.inf for barriers and outside the AOI).
    """

    # 1. Build the cost matrix
    cost_matrix = np.full(raster_da.shape, default_cost, dtype=np.float32)

    for code, cost in friction_dict.items():
        mask = raster_da.values == code
        if pd.isna(cost):
            cost_matrix[mask] = np.inf
        else:
            cost_matrix[mask] = float(cost)

    # Outside AOI (NaN or 0 in the raster) -> impermeable
    cost_matrix[np.isnan(raster_da.values) | (raster_da.values == 0)] = np.inf

    # 2. Wrap back into an xarray DataArray (spatialize the result)
    resistance_da = xr.DataArray(
        cost_matrix,
        coords=raster_da.coords,
        dims=raster_da.dims,
        name="resistance_surface",
        attrs=raster_da.attrs
    )

    # Force-write the CRS to make sure it is preserved
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
    Compute the Least Cost Path (LCP) between habitat patches.

    Parameters
    ----------
    corridors_gdf : gpd.GeoDataFrame
        Corridors (theoretical straight lines).
    nodes_df : gpd.GeoDataFrame
        Nodes carrying the 'geometry' column.
    raster_da : xr.DataArray
        Georeferenced land-cover grid used as a friction base.
    friction_dict : Dict[int, float]
        Mapping of land-cover codes to travel costs.
    max_cost_threshold : float, optional
        Max accumulated cost in friction x metres.

    Returns
    -------
    gpd.GeoDataFrame
        Real paths (LineString) with 'real_dist' and 'accumulated_cost'.
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

        # Safety: small patches whose boundary ring rasterizes to nothing. Fall back to
        # the FILLED polygon with all_touched=True (guaranteed >= 1 pixel for any non-empty
        # polygon overlapping the grid). The previous centroid fallback rasterized a Point
        # without all_touched, which often burns zero pixels (points have no area) and so
        # silently dropped those nodes -> their corridors failed as 'node_not_found'.
        if len(coords) == 0:
            mask = features.rasterize(
                [(row.geometry, 1)], out_shape=raster_da.shape, transform=transform, all_touched=True
            )
            coords = np.argwhere(mask == 1)

        if len(coords) > 0:
            patch_masks[idx] = coords
            
    # 3. Trace LCPs
    all_paths = []

    for _, row in tqdm(corridors_gdf.iterrows(), total=len(corridors_gdf), desc="Tracing LCPs"):
        u, v = int(row['node_1']), int(row['node_2'])
        
        # Default initialization (failure)
        path_data = {
            'node_1': u, 'node_2': v,
            'theoretical_dist': row['dist_m'],
            'geometry': row['geometry'], # The theoretical straight line
            'status': 'failed',
            'fail_reason': 'node_not_found', # Default reason
            'real_dist': np.nan,
            'accumulated_cost': np.nan,
            'efficiency': np.nan
        }
                
        # Attempt the computation
        if u in patch_masks and v in patch_masks:
            try:
                starts, ends = patch_masks[u], patch_masks[v]
                cumulative_costs, _ = mcp.find_costs(starts=starts, ends=ends, find_all_ends=False)
                costs_at_ends = cumulative_costs[ends[:, 0], ends[:, 1]]

                if np.all(costs_at_ends >= 1e9):
                    path_data['fail_reason'] = 'blocked'
                else:
                    cost_at_end = np.min(costs_at_ends)
                    best_end_idx = ends[np.argmin(costs_at_ends)]
                    path_pixels = mcp.traceback(best_end_idx)
                    path_coords = [transform * (c, r) for r, c in path_pixels]
                    
                    if len(path_coords) >= 2:
                        path_geom = LineString(path_coords)
                    else:
                        # Adjacent / overlapping patches: the cheapest end pixel is already a
                        # start pixel, so the MCP traceback returns a single pixel and no
                        # pixel-path LineString can be built. These patches ARE connected
                        # (accumulated cost ~ 0); fall back to the theoretical anchor-to-anchor
                        # segment from the Gabriel graph instead of leaving the default
                        # 'node_not_found', which mislabels a real, near-adjacent corridor.
                        path_geom = row['geometry']
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
        gdf_final.loc[too_expensive_mask, 'fail_reason'] = 'out_of_reach'
        
    success_count = len(gdf_final[gdf_final['status'] == 'success'])
    print(f"Done: {success_count} success, {len(gdf_final) - success_count} failed.")
    if 'fail_reason' in gdf_final.columns:
        print(gdf_final[gdf_final['status'] == 'failed']['fail_reason'].value_counts())
        
    return gdf_final


def soft_retrace_failed(
    failed_gdf: gpd.GeoDataFrame,
    nodes_df: gpd.GeoDataFrame,
    raster_da: xr.DataArray,
    friction_dict: Dict[int, float],
    soft_barrier: float = 100.0,
) -> gpd.GeoDataFrame:
    """
    Re-trace uncrossable failed links over a SOFT resistance, to locate the realistic
    barrier-crossing point of each rupture.

    Hard barriers (``NaN`` friction) are replaced by ``soft_barrier`` (100), so the least-cost
    path can cross at the cheapest point (narrowest road, near a structure) instead of the
    arbitrary straight desire-line crossing. The traced path is used ONLY to place the rupture
    point (it is not exported as a corridor: no non-functional corridor is shown).

    Parameters
    ----------
    failed_gdf : gpd.GeoDataFrame
        Failed links to re-trace (expects 'node_1', 'node_2'); typically the
        ``blocked`` subset.
    nodes_df : gpd.GeoDataFrame
        Patch nodes (RangeIndex aligned with node ids), 'geometry' column.
    raster_da : xr.DataArray
        Land-cover grid (same as compute_lcp_network).
    friction_dict : Dict[int, float]
        Per-code friction; ``NaN`` entries are the hard barriers softened to ``soft_barrier``.
    soft_barrier : float, default 100.0
        Finite cost given to hard-barrier codes (CEREMA "infranchissable" = 100).

    Returns
    -------
    gpd.GeoDataFrame
        One traced (Multi)LineString per re-traced link, columns ['node_1', 'node_2', 'geometry'].
    """
    cols = ['node_1', 'node_2', 'geometry']
    if failed_gdf is None or failed_gdf.empty:
        return gpd.GeoDataFrame(columns=cols, geometry='geometry', crs=raster_da.rio.crs)

    soft = {c: (float(soft_barrier) if (isinstance(v, float) and np.isnan(v)) else v)
            for c, v in friction_dict.items()}
    resistance_da = create_resistance_surface(raster_da, soft)
    transform = raster_da.rio.transform()
    mcp = MCP_Geometric(resistance_da.values, sampling=(abs(transform.e), abs(transform.a)))

    needed = set(failed_gdf['node_1'].astype(int)) | set(failed_gdf['node_2'].astype(int))
    patch_masks = {}
    for idx in needed:
        if idx not in nodes_df.index:
            continue
        geom = nodes_df.loc[idx].geometry
        mask = features.rasterize([(geom.boundary, 1)], out_shape=raster_da.shape,
                                  transform=transform, all_touched=True)
        coords = np.argwhere(mask == 1)
        if len(coords) == 0:
            mask = features.rasterize([(geom, 1)], out_shape=raster_da.shape,
                                      transform=transform, all_touched=True)
            coords = np.argwhere(mask == 1)
        if len(coords) > 0:
            patch_masks[idx] = coords

    out = []
    for _, row in failed_gdf.iterrows():
        u, v = int(row['node_1']), int(row['node_2'])
        if u not in patch_masks or v not in patch_masks:
            continue
        try:
            starts, ends = patch_masks[u], patch_masks[v]
            cumulative_costs, _ = mcp.find_costs(starts=starts, ends=ends, find_all_ends=False)
            costs_at_ends = cumulative_costs[ends[:, 0], ends[:, 1]]
            if np.all(~np.isfinite(costs_at_ends)):
                continue
            best_end = ends[np.argmin(costs_at_ends)]
            path_pixels = mcp.traceback(best_end)
            if len(path_pixels) >= 2:
                path_coords = [transform * (c, r) for r, c in path_pixels]
                out.append({'node_1': u, 'node_2': v, 'geometry': LineString(path_coords)})
        except Exception:
            continue

    if not out:
        return gpd.GeoDataFrame(columns=cols, geometry='geometry', crs=raster_da.rio.crs)
    return gpd.GeoDataFrame(out, geometry='geometry', crs=raster_da.rio.crs)


def safe_smooth(gdf: gpd.GeoDataFrame, **kwargs) -> gpd.GeoDataFrame:
    """
    Smooth polygon geometries in one batched pass, keeping the node set and index intact.

    Returns a copy of `gdf` with the SAME rows and index: geometries are smoothed where
    possible (only the geometry column changes), unusable ones keep their raw geometry, and a
    final ``buffer(0)`` cleans everything. No row is ever dropped or renumbered, which keeps
    node IDs aligned with the graph / corridors / patch masks (avoids 'node_not_found' and
    falsely isolated stepping stones).

    Smoothing uses a SINGLE ``smoothify`` call (``merge_collection=False`` so each feature stays
    separate). Calling smoothify per geometry respawns a joblib worker pool on every call, which
    is pathologically slow (minutes to hours) and triggers "worker stopped" warnings; one batched
    call does the whole set in a single parallel pass (seconds).

    Parameters
    ----------
    gdf : gpd.GeoDataFrame
        Polygon geometries to smooth.
    **kwargs
        Forwarded to ``smoothify`` (e.g. ``smooth_iterations``, ``num_cores``).

    Returns
    -------
    gpd.GeoDataFrame
        Same rows/index as `gdf`, geometries smoothed where possible then buffer(0)-cleaned.
    """
    out = gdf.copy()
    geom = out.geometry
    # Vectorized sanitation: repair invalid (non-empty) geometries in place.
    bad = geom.notna() & ~geom.is_empty & ~geom.is_valid
    if bad.any():
        out.loc[bad, "geometry"] = geom[bad].apply(make_valid)

    smoothable = (
        out.geometry.notna()
        & ~out.geometry.is_empty
        & out.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
    )
    # Guard against pathological mega-polygons: a single patch with a huge vertex count (e.g. a
    # near-region-wide habitat core in a heavily-vegetated AOI) makes smoothify (and even
    # buffer(0)/simplify) grind for hours on that one geometry. Keep such polygons RAW and PRINT
    # which ones, so it is visible in the log instead of a silent freeze.
    max_smooth_vertices = 50_000
    nverts = pd.Series(shapely.get_num_coordinates(out.geometry.values), index=out.index)
    too_big = smoothable & (nverts > max_smooth_vertices)
    if too_big.any():
        print(f"⚠️ safe_smooth: {int(too_big.sum())} polygon(s) over {max_smooth_vertices:,} "
              f"vertices (max {int(nverts.max()):,}) kept RAW (not smoothed) to avoid a "
              f"smoothify hang.", flush=True)
        smoothable = smoothable & ~too_big

    if smoothable.any():
        kwargs.setdefault("merge_collection", False)
        try:
            sm = smoothify(geom=out.loc[smoothable, ["geometry"]].reset_index(drop=True), **kwargs)
            new = sm.geometry.to_numpy()
            targets = out.index[smoothable.to_numpy()]
            keep = np.array([g is not None and not g.is_empty for g in new])
            if keep.any():
                out.loc[targets[keep], "geometry"] = gpd.GeoSeries(
                    new[keep], index=targets[keep], crs=gdf.crs
                )
        except Exception as e:
            print(f"Batch smoothing failed ({e}); keeping raw node geometries.")

    # buffer(0) only the non-oversized geometries: GEOS buffer/overlay can itself hang on a
    # mega-polygon, so the kept-raw ones (already valid from MSPA) are left untouched.
    safe = ~too_big
    out.loc[safe, "geometry"] = out.loc[safe, "geometry"].buffer(0)
    return out

def calculate_tortuosity(lcp_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Compute the tortuosity index: real distance / theoretical distance.

    A value of 1.0 means a straight path; higher values indicate constraints.

    Parameters
    ----------
    lcp_gdf : gpd.GeoDataFrame
        GeoDataFrame containing 'real_dist' and 'theoretical_dist'.

    Returns
    -------
    gpd.GeoDataFrame
        Input GeoDataFrame with an added 'tortuosity' column.
    """
    # Degenerate corridors (near-adjacent patches, theoretical_dist ~ 0) blow up to inf -> NaN.
    lcp_gdf['tortuosity'] = (
        lcp_gdf['real_dist'] / lcp_gdf['theoretical_dist']
    ).replace([np.inf, -np.inf], np.nan)
    return lcp_gdf

def anchor_endpoints(
    raw_geom: "LineString | MultiLineString",
    smooth_geom: "LineString | MultiLineString",
) -> "LineString | MultiLineString":
    """
    Force the smoothed line to start and end exactly where the raw line did.

    Restores network connectivity at junctions and habitat borders by snapping the
    smoothed endpoints back to the raw endpoints.

    Parameters
    ----------
    raw_geom : LineString or MultiLineString
        Original (pre-smoothing) geometry.
    smooth_geom : LineString or MultiLineString
        Smoothed geometry to anchor.

    Returns
    -------
    LineString or MultiLineString
        The smoothed geometry with endpoints snapped to the raw ones (or the raw
        smoothed geometry if anchoring fails).
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

def safe_smooth_lines(gdf: gpd.GeoDataFrame, **kwargs) -> gpd.GeoDataFrame:
    """
    Smooth line geometries branch by branch, with endpoint anchoring.

    Each (Multi)LineString is split into simple LineStrings, each branch is cleaned
    (set_precision + simplify), smoothed individually, and its endpoints are snapped
    back to the cleaned branch; branches are then reassembled.

    Parameters
    ----------
    gdf : gpd.GeoDataFrame
        Line geometries to smooth.
    **kwargs
        Forwarded to ``smoothify``.

    Returns
    -------
    gpd.GeoDataFrame
        Smoothed line geometries.
    """
    crs = gdf.crs

    # Pass 1: explode every row into cleaned simple-line branches, remembering which row
    # and slot each branch belongs to. Branches that the cleanup degrades to non-LineString
    # are kept raw (never smoothed). No smoothify call here, so this pass is cheap.
    clean_branches = []          # cleaned LineStrings queued for the SINGLE smoothify pass
    branch_key = []              # (row_pos, slot) parallel to clean_branches
    raw_slot_geom = {}           # (row_pos, slot) -> geometry kept as-is (not smoothed)
    row_slots = {}               # row_pos -> number of slots (branches) for that row
    kept_rows = []               # row_pos with at least one branch, in order
    row_records = {}             # row_pos -> original row (attributes)

    for pos, (_, row) in enumerate(tqdm(gdf.iterrows(), total=len(gdf), desc="Prep segments")):
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        if not geom.is_valid:
            geom = make_valid(geom)

        lines = []
        if geom.geom_type == 'LineString':
            lines.append(geom)
        elif geom.geom_type == 'MultiLineString':
            lines.extend(list(geom.geoms))
        elif geom.geom_type == 'GeometryCollection':
            for g in geom.geoms:
                if g.geom_type == 'LineString':
                    lines.append(g)
                elif g.geom_type == 'MultiLineString':
                    lines.extend(list(g.geoms))
        if not lines:
            continue

        slot = 0
        for line in lines:
            clean_line = set_precision(line, grid_size=0.01).simplify(tolerance=3.0, preserve_topology=True)
            if clean_line.geom_type != 'LineString':
                raw_slot_geom[(pos, slot)] = line       # cleanup destroyed it -> keep raw
            else:
                clean_branches.append(clean_line)
                branch_key.append((pos, slot))
            slot += 1

        row_slots[pos] = slot
        kept_rows.append(pos)
        row_records[pos] = row

    # Pass 2: ONE batched smoothify call over every cleaned branch. merge_collection=False
    # keeps one output per input, so results stay aligned with branch_key by position.
    smoothed_by_key = {}
    if clean_branches:
        kwargs.setdefault('merge_collection', False)
        batch = gpd.GeoDataFrame({'geometry': clean_branches}, crs=crs)
        try:
            out = smoothify(geom=batch, **kwargs).geometry.to_numpy()
            for (key, clean_line, sm_geom) in zip(branch_key, clean_branches, out):
                if sm_geom is not None and not sm_geom.is_empty:
                    smoothed_by_key[key] = anchor_endpoints(clean_line, sm_geom)
                else:
                    smoothed_by_key[key] = clean_line
        except Exception as e:
            print(f"Batch line smoothing failed ({e}); keeping cleaned branches.")
            for key, clean_line in zip(branch_key, clean_branches):
                smoothed_by_key[key] = clean_line

    # Pass 3: reassemble each row from its branches (smoothed or raw), in slot order.
    records = []
    for pos in kept_rows:
        parts = []
        for slot in range(row_slots[pos]):
            if (pos, slot) in raw_slot_geom:
                parts.append(raw_slot_geom[(pos, slot)])
            elif (pos, slot) in smoothed_by_key:
                parts.append(smoothed_by_key[(pos, slot)])
        if not parts:
            continue
        row_copy = row_records[pos].copy()
        row_copy.geometry = parts[0] if len(parts) == 1 else MultiLineString(parts)
        records.append(row_copy)

    if not records:
        return gpd.GeoDataFrame(columns=gdf.columns, crs=crs)

    return gpd.GeoDataFrame(records, crs=crs).set_geometry('geometry').reset_index(drop=True)
    

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
