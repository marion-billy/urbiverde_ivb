import sys
import pandas as pd
import numpy as np
import xarray as xr
import geopandas as gpd
from scipy import ndimage
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from tqdm import tqdm
from rasterio import features
from rasterio.enums import MergeAlg
from shapely.geometry import shape
from affine import Affine
import matplotlib.pyplot as plt
import networkx as nx
from sklearn.neighbors import BallTree
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points, unary_union, linemerge
from shapely.prepared import prep
from typing import Optional, Union, Any, List, Union, Tuple
sys.path.insert(1, '../../Hugo/a_b_c_functions/spatial_analysis/')
from utils_raster import raster_to_polygon
from utils_raster import create_img_reference

#######################################
################ MSPA #################
#######################################

def get_binary_habitat(da_lc: xr.DataArray, habitat_codes: List[int]) -> xr.DataArray:
    """
    Binarize the land-cover raster according to the species preferences.

    Parameters
    ----------
    da_lc : xr.DataArray
        Land-cover raster.
    habitat_codes : List[int]
        Codes considered as habitat.

    Returns
    -------
    xr.DataArray
        Binary raster (1: habitat / foreground, 0: matrix / background).
    """
    binary = xr.where(da_lc.isin(habitat_codes), 1, 0)
    return binary.where(da_lc.notnull(), 0).astype('uint8')

def fast_mspa(da_binary: xr.DataArray, edge_width_pixels: int = 1) -> Tuple[xr.DataArray, xr.DataArray]:
    """
    Identify the morphological categories Cores and Islets.

    Edge sensitivity is tunable via edge_width_pixels.

    Parameters
    ----------
    da_binary : xr.DataArray
        Binary mask (1: habitat, 0: background).
    edge_width_pixels : int, default 1
        Number of pixels to shave off the border.

    Returns
    -------
    tuple of (xr.DataArray, xr.DataArray, xr.DataArray)
        (cores, islets, edges) rasters.
    """
    binary_mask = da_binary.values 
    
    struct = np.ones((3,3)) # structuring element, queen connectivity / 8 neighbours
    # EROSION (Core creation)
    core_arr = ndimage.binary_erosion(binary_mask, structure=struct, iterations=edge_width_pixels)
    labels, n_labels = ndimage.label(binary_mask)

    # An Islet is a blob that vanishes after erosion: no Core pixel inside
    labels_with_core = np.unique(labels[core_arr > 0])
    is_core_patch = np.isin(labels, labels_with_core)
    islet_arr = (labels > 0) & (~is_core_patch)

    # Edge
    edge_arr = (is_core_patch) & (core_arr == 0)
    
    # --- C. Re-wrap into DataArrays (copy the input coordinates) ---
    da_core = da_binary.copy(data=core_arr.astype('uint8'))
    da_islet = da_binary.copy(data=islet_arr.astype('uint8'))
    da_edge = da_binary.copy(data=edge_arr.astype('uint8'))
    
    return da_core, da_islet, da_edge

