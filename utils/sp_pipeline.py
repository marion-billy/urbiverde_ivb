import os
import geopandas as gpd
import pandas as pd
import xarray as xr
from shapely.geometry import LineString
from rasterio import features
import networkx as nx
import sys
sys.path.insert(1, '../../marion/corridor_project/utils/')
import species_params as spp
sys.path.insert(1, '../../marion/corridor_project/utils/')
import importlib
import landcover as lc
importlib.reload(lc)
import connectivity as conn
import routing as rout
# Node smoothing uses routing.safe_smooth (smoothify-based, index-preserving). We no
# longer import the geoai-dependent canonical safe_smooth from a_b_c_functions, which
# is what let us drop the 6.6 GB my_custom_libs/geoai stack.
from typing import Union
from pathlib import Path, PurePosixPath
from paths import CorridorPaths

def sp_pipeline(
    ecoprofil_key: str, 
    aoi_raw: gpd.GeoDataFrame, 
    CITY: str, 
    OUTPUT_DIR: Union[str, Path],
    lc_wc: xr.DataArray, 
    lc_osm: gpd.GeoDataFrame
) -> None:
    """
    Executes the full spatial processing pipeline to analyze habitat connectivity 
    for a specific ecological ecoprofil.

    This function performs a comprehensive series of spatial operations:
    1. Buffers the Area of Interest (AOI) based on the species' dispersal distance.
    2. Clips the master landcover and OSM data to the ecoprofil's buffer and generates 
       a species-specific landcover raster.
    3. Identifies morphological connectivity elements (biodiversity cores and stepping stones).
    4. Constructs a Gabriel graph to model theoretical connectivity.
    5. Computes a Least Cost Path (LCP) network over a friction/resistance surface.
    6. Calculates structural and functional connectivity metrics (e.g., dPC, Edge Betweenness 
       Centrality, pinch points, and Probability of Connectivity (PC) indices).
    7. Exports the finalized spatial layers and statistical KPIs to disk.

    Parameters
    ----------
    ecoprofil_key : str
        Unique identifier for the ecological ecoprofil (e.g., 'ground_mammal',
        'forest_edge_bird'). Used to retrieve species-specific parameters (like `d0`
        distance, habitat codes, and friction values) from `spp.SPECIES_CONFIG`.
    aoi_raw : gpd.GeoDataFrame
        Raw Area of Interest (AOI) boundaries.
    CITY : str
        Name of the city or study area. Used as a suffix for naming output files.
    OUTPUT_DIR : Union[str, Path]
        Root output directory (`<root>/data/outputs/<CITY>`). A subdirectory named
        after `ecoprofil_key` is created automatically.
    lc_wc : xr.DataArray
        ESA WorldCover raster extracted for the maximum possible buffer extent. Base
        layer for land-cover generation.
    lc_osm : gpd.GeoDataFrame
        OpenStreetMap vector dataset (roads, buildings, waterways) extracted for the
        maximum possible buffer extent.

    Returns
    -------
    None
        Returns nothing in memory. Writes directly under the ecoprofil output directory:
            - Rasters (.tif): land cover, binary habitat, friction/resistance, dispersal.
            - Vectors (.geojson): theoretical edges, LCP corridors, uncrossable barriers
              (failed paths), rupture points, aggregated corridor segments, nodes,
              isolated nodes.
            - Statistics (.csv): Key Performance Indicators (KPIs) mapping theoretical vs.
              real connectivity, network tortuosity, and component counts.
    """
    print(f"--- PIPELINE START FOR: {ecoprofil_key} ---")

    # Per-step timing (temporary instrumentation): prints the wall time of each heavy
    # step so the bottleneck is visible. Remove the _lap(...) calls to silence.
    import time
    _tprev = time.perf_counter()

    def _lap(label: str) -> None:
        nonlocal _tprev
        now = time.perf_counter()
        print(f"  ⏱ {label}: {now - _tprev:.1f}s")
        _tprev = now

    # 1. Set up directories and fetch the config
    specie = spp.SPECIES_CONFIG[ecoprofil_key]
    # Centralized, typed paths. Derive the project root from the legacy OUTPUT_DIR
    # (= <root>/data/outputs/<CITY>), so the notebook callers stay unchanged.
    paths = CorridorPaths(CITY, project_root=PurePosixPath(OUTPUT_DIR).parents[2])
    ecoprofil_dir = paths.init_ecoprofil(ecoprofil_key)
    
    # 2. Ecoprofil-specific processing
    # Landcover
    aoi_utm, aoi_ee, utm_epsg = lc.setup_aoi(aoi_raw)
    total_area_km2 = aoi_utm.area.sum() / 1e6

    d0 = specie['graph']['d0']
    aoi_buffered_geom = gpd.GeoSeries(aoi_utm.buffer(2 * d0), crs=utm_epsg).to_crs(aoi_raw.crs)
    aoi_buffered = aoi_raw.copy()
    aoi_buffered.geometry = aoi_buffered_geom
    aoi_buffered = aoi_buffered.dissolve()
    aoib_utm, aoib_ee, utmb_epsg = lc.setup_aoi(aoi_buffered)
    total_areab_km2 = aoib_utm.area.sum() / 1e6
    
    da_lc = lc.generate_ecoprofil_landcover(lc_wc, lc_osm, aoi_buffered, utmb_epsg, specie['habitat_codes'])
    da_export = da_lc.fillna(0).astype('uint8')
    da_export.rio.to_raster(paths.landcover_tif(ecoprofil_key))

    # Binary habitat
    binary_wc = conn.get_binary_habitat(da_lc, specie['habitat_codes'])
    gdf_cores, gdf_islets = conn.get_connectivity_elements(binary_wc, core_min_ha=1.0, islet_min_ha=0.1)
    gdf_islets = gdf_islets[gdf_islets['class'] == "Stepping Stone (Small Core)"].copy()
    print(f"✓ {len(gdf_cores)} Reservoirs and {len(gdf_islets)} Stepping Stones (Small Cores) identified")
    binary_wc.rio.to_raster(paths.binary_habitat_tif(ecoprofil_key))

    # Graph construction
    df_nodes = conn.prepare_graph_nodes(gdf_cores, gdf_islets)
    # Explicit CRS guard: the binary-habitat -> raster_to_polygon -> concat chain does not
    # always propagate the CRS (geopandas/rioxarray version dependent). Geometries are in the
    # buffered UTM grid, so stamp it back so downstream .to_crs (dispersal, segments) works.
    if df_nodes.crs is None:
        df_nodes = df_nodes.set_crs(utmb_epsg)
    _lap("prepare nodes")
    G = conn.build_gabriel_graph(df_nodes, specie)
    _lap("build_gabriel_graph")

    # PC weighting: weight each patch by its area INSIDE the strict AOI (out-of-AOI buffer
    # patches keep 0 area, so they stay routing conduits only). This keeps PC a [0,1] territory
    # probability instead of the buffer-inflated value (numerator on the buffer, denominator on
    # the strict AOI). Connectivity/routing is unchanged; exported patch geometries and
    # total_area_ha are untouched. Flows through G -> G_pc -> G_lcp, so PC theory AND real use it.
    in_aoi_area_ha = df_nodes.geometry.intersection(aoi_utm.union_all()).area / 1e4
    for nid in G.nodes:
        G.nodes[nid]['area'] = float(in_aoi_area_ha.get(nid, 0.0))

    # Smooth node polygons (index-stable: keeps every node, only geometry changes)
    df_nodes = rout.safe_smooth(df_nodes)
    _lap("safe_smooth (nodes)")

    # Materialize the graph node id (= df_nodes.index) as a column so it survives the
    # GeoJSON export (which drops the pandas index). LCP node_1/node_2, ruptures and
    # barriers all reference this id; without it the dashboard cannot link a rupture/
    # barrier to the habitat patches it sits between. Set here (before the isolated-nodes
    # subset and the nodes export) so both nodes_*.geojson and isolated_nodes_*.geojson
    # carry it; it flows through the AOI clip / betweenness copy (left index preserved).
    df_nodes['node_id'] = df_nodes.index

    # LCP Network
    pc_value = conn.calculate_pc_index(G, total_area_km2)
    _lap("calculate_pc_index (theory)")
    gdf_edges = conn.graph_to_gdf_edges(G, utmb_epsg)
    # The full graph (city + buffer) is kept in memory for the LCP computation below, but the
    # exported file is clipped to the AOI: keep an edge only if a part of it touches the city
    # (intersects), so the displayed graph matches the displayed corridors and no buffer-only
    # link is shown. Same rule as the lcp/segments layers.
    aoi_edges = aoi_utm.to_crs(gdf_edges.crs).union_all()
    gdf_edges_city = gdf_edges[gdf_edges.geometry.intersects(aoi_edges)].copy()
    gdf_edges_city.to_file(str(paths.edges_geojson(ecoprofil_key)), driver='GeoJSON')

    resistance_raster = rout.create_resistance_surface(da_lc, specie['friction'])
    resistance_raster.rio.to_raster(paths.friction_tif(ecoprofil_key))

    threshold = d0 * spp.FRICTION_AVG_FAVORABLE
    gdf_lcp = rout.compute_lcp_network(gdf_edges, df_nodes, da_lc, specie['friction'], max_cost_threshold=threshold)
    _lap("compute_lcp_network (tracing)")

    # Dispersal surface (cumulative cost from habitats), clipped to the city AOI.
    disp = rout.compute_dispersal_surface(da_lc, df_nodes, specie['friction'])
    _lap("compute_dispersal_surface")
    disp_city = disp.rio.clip(aoi_utm.geometry, aoi_utm.crs, drop=True)
    disp_city.rio.to_raster(paths.dispersal_tif(ecoprofil_key))
    # Bounded variant: keep only the area reachable within the dispersal budget
    # (`threshold` = d0 * FRICTION_AVG_FAVORABLE, the same cost ceiling as the LCP success
    # threshold; CEREMA "carte de dispersion" reach). Derived by masking the continuous surface
    # (pixels beyond the budget -> NaN), so no second cost flood is computed.
    disp_bounded = disp_city.where(disp_city <= threshold)
    disp_bounded.rio.write_crs(disp_city.rio.crs, inplace=True)
    disp_bounded.rio.to_raster(paths.dispersal_bounded_tif(ecoprofil_key))

    gdf_lcp_city = gdf_lcp[gdf_lcp.geometry.intersects(aoi_utm.union_all())].copy() # clip off the buffer
 
    # Failed links = status 'failed': out_of_reach (route exists but beyond the dispersal
    # budget), blocked (hard obstacle), node_not_found (technical). For the blocked links we
    # re-trace over a soft barrier (100) so (a) the rupture point lands at the realistic
    # (cheapest) crossing and (b) the blocked link carries that real terrain-following geometry
    # instead of the straight desire line. The full failed_links layer is kept (analytical);
    # the dashboard renders only the blocked subset (see prep_for_dashboard).
    _blocked = gdf_lcp_city[(gdf_lcp_city['status'] == 'failed') &
                            (gdf_lcp_city['fail_reason'] == 'blocked')]
    soft_paths = rout.soft_retrace_failed(_blocked, df_nodes, da_lc, specie['friction'])
    gdf_ruptures = conn.extract_rupture_points(gdf_lcp=gdf_lcp_city, lc_osm=lc_osm,
                                               friction_dict=specie['friction'], soft_paths=soft_paths)

    gdf_lcp_city_failed = gdf_lcp_city[gdf_lcp_city['status'] == 'failed'].copy()
    gdf_lcp_city = gdf_lcp_city[gdf_lcp_city['status'] == 'success'].copy()
    if not gdf_lcp_city_failed.empty:
        # Swap each blocked link's straight desire line for its soft-retraced real route (kept,
        # not discarded). Order-independent (node_1, node_2) key since links are undirected.
        if soft_paths is not None and not soft_paths.empty:
            _soft = {(min(int(a), int(b)), max(int(a), int(b))): g
                     for a, b, g in zip(soft_paths['node_1'], soft_paths['node_2'], soft_paths.geometry)
                     if g is not None and not g.is_empty}
            if _soft:
                gdf_lcp_city_failed['geometry'] = [
                    _soft.get((min(int(a), int(b)), max(int(a), int(b))), g)
                    for a, b, g in zip(gdf_lcp_city_failed['node_1'], gdf_lcp_city_failed['node_2'],
                                       gdf_lcp_city_failed.geometry)
                ]
        # Enrich each failed link with the obstacle(s) it crosses ('obstacle' wc_codes) and the
        # number of rupture points on it ('n_ruptures'); exact (node_1, node_2) match. out_of_reach
        # links cross no obstacle (obstacle='' / 0); only blocked links carry ruptures.
        gdf_lcp_city_failed = conn.enrich_failed_links_with_ruptures(gdf_lcp_city_failed, gdf_ruptures)
        gdf_lcp_city_failed.to_file(str(paths.failed_links_geojson(ecoprofil_key)), driver='GeoJSON')
    # Rupture points as their own layer (points where a blocked link crosses its obstacle).
    if gdf_ruptures is not None and not gdf_ruptures.empty:
        gdf_ruptures.to_file(str(paths.rupture_points_geojson(ecoprofil_key)), driver='GeoJSON')

    G_success = nx.from_pandas_edgelist(gdf_lcp_city, 'node_1', 'node_2')
    G_success.add_nodes_from(df_nodes.index) # Add all study nodes
    isolated_nodes_list = list(nx.isolates(G_success))
    df_isolated_nodes = df_nodes[df_nodes.index.isin(isolated_nodes_list)].copy()
    # A node with any part outside the AOI must not be flagged isolated (it is a boundary/buffer
    # patch, not a city patch). Use 'within' (fully inside) instead of 'intersects'.
    df_isolated_nodes_city = df_isolated_nodes[df_isolated_nodes.geometry.within(aoi_utm.union_all())].copy()
    if not df_isolated_nodes_city.empty:
            df_isolated_nodes_city.to_file(str(paths.isolated_nodes_geojson(ecoprofil_key)), driver='GeoJSON')
    
    # Tortuosity = realized length / straight-line length. Degenerate corridors (near-adjacent
    # patches whose theoretical_dist ~ 0) blow up to inf; exclude them from the statistic (NaN).
    gdf_lcp_city['tortuosity'] = (
        gdf_lcp_city['real_dist'] / gdf_lcp_city['theoretical_dist']
    ).replace([float('inf'), float('-inf')], float('nan'))

    G_pc = nx.from_pandas_edgelist(gdf_lcp, 'node_1', 'node_2')
    G_pc.add_nodes_from(G.nodes(data=True))   # include distance-isolated patches (self-term ai^2/A^2) -> denominator independent of 2*d0
    for node in G_pc.nodes():
        if node in G:
            G_pc.nodes[node].update(G.nodes[node])
    pc_real, G_lcp = conn.calculate_pc_index_lcp(G_pc, total_area_km2, specie, gdf_lcp)
    _lap("calculate_pc_index_lcp (real)")

    # Metrics: dPC, ebc, current_flow
    gdf_lcp_city = conn.calculate_edge_dpc(gdf_lcp_city, G_lcp, total_area_km2, pc_real)
    gdf_lcp_city = conn.calculate_edge_betweenness(gdf_lcp_city, G_lcp)
    gdf_lcp_city = conn.classify_corridors(gdf_lcp_city, 0.75)
    gdf_lcp_city = conn.calculate_pinch_points_network(gdf_lcp_city, G_lcp)
    gdf_lcp_city.to_file(str(paths.lcp_geojson(ecoprofil_key)), driver='GeoJSON')
    _lap("edge metrics (dPC/ebc/classify/pinch)")

    # From LCP to corridor segments (corridor portions outside habitat patches, aggregated by overlap)
    gdf_urbanplan_segments_raw = conn.create_corridor_segments(gdf_lcp_city, df_nodes)
    gdf_urbanplan_segments_smoothed = rout.safe_smooth_lines(gdf_urbanplan_segments_raw)
    gdf_urbanplan_segments = conn.weld_segments(gdf_urbanplan_segments_smoothed)
    # Clip to the AOI like the other layers: drop any segment lying entirely in the buffer,
    # keep whole any segment that touches the city (intersects).
    aoi_seg = aoi_utm.to_crs(gdf_urbanplan_segments.crs).union_all()
    gdf_urbanplan_segments = gdf_urbanplan_segments[gdf_urbanplan_segments.geometry.intersects(aoi_seg)].copy()
    gdf_urbanplan_segments.to_file(str(paths.segments_geojson(ecoprofil_key)), driver='GeoJSON')
    _lap("segments (safe_smooth_lines + weld)")
    # da_heatmap = conn.lcp_heatmap(gdf_lcp_city, aoib_utm, res=10, crs_utm=utm_epsg)
    # da_heatmap.rio.to_raster(f"{ecoprofil_dir}/heatmap_{ecoprofil_key}_{CITY}.tif")

    # Nodes Metrics
    # Keep, on top of the AOI nodes, the out-of-AOI (buffer) patches that are an endpoint
    # of a kept line (edge / corridor / barrier), so every displayed line terminates on a
    # visible habitat instead of dead-ending at the AOI edge. Based on the clipped edges, the
    # superset of the displayed line layers.
    linked_ids = set(gdf_edges_city['node_1']).union(gdf_edges_city['node_2'])

    # Sub-networks: connected components of the REALIZED (post-barrier) network. G_success
    # already holds the success corridors that touch the AOI, over all study nodes. Count the
    # components on this true graph (NOT a subgraph induced on AOI-only nodes: that would
    # re-create the fake dead-ends the buffer-keep logic avoids), then keep only the
    # components that touch the displayed node set (AOI nodes + kept buffer endpoints, same
    # rule as the nodes export below). A patch linked to a kept out-of-AOI patch therefore
    # stays in its real sub-network. subnetwork_id labels multi-node sub-networks (>=2
    # patches); singletons (isolated or kept-but-unrealized) stay null and are covered by
    # isolated_nodes.
    aoi_geom = aoi_utm.union_all()
    in_aoi_ids = set(df_nodes[df_nodes.geometry.intersects(aoi_geom)].index)
    displayed_ids = set(df_nodes[df_nodes.geometry.intersects(aoi_geom) | df_nodes.index.isin(linked_ids)].index)

    def _subnetworks(graph):
        """Sub-networks of ``graph``: connected components with >=3 patches inside the AOI.

        Connectivity is read on the true ``graph`` (a patch linked to a kept out-of-AOI
        neighbour stays in its sub-network, no fake split), but the size and the >=3
        threshold count only patches inside the AOI (``in_aoi_ids``), so the metric matches
        the AOI-clipped dashboard view: a component sitting entirely in the kept out-of-AOI
        ring has 0 in-AOI patches, is not counted, and leaves no id gap when the dashboard
        clips. The id is still written on the ring members of a counted component (they keep
        their sub-network id in the file); only the count and size ignore them. A sub-network
        needs at least 3 in-AOI patches; smaller groups (isolated patches or a lone pair) get
        no subnetwork_id.
        Returns ``(labels {node_id: subnetwork_id}, sizes [int])``."""
        min_patches = 3
        labels, sizes = {}, []
        for comp in nx.connected_components(graph):
            core = comp & in_aoi_ids
            if len(core) >= min_patches:
                sizes.append(len(core))
                for nid in comp & displayed_ids:
                    labels[nid] = len(sizes)
        return labels, sizes

    # Realized (post-barrier) vs theoretical (pre-barrier) sub-networks, both on the AOI link
    # set so the difference isolates the fragmenting effect of the barriers: realized = the
    # success corridors (G_success), theoretical = the kept Gabriel edges (gdf_edges_city, the
    # same links before any failed). Using the full buffered Gabriel graph G for theory would
    # merge displayed patches through buffer-only links and under-count the potential sub-networks.
    G_theory = nx.from_pandas_edgelist(gdf_edges_city, 'node_1', 'node_2')
    subnet_id, sub_sizes = _subnetworks(G_success)
    _, sub_sizes_theory = _subnetworks(G_theory)
    df_nodes['subnetwork_id'] = df_nodes.index.map(subnet_id.get)
    n_subnetworks = len(sub_sizes)
    largest_subnetwork_size = max(sub_sizes) if sub_sizes else 0
    n_subnetworks_theory = len(sub_sizes_theory)

    df_nodes = conn.calculate_node_betweenness(df_nodes, G_lcp, aoi_utm, keep_ids=linked_ids)
    df_nodes.to_file(str(paths.nodes_geojson(ecoprofil_key)), driver='GeoJSON')
    _lap("calculate_node_betweenness")

    # KPIs. The "*_in_aoi" entries are derived stats clipped to the city AOI (buffer excluded),
    # matching the dashboard's in-AOI view; they were previously recomputed in prep_for_dashboard.
    aoi_total_ha = float(aoi_utm.area.sum() / 1e4)
    habitat_ha_in_aoi = float(df_nodes.geometry.intersection(aoi_geom).area.sum() / 1e4)
    nodes_in_aoi = df_nodes[df_nodes.index.isin(in_aoi_ids)]
    # Planner-facing connectivity KPIs, derived from PC (which weights each patch by its in-AOI
    # area -> these share the in-AOI basis, consistent with habitat_ha_in_aoi = sum of those areas).
    # EC = equivalent connected area: the size of a single fully-connected patch that yields the
    # same PC, i.e. PC expressed as tangible hectares (EC = sqrt(PC) * AOI area). connected_habitat_pct
    # = EC as a share of in-AOI habitat = "how much of the habitat functions as connected" (0-100,
    # linear, bounded since EC <= habitat). These are the headline (a % loss of an abstract index was
    # unintuitive for planners); loss is read in ha as ec_theory_ha - ec_real_ha.
    ec_theory_ha = (pc_value ** 0.5) * aoi_total_ha
    ec_real_ha = (pc_real ** 0.5) * aoi_total_ha
    connected_habitat_pct = (ec_real_ha / habitat_ha_in_aoi * 100) if habitat_ha_in_aoi > 0 else 0.0
    stats = {
    "nb_nodes": int(len(df_nodes)),
    "isolated_nodes_count": int(len(df_isolated_nodes_city)),
    "cores_count": int(len(gdf_cores)),
    "islets_count": int(len(gdf_islets)),
    "n_subnetworks_theory": int(n_subnetworks_theory),
    "n_subnetworks": int(n_subnetworks),
    "subnetworks_split_by_failed_links": int(n_subnetworks - n_subnetworks_theory),
    "largest_subnetwork_size": int(largest_subnetwork_size),
    "nb_corridors": int(len(gdf_lcp_city)),
    "nb_failed_corridors": int(len(gdf_lcp_city_failed)),
    "pc_theory": float(pc_value),
    "pc_real": float(pc_real),
    "ec_theory_ha": round(ec_theory_ha, 1),
    "ec_real_ha": round(ec_real_ha, 1),
    "connected_habitat_pct": round(connected_habitat_pct, 1),
    "median_tortuosity": float(gdf_lcp_city['tortuosity'].median()),
    "mean_tortuosity": float(gdf_lcp_city['tortuosity'].mean()),
    "aoi_total_ha": round(aoi_total_ha, 1),
    "habitat_ha_in_aoi": round(habitat_ha_in_aoi, 1),
    "habitat_coverage_pct": round(habitat_ha_in_aoi / aoi_total_ha * 100, 1) if aoi_total_ha > 0 else 0.0,
    "nodes_in_aoi": int(len(in_aoi_ids)),
    "cores_in_aoi": int((nodes_in_aoi['node_type'] == 'core').sum()),
    "islets_in_aoi": int((nodes_in_aoi['node_type'] == 'islet').sum()),
}

    pd.DataFrame([stats]).to_csv(paths.stats_csv(ecoprofil_key), index=False)

    # World read/write on the produced files: the Jupyter kernel runs as root, so without
    # this teammates (non-root) hit "Permission denied" on these outputs. -R a+rwX gives
    # dirs +x (traversable) and files +rw, per the convention. Parent dirs kept traversable.
    import subprocess
    subprocess.run(["chmod", "-R", "a+rwX", str(ecoprofil_dir)], check=False)
    subprocess.run(["chmod", "a+rwX", str(paths.city_dir), str(paths.outputs)], check=False)
    _lap("chmod outputs")

    print(f"--- DONE: Results saved in {ecoprofil_dir} ---")