def get_connectivity_elements(
    da_binary: xr.DataArray, 
    core_min_ha: float = 1.0, 
    islet_min_ha: float = 0.1
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Identify and classify connectivity elements (Cores and Stepping Stones).
    A Core is a patch whose CORE is >= core_min_ha, but the returned geometry includes the edge.
    Cores too small to qualify are downgraded to Stepping Stones.
    """
    
    # 1. Calcul MSPA
    da_core, da_islet, da_edge = fast_mspa(da_binary, edge_width_pixels=1)
    
    # 2. Vectorisation des Cores (pour calculer la surface interne de chaque patch)
    gdf_pure_cores = raster_to_polygon(da_core, data_type='uint8')
    gdf_pure_cores = gdf_pure_cores[gdf_pure_cores['value'] == 1].copy()
    if not gdf_pure_cores.empty:
        gdf_pure_cores['core_area_ha'] = gdf_pure_cores.geometry.area / 10000
    
    # 3. Vectorisation de tous les patchs d'habitat (Foreground complet)
    gdf_full_patches = raster_to_polygon(da_binary, data_type='uint8')
    gdf_full_patches = gdf_full_patches[gdf_full_patches['value'] == 1].copy()
    gdf_full_patches['total_area_ha'] = gdf_full_patches.geometry.area / 10000

    # Attribution de la surface de coeur max par patch
    if not gdf_pure_cores.empty:
        joined = gpd.sjoin(gdf_full_patches, gdf_pure_cores, how='left', predicate='intersects')
        patch_core_max = joined.groupby(joined.index)['core_area_ha'].max()
        gdf_full_patches['max_core_ha'] = patch_core_max.fillna(0)
    else:
        gdf_full_patches['max_core_ha'] = 0.0
    
    # 4. Classification
    mask_noyau = gdf_full_patches['max_core_ha'] >= core_min_ha # Un Noyau (Core) a un coeur >= seuil
    mask_ss = (~mask_noyau) & (gdf_full_patches['total_area_ha'] >= islet_min_ha) # Un Stepping Stone est soit un petit core, soit un islet (max_core_ha == 0)
    gdf_cores_final = gdf_full_patches[mask_noyau].copy()
    gdf_cores_final['class'] = "Core (Noyau)"
    gdf_stepping_stones = gdf_full_patches[mask_ss].copy()
    # Assign 'class' unconditionally: np.where on an empty frame yields an empty array, so the column
    # still exists when there are zero stepping stones. The previous `if not empty` guard skipped it,
    # so gdf_stepping_stones[cols] then raised KeyError('class') on any 0-islet run (crash -> empty
    # output). A zero-islet result is legitimate (e.g. extreme friction / small habitat).
    gdf_stepping_stones['class'] = np.where(
        gdf_stepping_stones['max_core_ha'] > 0,
        "Stepping Stone (Small Core)",
        "Stepping Stone (Islet)"
    )

    cols = ['geometry', 'total_area_ha', 'max_core_ha', 'class']
    return gdf_cores_final[cols], gdf_stepping_stones[cols]
    
#######################################
############ GRAPH THEORY #############
#######################################

def prepare_graph_nodes(gdf_cores: gpd.GeoDataFrame, gdf_islets: gpd.GeoDataFrame) -> pd.DataFrame:
    """
    Merge core habitats and stepping stones into a unified dataset and extract a representative point (centroid forced inside the shape).

    Parameters
    ----------
    gdf_cores : gpd.GeoDataFrame
        Large habitat patches (reservoirs).
    gdf_islets : gpd.GeoDataFrame
        Small habitat patches (stepping stones).

    Returns
    -------
    pd.DataFrame
        Merged dataset with 'x', 'y' coordinates and 'node_type'.
    """
    nodes = pd.concat([
        gdf_cores.assign(node_type='core'), 
        gdf_islets.assign(node_type='islet')
    ], ignore_index=True)
    
    rep_points = nodes.geometry.representative_point()
    nodes['x'] = rep_points.x
    nodes['y'] = rep_points.y
    return nodes


def build_gabriel_graph(nodes_df: gpd.GeoDataFrame, species_params: dict,
                        debug_node: int = None) -> nx.Graph:
    """
    Build a Gabriel graph based on edge-to-edge distances.
    Less restrictive than the RNG, it keeps alternative paths (loops).

    Parameters
    ----------
    nodes_df : gpd.GeoDataFrame
        Node polygons with a clean RangeIndex (0..N-1) used as node IDs.
    species_params : dict
        Per-ecoprofil config, reads species_params['graph']['d0'].
    debug_node : int, optional
        If set, log every candidate/skip/prune decision involving this node ID.
        Temporary diagnostic, does not alter the graph. Default None.
    """
    d0 = species_params['graph']['d0']
    max_dist = 2 * d0
    dbg_set = set(debug_node) if isinstance(debug_node, (list, tuple, set)) else ({debug_node} if debug_node is not None else set())
    _cand = {n: {'count': 0, 'nearest': (float('inf'), None), 'touch': 0, 'toofar': 0} for n in dbg_set}
    _edge = {n: [] for n in dbg_set}  # (other, dist, kept, pruner)

    # 0. Validity guard. Raw MSPA polygons are frequently self-intersecting; geometry
    # predicates (distance, nearest_points) on an invalid polygon silently return wrong
    # values, which drops legitimate candidate edges and leaves nodes spuriously isolated
    # even when a valid neighbour sits a few metres away with nothing in between. Repair
    # them here (make_valid is far cheaper than node smoothing, so the graph can still be
    # built before the smoothing step). Index is preserved, so node IDs stay aligned.
    nodes_df = nodes_df.copy()
    invalid = ~nodes_df.geometry.is_valid
    if invalid.any():
        nodes_df.loc[invalid, 'geometry'] = nodes_df.geometry[invalid].make_valid()

    # 1. Initialisation
    G_candidate = nx.Graph()
    for i, row in nodes_df.iterrows():
        G_candidate.add_node(i, area=row['total_area_ha'], type=row['node_type'], pos=(row['x'], row['y']))
    
    sindex = nodes_df.sindex
    candidate_edges = []
    # Patches that physically touch (gap <= 0.1 m, adjacent on the raw MSPA grid) are
    # contiguous habitat split by the core/stepping-stone threshold. They get a direct
    # zero-cost adjacency edge (added after pruning, never pruned), instead of being
    # dropped. This replaces the old "touching-exclusion" workaround, which both failed to
    # connect a stepping stone to the core it touches AND let a long spurious edge survive
    # across that core (the touching core was excluded from pruning), producing phantom
    # corridors/ruptures. See suivi/decision_log.md.
    touch_edges = []

    # 2. Step 1: candidate search
    for i, row in tqdm(nodes_df.iterrows(), total=len(nodes_df), desc="Step 1/2: candidate search"):
        current_geom = row.geometry
        possible_neighbors = list(sindex.query(current_geom.buffer(max_dist)))
        
        for idx in possible_neighbors:
            if idx <= i: continue

            target_geom = nodes_df.iloc[idx].geometry
            dist = current_geom.distance(target_geom)
            if dbg_set and (i in dbg_set or idx in dbg_set):
                tgt = i if i in dbg_set else idx
                other = idx if tgt == i else i
                if dist <= 0.1:
                    _cand[tgt]['touch'] += 1
                elif dist > max_dist:
                    _cand[tgt]['toofar'] += 1
                else:
                    _cand[tgt]['count'] += 1
                    if dist < _cand[tgt]['nearest'][0]:
                        _cand[tgt]['nearest'] = (dist, other)
            if dist <= 0.1:
                # Touching patches: contiguous habitat -> direct adjacency edge (see above).
                p1, p2 = nearest_points(current_geom, target_geom)
                touch_edges.append({'u': i, 'v': idx, 'p1': p1, 'p2': p2})
            elif dist <= max_dist:
                p1, p2 = nearest_points(current_geom, target_geom)
                candidate_edges.append({
                    'u': i, 'v': idx, 'dist': dist, 'p1': p1, 'p2': p2
                })

    # 3. Step 2: Gabriel filtering
    G_gab = nx.Graph()
    G_gab.add_nodes_from(G_candidate.nodes(data=True))

    for edge in tqdm(candidate_edges, desc="Step 2/2: Gabriel filtering"):
        u, v, dist_uv = edge['u'], edge['v'], edge['dist']
        is_gabriel = True
        
        p_u, p_v = edge['p1'], edge['p2']
        
        # --- LOGIQUE GABRIEL ---
        # Le milieu du segment reliant les deux points les plus proches
        midpoint = Point((p_u.x + p_v.x)/2, (p_u.y + p_v.y)/2)
        radius = dist_uv / 2
        
        # Search zone: the circle of diameter UV
        search_zone = midpoint.buffer(radius)
        potential_c = list(sindex.query(search_zone))
        
        pruner = None
        pruner_d = None
        for idx_c in potential_c:
            if idx_c in [u, v]: continue
            geom_c = nodes_df.iloc[idx_c].geometry
            # If a patch C is closer to the midpoint than the radius, break the edge
            dc = geom_c.distance(midpoint)
            if dc < radius:
                is_gabriel = False
                pruner = idx_c
                pruner_d = dc
                break

        if is_gabriel:
            prob = np.exp(-dist_uv / d0)
            G_gab.add_edge(u, v,
                           dist_m=dist_uv,
                           prob=prob,
                           cost_log=-np.log(prob),
                           anchor_pts=(p_u, p_v))

        if dbg_set and (u in dbg_set or v in dbg_set):
            tgt = u if u in dbg_set else v
            other = v if tgt == u else u
            _edge[tgt].append((other, dist_uv, is_gabriel, pruner, pruner_d, radius))

    if dbg_set:
        print(f"\n=== DEBUG nodes {sorted(dbg_set)} (RangeIndex ok: {list(nodes_df.index) == list(range(len(nodes_df)))}) ===")
        for n in sorted(dbg_set):
            c = _cand[n]
            kept = [e for e in _edge[n] if e[2]]
            pruned = [e for e in _edge[n] if not e[2]]
            print(f"- node {n}: final degree = {G_gab.degree(n) if n in G_gab else 'ABSENT'}")
            print(f"    candidates in range: {c['count']} (nearest {c['nearest'][0]:.0f}m -> node {c['nearest'][1]}) | touching-skips: {c['touch']} | too-far: {c['toofar']}")
            print(f"    edges KEPT: {len(kept)} | edges PRUNED: {len(pruned)}")
            # closest 12 candidate edges, sorted by gap, with the pruning decision
            for other, d, keptf, pr, prd, rad in sorted(_edge[n], key=lambda e: e[1])[:12]:
                if keptf:
                    print(f"      gap={d:7.1f}m -> node {other}: KEPT")
                else:
                    print(f"      gap={d:7.1f}m -> node {other}: PRUNED by node {pr} (its dist to gap-midpoint={prd:.1f}m < radius={rad:.1f}m)")
        print("=== end debug ===\n")

    # Adjacency edges for touching patches: contiguous habitat connected at ~zero cost
    # (prob = 1). Added last so they are never pruned. A pair is either touching or a
    # candidate (mutually exclusive distance bands), so this never duplicates a kept edge.
    for e in touch_edges:
        if not G_gab.has_edge(e['u'], e['v']):
            G_gab.add_edge(e['u'], e['v'], dist_m=0.0, prob=1.0, cost_log=0.0,
                           anchor_pts=(e['p1'], e['p2']))

    print(f"Gabriel graph built: {G_gab.number_of_nodes()} nodes and {G_gab.number_of_edges()} edges "
          f"({len(touch_edges)} adjacency/touch edges).")
    return G_gab

def _pc_numerator(G: nx.Graph, weight: str = 'cost_log') -> float:
    """
    Vectorized PC numerator: sum over connected components of
    ``sum_ij a_i * a_j * exp(-d_ij)`` where ``d_ij`` is the least-cost path length
    (Dijkstra on ``weight``) and areas are in km2 (node attr 'area' is in ha).

    Replaces the previous pure-Python ``all_pairs_dijkstra`` + O(N^2) double loop,
    which dominated runtime on large cities (hours on Toulouse). Uses scipy's C-level
    Dijkstra for the dense per-component cost matrix and a numpy outer product for the
    sum. Mathematically identical: within a component every pair is reachable, and the
    diagonal d_ii = 0 gives exp(0) = 1, matching the old n1 == n2 special case.

    Parameters
    ----------
    G : nx.Graph
        Connectivity graph; node attr 'area' (ha), edge attr ``weight`` (>= 0).
    weight : str, default 'cost_log'
        Edge attribute used as the Dijkstra cost.

    Returns
    -------
    float
        The PC numerator (not yet divided by total_area_km2**2).
    """
    pc_sum = 0.0
    for comp in nx.connected_components(G):
        sub = G.subgraph(comp)
        nodelist = list(sub.nodes())
        local = {node: k for k, node in enumerate(nodelist)}
        areas = np.array([sub.nodes[node]['area'] / 100.0 for node in nodelist])  # ha -> km2

        if len(nodelist) == 1:
            pc_sum += float(areas[0] * areas[0])  # self pair, prob = 1
            continue

        # Symmetric sparse cost matrix in local indexing
        rows, cols, data = [], [], []
        for u, v, d in sub.edges(data=True):
            iu, iv = local[u], local[v]
            w = d[weight]
            rows += [iu, iv]
            cols += [iv, iu]
            data += [w, w]
        W = csr_matrix((data, (rows, cols)), shape=(len(nodelist), len(nodelist)))

        dist = dijkstra(W, directed=False)        # dense NxN, 0 on diagonal
        prob = np.exp(-dist)                       # diagonal -> 1.0, matches n1 == n2
        pc_sum += float((areas[:, None] * areas[None, :] * prob).sum())

    return pc_sum


def calculate_pc_index(G: nx.Graph, total_area_km2: float) -> float:
    """
    Compute the Probability of Connectivity (PC) index for the landscape.

    Measures the overall 'permeability' of the landscape for a given species.

    Parameters
    ----------
    G : nx.Graph
        The connectivity graph.
    total_area_km2 : float
        Total study-area (AOI) surface in km2.

    Returns
    -------
    float
        PC index value (0 to 1).
    """
    return _pc_numerator(G, weight='cost_log') / (total_area_km2 ** 2)

def graph_to_gdf_edges(G: nx.Graph, crs: Any) -> gpd.GeoDataFrame:
    """Convert all edges of a NetworkX graph into a GeoDataFrame."""
    edges = []
    for u, v, data in G.edges(data=True):
        p1, p2 = data['anchor_pts']
        # Touching patches share their nearest point (p1 == p2): a 2-identical-point
        # LineString is degenerate and breaks GeoJSON export / downstream geometry ops.
        # Nudge into a valid 1 mm segment at the contact point (adjacency, no real corridor).
        if p1.equals(p2) or p1.distance(p2) < 1e-6:
            geom = LineString([(p1.x, p1.y), (p1.x + 1e-3, p1.y)])
        else:
            geom = LineString([p1, p2])  # the actual gap, not the centroid distance
        edges.append({
            'node_1': u,
            'node_2': v,
            'dist_m': data['dist_m'],
            'cost_log': data['cost_log'],
            'geometry': geom
        })
    return gpd.GeoDataFrame(edges, crs=crs)
    
def calculate_pc_index_lcp(G: nx.Graph, total_area_km2: float, species_params: dict, gdf_lcp: gpd.GeoDataFrame = None):
    """
    Compute the real PC using accumulated cost as the biological weight.
    If gdf_lcp is provided, update the graph. 
    Otherwise, use the graph as is (useful for dPC iterations).
    """
    d0 = species_params['graph']['d0']
    G_curr = G.copy()
    
    if gdf_lcp is not None:
        lcp_lookup = {tuple(sorted((int(row['node_1']), int(row['node_2'])))): row['accumulated_cost'] 
                      for _, row in gdf_lcp.iterrows()}
        
        for u, v in G_curr.edges():
            edge_key = tuple(sorted((u, v)))
            acc_cost = lcp_lookup.get(edge_key)
            if acc_cost is not None:
                if np.isnan(acc_cost) or np.isinf(acc_cost):
                    cost_log = 999999 # Prohibitive cost on data error
                else:
                    cost_log = max(0.0, acc_cost / d0)
                prob = np.exp(-cost_log)
                G_curr[u][v].update({'accumulated_cost': acc_cost, 'prob': prob, 'cost_log': cost_log})

    # Calcul du PC (vectorized; see _pc_numerator)
    pc_value = _pc_numerator(G_curr, weight='cost_log') / (total_area_km2 ** 2)

    return pc_value, G_curr

def calculate_edge_dpc(gdf_lcp: gpd.GeoDataFrame, G_curr: nx.Graph, total_area_km2: float, pc_real: float) -> gpd.GeoDataFrame:
    """
    Compute the dPC importance for each real corridor (LCP).

    Parameters
    ----------
    gdf_lcp : gpd.GeoDataFrame
        GeoDataFrame of LCP paths (must contain node_1, node_2 and real_dist).
    G_curr : nx.Graph
        Graph updated with real distances.
    total_area_km2 : float
        Total study-area surface (AOI).
    pc_real : float
        The real PC value.

    Returns
    -------
    gpd.GeoDataFrame
        Input GeoDataFrame with 'dPC_val' and 'dPC_relative' columns, sorted by 'dPC_val'.

    DISABLED (2026-06-10): the dPC (flux) corridor metric is not needed for now.
    The function short-circuits and returns NaN 'dPC_val' / 'dPC_relative' columns
    (kept so downstream writers / classify_corridors do not KeyError). The full
    implementation is preserved verbatim below the early return; delete the
    early-return block to re-enable. See suivi/decision_log.md.
    """
    # --- TEMPORARY DISABLE: skip the dPC (flux) corridor metric -------------
    df = gdf_lcp.copy()
    df['dPC_val'] = np.nan
    df['dPC_relative'] = np.nan
    return df
    # --- preserved implementation below (unreachable while disabled) ---------

    df = gdf_lcp.copy()

    def compute_row(row):
        u, v = int(row['node_1']), int(row['node_2'])
        
        # Fetch data from the graph G_curr
        a_i = G_curr.nodes[u]['area'] / 100 # ha -> km2
        a_j = G_curr.nodes[v]['area'] / 100 # ha -> km2
        prob = G_curr[u][v]['prob']
        
        # Calcul du dPC (flux)
        val = (a_i * a_j * prob) / (total_area_km2**2)
        return val, (val / pc_real) * 100

    res = df.apply(compute_row, axis=1)
    
    df['dPC_val'], df['dPC_relative'] = zip(*res)
    return df.sort_values(by='dPC_val', ascending=False)

def calculate_edge_betweenness(gdf_lcp: gpd.GeoDataFrame, G_curr: nx.Graph) -> gpd.GeoDataFrame:
    """
    Compute the betweenness centrality for each corridor.
    Identify corridors that are mandatory passages (connectors).

    DISABLED (2026-06-10): the edge-betweenness (flow) corridor metric is not
    needed for now. The function short-circuits and returns a NaN 'ebc_score'
    column (kept so downstream writers / classify_corridors do not KeyError). The
    full implementation is preserved verbatim below the early return; delete the
    early-return block to re-enable. See suivi/decision_log.md.
    """
    # --- TEMPORARY DISABLE: skip the edge-betweenness (flow) corridor metric -
    df = gdf_lcp.copy()
    df['ebc_score'] = np.nan
    return df
    # --- preserved implementation below (unreachable while disabled) ---------

    df = gdf_lcp.copy()
    edge_centrality = nx.edge_betweenness_centrality(G_curr, weight='cost_log', normalized=True)
    
    def get_centrality(row):
        u, v = int(row['node_1']), int(row['node_2'])
        return edge_centrality.get((u, v)) or edge_centrality.get((v, u), 0)

    df['ebc_score'] = df.apply(get_centrality, axis=1)
    
    # 3. Normalize from 0 to 100 
    if df['ebc_score'].max() > 0:
        df['ebc_score'] = (df['ebc_score'] / df['ebc_score'].max()) * 100
        
    return df.sort_values(by='ebc_score', ascending=False)

def classify_corridors(gdf_lcp: gpd.GeoDataFrame, q: float = 0.5) -> gpd.GeoDataFrame:
    """
    Compute thresholds and categorize corridors.
    Retourne le GeoDataFrame enrichi de la colonne 'category'.

    DISABLED (2026-06-10): this classification derives from dPC_relative (flux) and
    ebc_score (flow), both disabled. It short-circuits and returns a None 'category'
    column. The full implementation is preserved verbatim below the early return;
    delete the early-return block (and re-enable dPC + edge betweenness) to restore.
    See suivi/decision_log.md.
    """
    # --- TEMPORARY DISABLE: classification depends on disabled flux/flow -----
    gdf_lcp = gdf_lcp.copy()
    gdf_lcp['category'] = None
    return gdf_lcp
    # --- preserved implementation below (unreachable while disabled) ---------

    flow_threshold = gdf_lcp['dPC_relative'].quantile(q)
    rarity_threshold = gdf_lcp['ebc_score'].quantile(q)

    def _classify(row):
        hi_flow = row['dPC_relative'] > flow_threshold
        hi_rarity = row['ebc_score'] > rarity_threshold
        if hi_flow and hi_rarity: return 'Ecological highway'
        if not hi_flow and hi_rarity: return 'Strategic bottleneck'
        if hi_flow and not hi_rarity: return 'Redundant mesh'
        return 'Local link'

    gdf_lcp = gdf_lcp.copy()
    gdf_lcp['category'] = gdf_lcp.apply(_classify, axis=1)
    return gdf_lcp

def calculate_node_betweenness(df_nodes: gpd.GeoDataFrame, G_curr: nx.Graph, aoi_gdf: gpd.GeoDataFrame = None,
                               keep_ids: set = None) -> gpd.GeoDataFrame:
    """
    Compute the Node Betweenness Centrality (NBC) for each habitat reservoir.
    Identify patches acting as ecological hubs.
    Allows filtering on the AOI for local normalization.

    Parameters
    ----------
    df_nodes : gpd.GeoDataFrame
        All study nodes (city AOI + buffer).
    G_curr : nx.Graph
        LCP graph used for the centrality (preserved path only).
    aoi_gdf : gpd.GeoDataFrame, optional
        If given, the export is clipped to nodes intersecting the AOI. Default None.
    keep_ids : set, optional
        Node IDs to keep even when they fall outside the AOI. Used to retain the
        out-of-AOI (buffer) patches that are an endpoint of a kept corridor, so the
        corridors terminate on a visible habitat instead of dead-ending at the AOI
        edge. These linked patches are connected by construction, so they never
        appear in the isolated-nodes layer. Default None.

    DISABLED (2026-06-10): the node network-role metric (NBC) is not needed for
    now. The function short-circuits and returns a NaN 'nbc_score' column, but
    KEEPS the AOI spatial clip (now AOI nodes + keep_ids). The full implementation
    is preserved verbatim below the early return; delete the early-return block to
    re-enable. See suivi/decision_log.md.
    """
    keep_ids = keep_ids or set()
    # --- TEMPORARY DISABLE: skip node betweenness, keep the AOI clip ---------
    df = df_nodes.copy()
    df['nbc_score'] = np.nan
    if aoi_gdf is not None:
        in_aoi = df.geometry.intersects(aoi_gdf.geometry.union_all())
        df = df[in_aoi | df.index.isin(keep_ids)].copy()
    return df
    # --- preserved implementation below (unreachable while disabled) ---------

    df = df_nodes.copy()

    # 1. Calcul via NetworkX sur tout le graphe (Buffer inclus)
    node_centrality = nx.betweenness_centrality(G_curr, weight='cost_log', normalized=True)
    
    # 2. Assignation des scores bruts 
    df['nbc_score_raw'] = df.index.map(lambda node_id: node_centrality.get(node_id, 0))
    
    # 3. Filtrage spatial : noeuds dans l'AOI + les patches "linked" hors AOI (keep_ids)
    if aoi_gdf is not None:
        in_aoi = df.geometry.intersects(aoi_gdf.geometry.union_all())
        df = df[in_aoi | df.index.isin(keep_ids)].copy()

    # 4. Normalize from 0 to 100 (city AOI)
    max_score = df['nbc_score_raw'].max()
    if max_score > 0:
        df['nbc_score'] = (df['nbc_score_raw'] / max_score) * 100
    else:
        df['nbc_score'] = 0
    df = df.drop(columns=['nbc_score_raw'])
        
    return df.sort_values(by='nbc_score', ascending=False)

def calculate_pinch_points_network(gdf_lcp: gpd.GeoDataFrame, G_curr: nx.Graph) -> gpd.GeoDataFrame:
    """
    Compute pinch points (bottlenecks) via circuit theory (current-flow).
    Vectorial equivalent of Circuitscape.

    DISABLED (2026-06-10): the current-flow solver
    ``nx.edge_current_flow_betweenness_centrality`` is ~O(N^2) memory and ~O(N^3)
    time, so it hangs for hours on the giant connected component of large cities
    (e.g. Toulouse). The pinch-point attribute is not needed for now, so this
    function short-circuits and returns a NaN ``pinch_point_score`` column. The
    full implementation is preserved verbatim below the early return; delete the
    early-return block to re-enable it. See suivi/decision_log.md.
    """
    # --- TEMPORARY DISABLE: skip the expensive current-flow computation -----
    # Keep the column so downstream writers / viz that reference it do not break.
    df = gdf_lcp.copy()
    df['pinch_point_score'] = np.nan
    return df
    # --- preserved implementation below (unreachable while disabled) ---------

    df = gdf_lcp.copy()
    edge_current_flow = {}

    G_clean = G_curr.copy()

    # 1. Remove links with zero or near-zero probability for the matrix inversion
    edges_to_remove = [(u, v) for u, v, d in G_clean.edges(data=True) if d.get('prob', 0) <= 1e-12]
    G_clean.remove_edges_from(edges_to_remove)
    
    # 2. Iterate over the connected components of the graph 
    for comp in nx.connected_components(G_clean):
        subgraph = G_clean.subgraph(comp)
        
        # Il faut au moins 2 noeuds pour qu'un courant circule
        if len(subgraph.nodes) > 1:
            try:
                flows = nx.edge_current_flow_betweenness_centrality(
                    subgraph, 
                    weight='prob', 
                    normalized=True,
                    solver='lu' 
                )
                edge_current_flow.update(flows)
            except Exception as e:
                # micro-composante: avertissement 
                print(f" Skipped: component of {len(subgraph.nodes)} nodes ({e})")

    # 3. Extraire score
    def get_current_flow(row):
        u, v = int(row['node_1']), int(row['node_2'])
        return edge_current_flow.get((u, v)) or edge_current_flow.get((v, u), 0)

    # 4. Assigner score
    df['pinch_point_score'] = df.apply(get_current_flow, axis=1)
    
    # 5. Normalize from 0 to 100
    max_score = df['pinch_point_score'].max()
    if max_score > 0:
        df['pinch_point_score'] = (df['pinch_point_score'] / max_score) * 100
    else:
        df['pinch_point_score'] = 0
        
    return df

def extract_rupture_points(
    gdf_lcp: gpd.GeoDataFrame,
    lc_osm: gpd.GeoDataFrame,
    friction_dict: dict,
    cluster_tolerance: float = 15.0,
    soft_paths: gpd.GeoDataFrame = None
) -> gpd.GeoDataFrame:
    """
    Extract rupture points: crossings between the FAILED corridors and the uncrossable OSM
    obstacles.

    If ``soft_paths`` is given (output of ``routing.soft_retrace_failed``: the failed links
    re-traced over a soft barrier), the realistic least-cost crossing is used in place of the
    straight desire line, so the rupture point lands where the animal would actually try to
    cross. Falls back to the straight line for links without a soft path.
    """
    # 1. Keep only failures caused by barriers
    gdf_failed = gdf_lcp[
        (gdf_lcp['status'] == 'failed') &
        (gdf_lcp['fail_reason'] == 'blocked')
    ].copy()

    empty_gdf = gpd.GeoDataFrame(columns=['pn_id', 'geometry'], crs=gdf_lcp.crs)
    if gdf_failed.empty:
        return empty_gdf

    # 1b. Swap the straight desire line for the soft-retraced least-cost path where available,
    # so the obstacle crossing below is the realistic (cheapest) crossing, not a geometric artefact.
    if soft_paths is not None and not soft_paths.empty:
        sp = {(int(r['node_1']), int(r['node_2'])): r.geometry
              for _, r in soft_paths.iterrows() if r.geometry is not None and not r.geometry.is_empty}
        if sp:
            gdf_failed['geometry'] = [
                sp.get((int(n1), int(n2)), g)
                for n1, n2, g in zip(gdf_failed['node_1'], gdf_failed['node_2'], gdf_failed['geometry'])
            ]

    # 2. Dynamic identification of barriers (excluding buildings (51); water (80) IS included)
    obstacle_codes = [
        k for k, v in friction_dict.items()
        if isinstance(v, float) and np.isnan(v) and str(k) != '51'
    ]
    if not obstacle_codes:
        return empty_gdf
    
    # 3. Filtrage OSM
    obstacles = lc_osm[lc_osm['wc_code'].isin(obstacle_codes)].copy()
    if obstacles.empty:
        return empty_gdf
    
    if obstacles.crs != gdf_failed.crs:
        obstacles = obstacles.to_crs(gdf_failed.crs)

    # 4. Single SJOIN: line (failure) x obstacle
    obstacles_simple   = obstacles[['geometry']].reset_index(drop=True).rename(columns={'geometry': 'obs_geom'})
    obstacles_for_join = obstacles[['wc_code', 'geometry']].reset_index(drop=True)
    failed_simple      = gdf_failed.reset_index(drop=True)

    joined_exact = gpd.sjoin(failed_simple, obstacles_for_join, how='inner', predicate='intersects')
    if joined_exact.empty:
        return empty_gdf
    joined_exact = joined_exact.merge(obstacles_simple, left_on='index_right', right_index=True, how='left')

    # 5. Compute collision centroids (the geographic black spot)
    obstacles_simple = obstacles[['geometry']].reset_index(drop=True).rename(columns={'geometry': 'obs_geom'})
    obstacles_for_join = obstacles[['wc_code', 'geometry']].reset_index(drop=True)
    
    failed_simple = gdf_failed.reset_index(drop=True)
    joined_exact = gpd.sjoin(failed_simple, obstacles_for_join, how='inner', predicate='intersects')
    joined_exact = joined_exact.merge(obstacles_simple, left_on='index_right', right_index=True, how='left')
    
    # L'intersection exacte entre la ligne droite et l'obstacle
    joined_exact['intersection'] = joined_exact.apply(
        lambda r: r['geometry'].intersection(r['obs_geom']), axis=1
    )
    
    # Clean up empty geometries
    joined_exact = joined_exact[~joined_exact['intersection'].is_empty].copy()
    
    # 5. De-aggregated rupture points: ONE point per (failed corridor x obstacle) crossing.
    # The previous clustering merged nearby crossings and kept only the FIRST corridor's
    # node_1/node_2 per cluster (`'first'`), which destroyed the corridor<->rupture link and
    # made an exact barrier enrichment impossible. Here every crossing keeps its exact
    # originating corridor (node_1/node_2) and obstacle code; cluster_tolerance is unused now.
    rupt = joined_exact[['node_1', 'node_2', 'wc_code', 'intersection']].copy()
    rupt['geometry'] = rupt['intersection'].apply(lambda g: g.centroid)
    rupt = gpd.GeoDataFrame(
        rupt.drop(columns=['intersection']).reset_index(drop=True),
        geometry='geometry',
        crs=gdf_lcp.crs,
    )
    rupt['pn_id'] = rupt.index
    return rupt[['pn_id', 'wc_code', 'node_1', 'node_2', 'geometry']]


def enrich_failed_links_with_ruptures(
    gdf_barriers: gpd.GeoDataFrame,
    gdf_ruptures: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Attach obstacle-crossing information from rupture points to failed links.

    Each failed link is matched to the rupture points that share its
    ``(node_1, node_2)`` endpoints (an exact, lossless match now that the rupture points
    are de-aggregated). Two columns are added, the rest of the barrier attributes are kept.

    Parameters
    ----------
    gdf_barriers : gpd.GeoDataFrame
        Failed corridors (``status == 'failed'``), carrying ``node_1`` / ``node_2``.
    gdf_ruptures : gpd.GeoDataFrame
        De-aggregated rupture points with ``node_1`` / ``node_2`` / ``wc_code``.

    Returns
    -------
    gpd.GeoDataFrame
        ``gdf_barriers`` plus:
            - ``obstacle`` : comma-joined sorted unique crossed WorldCover codes
              (e.g. ``'52,53'``); empty string when the barrier crosses no obstacle
              (e.g. an ``out_of_reach`` failure, which is not a physical block).
            - ``n_ruptures`` : number of rupture points on the barrier (0 if none).
    """
    out = gdf_barriers.copy()
    out['obstacle'] = ''
    out['n_ruptures'] = 0
    if gdf_ruptures is None or len(gdf_ruptures) == 0:
        return out

    def _key(u: float, v: float) -> tuple:
        """Order-independent endpoint key (corridors are undirected)."""
        a, b = int(u), int(v)
        return (a, b) if a <= b else (b, a)

    grouped = {}
    for u, v, code in zip(gdf_ruptures['node_1'], gdf_ruptures['node_2'], gdf_ruptures['wc_code']):
        k = _key(u, v)
        bucket = grouped.setdefault(k, {'codes': set(), 'count': 0})
        bucket['count'] += 1
        if code is not None and not (isinstance(code, float) and np.isnan(code)):
            bucket['codes'].add(str(int(code)))

    keys = [_key(u, v) for u, v in zip(out['node_1'], out['node_2'])]
    out['obstacle'] = [','.join(sorted(grouped[k]['codes'])) if k in grouped else '' for k in keys]
    out['n_ruptures'] = [grouped[k]['count'] if k in grouped else 0 for k in keys]
    return out
    

def create_corridor_segments(gdf_lcp: gpd.GeoDataFrame, df_nodes: gpd.GeoDataFrame, tolerance: float = 0.1, buffer_dist: float = 15.0) -> gpd.GeoDataFrame:
    """
    Transform LCP corridors into unique corridor segments (the corridor portions outside habitat patches).
    """
    # 1. Nettoyage des corridors (Accrochage + Gommage)
    habitats_union = df_nodes.geometry.union_all()
    gdf_matrix = gdf_lcp.copy()
    
    # Snap
    new_geoms = []
    for geom in gdf_matrix.geometry:
        if geom is None or geom.is_empty:
            new_geoms.append(geom)
            continue
            
        # Get all the line coordinates
        coords = list(geom.coords)
        start_pt = Point(coords[0])
        end_pt = Point(coords[-1])
        
        # On trouve le point exact le plus proche sur le polygone d'habitat
        # nearest_points renvoie (point_sur_ligne, point_sur_polygone)
        _, snap_start = nearest_points(start_pt, habitats_union)
        _, snap_end = nearest_points(end_pt, habitats_union)
        
        # Add these points to the line endpoints to force contact
        extended_coords = [snap_start.coords[0]] + coords + [snap_end.coords[0]]
        new_geoms.append(LineString(extended_coords))
        
    gdf_matrix['geometry'] = new_geoms
    # -------------------------------------------

    # Erase the parts of each corridor that fall inside habitat patches. Differencing
    # against the full habitat union is O(N * union_size) (the union holds ~10^4 polygons,
    # ~13 min on Toulouse); instead difference each corridor only against the patches it
    # actually intersects, found via a spatial-index join. Result is identical: a corridor
    # is unchanged by patches it does not intersect.
    gdf_matrix = gdf_matrix.reset_index(drop=True)
    nodes_geom = df_nodes.geometry.reset_index(drop=True)
    sj = gpd.sjoin(gdf_matrix[['geometry']], gpd.GeoDataFrame(geometry=nodes_geom),
                   how='inner', predicate='intersects')
    new_geoms = list(gdf_matrix.geometry)
    for cpos, grp in sj.groupby(level=0):
        local = unary_union(nodes_geom.iloc[grp['index_right'].values].values)
        new_geoms[cpos] = gdf_matrix.geometry.iloc[cpos].difference(local)
    gdf_matrix['geometry'] = new_geoms
    gdf_matrix = gdf_matrix[~gdf_matrix.geometry.is_empty].copy()
    
    # Explode the line into all its fragments
    exploded = gdf_matrix.explode(index_parts=False)
    exploded['lcp_id'] = exploded.index  
    exploded = exploded.reset_index(drop=True)

    exploded = exploded[exploded.geometry.geom_type == 'LineString'].copy()
    if exploded.empty:
        return gpd.GeoDataFrame()    

    # --- ARTEFACTS RASE-MURS ---
    # a) Identifier les VRAIS ponts (ceux qui touchent au moins 2 habitats)
    nodes_temp = df_nodes.copy().reset_index(drop=True)
    nodes_temp['node_id'] = nodes_temp.index

    # Mini-buffer de contact (0.1m) juste pour s'assurer que la jointure spatiale capte bien la touche
    frag_buf = gpd.GeoDataFrame(geometry=exploded.geometry.buffer(0.1), crs=exploded.crs)
    touches = gpd.sjoin(frag_buf, nodes_temp[['node_id', 'geometry']], how='inner', predicate='intersects')
    
    # On compte combien d'habitats uniques chaque fragment touche
    num_nodes = touches.groupby(touches.index)['node_id'].nunique()
    exploded['num_nodes'] = exploded.index.map(num_nodes).fillna(0)

    # b) Identify what "skirts the walls" (entirely inside the 15 m buffer). Prepare the
    # buffered union once so each per-fragment containment test is index-accelerated; the
    # plain .within against this single huge geometry was the dominant cost (~64 min on
    # Toulouse). within(B) is equivalent to B.contains(A).
    habitats_buffered = prep(habitats_union.buffer(buffer_dist))
    exploded['is_skirting'] = [habitats_buffered.contains(g) for g in exploded.geometry]

    # c)
    # Est un artefact : Une ligne qui rase les murs (is_skirting = True) ET qui ne connecte pas 2 habitats (num_nodes < 2).
    # Also drop, as a safety, all microscopic slivers under 2 metres.
    mask_artifact = (exploded['is_skirting'] & (exploded['num_nodes'] < 2)) | (exploded.geometry.length < 2.0)

    # On ne garde que ce qui n'est PAS un artefact
    exploded_clean = exploded[~mask_artifact].copy()
    
    # Weld everything back for the next step
    gdf_matrix = exploded_clean.dissolve(by='lcp_id')
    gdf_matrix['geometry'] = gdf_matrix['geometry'].apply(
        lambda g: linemerge(g) if g.geom_type == 'MultiLineString' else g
    )

    # On simplifie les LCP pour tuer le bruit raster (les pixels en escalier).
    # tolerance=2.0 (metres). 
    gdf_matrix['geometry'] = gdf_matrix.geometry.simplify(tolerance=2.0, preserve_topology=True)

    # 2. Topological splitting at intersections
    merged = unary_union(gdf_matrix.geometry.tolist())
    if hasattr(merged, 'geoms'):
        lines = [g for g in merged.geoms if g.geom_type == 'LineString']
        for mg in [g for g in merged.geoms if g.geom_type == 'MultiLineString']:
            lines.extend(list(mg.geoms))
    else:
        lines = [merged]
        
    gdf_segments = gpd.GeoDataFrame(geometry=lines, crs=gdf_lcp.crs)
    gdf_segments['segment_id'] = range(len(gdf_segments))

    # 3. Spatial aggregation of metrics (dPC, EBC, pinch point)
    gdf_seg_buf = gdf_segments.copy()
    gdf_seg_buf.geometry = gdf_segments.geometry.buffer(tolerance)
    join_df = gpd.sjoin(gdf_seg_buf, gdf_matrix, how='left', predicate='intersects')

    metrics = join_df.groupby('segment_id').agg(
        corridor_count=('node_1', 'count'),
        sum_dPC=('dPC_val', 'sum') if 'dPC_val' in join_df.columns else ('node_1', 'count'),
        max_ebc=('ebc_score', 'max') if 'ebc_score' in join_df.columns else ('node_1', 'max'),
        max_pinch_point=('pinch_point_score', 'max') if 'pinch_point_score' in join_df.columns else ('node_1', 'max')
    ).reset_index()
    gdf_final = gdf_segments.merge(metrics, on='segment_id')

    # Define logical rounding rules for the grouping (weld)
    rounding_rules = {
        'sum_dPC': 12,          # 12 decimals so we do not kill the dPC (e.g. 0.000000508736)
        'max_ebc': 3,           # 0-1 scale: 3 decimals are enough (e.g. 0.293)
        'max_pinch_point': 2    # Large scale: 1 decimal is enough to smooth the noise (e.g. 26.9)
    }

    for col, decimals in rounding_rules.items():
        if col in gdf_final.columns:
            # Create the group column with the custom rounding
            gdf_final[f'grp_{col}'] = gdf_final[col].round(decimals)
            
    return gdf_final

def weld_segments(gdf_final: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Weld geometric segments sharing the same attributes"""
    # Only dissolve by grouping keys that actually carry values. When the dPC / ebc /
    # pinch metrics are disabled, their grp_* columns are all NaN; dissolve() runs a
    # groupby that, with the default dropna=True, drops every NaN-keyed row and would
    # silently empty the layer. Keep only grp_* keys with at least one non-NaN value,
    # and pass dropna=False so partially-NaN keys never drop rows either.
    grp_cols = [c for c in gdf_final.columns if 'grp_' in c and gdf_final[c].notna().any()]
    dissolve_cols = ['corridor_count'] + grp_cols

    gdf_clean = gdf_final.dissolve(by=dissolve_cols, dropna=False).reset_index()
    
    # linemerge works perfectly because the smoothed anchor points 
    # have exactly the same floating-point coordinates
    gdf_clean['geometry'] = gdf_clean['geometry'].apply(
        lambda g: linemerge(g) if g.geom_type == 'MultiLineString' else g
    )
    gdf_clean = gdf_clean.explode(index_parts=False).reset_index(drop=True)
    
    cols_to_drop = [c for c in gdf_clean.columns if 'grp_' in c]
    gdf_clean = gdf_clean.drop(columns=cols_to_drop + ['segment_id'], errors='ignore')
    gdf_clean['segment_id'] = range(len(gdf_clean))
    
    return gdf_clean
