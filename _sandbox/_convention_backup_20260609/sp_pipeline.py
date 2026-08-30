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
    guild_key: str, 
    aoi_raw: gpd.GeoDataFrame, 
    CITY: str, 
    OUTPUT_DIR: Union[str, Path],
    lc_wc: xr.DataArray, 
    lc_osm: gpd.GeoDataFrame
) -> None:
    """
    Executes the full spatial processing pipeline to analyze habitat connectivity 
    for a specific ecological guild.

    This function performs a comprehensive series of spatial operations:
    1. Buffers the Area of Interest (AOI) based on the species' dispersal distance.
    2. Clips the master landcover and OSM data to the guild's buffer and generates 
       a species-specific landcover raster.
    3. Identifies morphological connectivity elements (biodiversity cores and stepping stones).
    4. Constructs a Gabriel graph to model theoretical connectivity.
    5. Computes a Least Cost Path (LCP) network over a friction/resistance surface.
    6. Calculates structural and functional connectivity metrics (e.g., dPC, Edge Betweenness 
       Centrality, pinch points, and Probability of Connectivity (PC) indices).
    7. Exports the finalized spatial layers and statistical KPIs to disk.

    Args:
        guild_key (str): The unique identifier for the ecological guild (e.g., 'mammal_edge', 
            'bird_woodland'). Used to retrieve species-specific parameters (like `d0` distance, 
            habitat codes, and friction values) from `spp.SPECIES_CONFIG`.
        aoi_raw (gpd.GeoDataFrame): The raw Area of Interest (AOI) boundaries.
        CITY (str): The name of the city or study area. Used as a suffix for naming output files.
        OUTPUT_DIR (Union[str, Path]): The root directory where outputs will be saved. A specific 
            subdirectory named after the `guild_key` will be created automatically.
        lc_wc (xr.DataArray): The ESA WorldCover raster extracted for the maximum 
            possible buffer extent. Used as the base layer for landcover generation.
        lc_osm (gpd.GeoDataFrame): The OpenStreetMap vector dataset (roads, buildings, 
            waterways) extracted for the maximum possible buffer extent.

    Returns:
        None: The function does not return any objects in memory. Instead, it writes the 
        following directly to the specified `OUTPUT_DIR`:
            - Rasters (.tif): Landcover, binary habitat, and friction/resistance surfaces.
            - Vectors (.json/.geojson): Theoretical edges, LCP corridors, uncrossable barriers 
              (failed paths), aggregated urban planning segments, and network nodes.
            - Statistics (.json): Key Performance Indicators (KPIs) mapping theoretical vs. real 
              connectivity, network tortuosity, and total component counts.
    """
    print(f"--- DÉBUT DU PIPELINE POUR : {guild_key} ---")

    # 1. Configurer les répertoires et récupérer la config
    specie = spp.SPECIES_CONFIG[guild_key]
    # Centralized, typed paths. Derive the project root from the legacy OUTPUT_DIR
    # (= <root>/data/outputs/<CITY>), so the notebook callers stay unchanged.
    paths = CorridorPaths(CITY, project_root=PurePosixPath(OUTPUT_DIR).parents[2])
    guild_dir = paths.init_guild(guild_key)
    
    # 2. Traitement spécifique à la guilde
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
    
    da_lc = lc.generate_guild_landcover(lc_wc, lc_osm, aoi_buffered, utmb_epsg, specie['habitat_codes'])
    da_export = da_lc.fillna(0).astype('uint8')
    da_export.rio.to_raster(paths.landcover_tif(guild_key))

    # Binary habitat
    binary_wc = conn.get_binary_habitat(da_lc, specie['habitat_codes'])
    gdf_cores, gdf_islets = conn.get_connectivity_elements(binary_wc, core_min_ha=1.0, islet_min_ha=0.1)
    gdf_islets = gdf_islets[gdf_islets['class'] == "Stepping Stone (Small Core)"].copy()
    print(f"✓ {len(gdf_cores)} Reservoirs et {len(gdf_islets)} Stepping Stones (Small Cores) identified")
    binary_wc.rio.to_raster(paths.binary_habitat_tif(guild_key))

    # Graph construction
    df_nodes = conn.prepare_graph_nodes(gdf_cores, gdf_islets)
    G = conn.build_gabriel_graph(df_nodes, specie)

    # Lissage des polygones de noeuds
    df_nodes = rout.safe_smooth(df_nodes)
    df_nodes["geometry"] = df_nodes.geometry.buffer(0)
    
    # LCP Network
    pc_value = conn.calculate_pc_index(G, total_area_km2)
    gdf_edges = conn.graph_to_gdf_edges(G, utmb_epsg)
    gdf_edges.to_file(paths.edges_geojson(guild_key), driver='GeoJSON')
    
    resistance_raster = rout.create_resistance_surface(da_lc, specie['friction'])
    resistance_raster.rio.to_raster(paths.friction_tif(guild_key))

    threshold = d0 * spp.FRICTION_AVG_FAVORABLE
    gdf_lcp = rout.compute_lcp_network(gdf_edges, df_nodes, da_lc, specie['friction'], max_cost_threshold=threshold)

    # Dispersal surface (coût cumulé depuis les habitats), clippée à l'AOI ville.
    disp = rout.compute_dispersal_surface(da_lc, df_nodes, specie['friction'])
    disp_city = disp.rio.clip(aoi_utm.geometry, aoi_utm.crs, drop=True)
    disp_city.rio.to_raster(paths.dispersal_tif(guild_key))

    gdf_lcp_city = gdf_lcp[gdf_lcp.geometry.intersects(aoi_utm.union_all())].copy() # on coupe le buffer
 
    # Points de rupture : corridors failed croisés au réseau OSM.
    gdf_ruptures = conn.extract_rupture_points(gdf_lcp=gdf_lcp_city, lc_osm=lc_osm, friction_dict=specie['friction'])
    if not gdf_ruptures.empty:
        gdf_ruptures.to_file(paths.ruptures_geojson(guild_key), driver='GeoJSON')
        
    #enregister  patchs isolés
    gdf_lcp_city_failed = gdf_lcp_city[gdf_lcp_city['status'] == 'failed'].copy()
    gdf_lcp_city = gdf_lcp_city[gdf_lcp_city['status'] == 'success'].copy()
    if not gdf_lcp_city_failed.empty:
        gdf_lcp_city_failed.to_file(paths.barriers_geojson(guild_key), driver='GeoJSON')

    G_success = nx.from_pandas_edgelist(gdf_lcp_city, 'node_1', 'node_2')
    G_success.add_nodes_from(df_nodes.index) # Ajoute tous les nœuds de l'étude
    isolated_nodes_list = list(nx.isolates(G_success))
    df_isolated_nodes = df_nodes[df_nodes.index.isin(isolated_nodes_list)].copy()
    df_isolated_nodes_city = df_isolated_nodes[df_isolated_nodes.geometry.intersects(aoi_utm.union_all())].copy()
    if not df_isolated_nodes_city.empty:
            df_isolated_nodes_city.to_file(paths.isolated_nodes_geojson(guild_key), driver='GeoJSON')
    
    gdf_lcp_city['tortuosity'] = gdf_lcp_city['real_dist'] / gdf_lcp_city['theoretical_dist']

    G_pc = nx.from_pandas_edgelist(gdf_lcp, 'node_1', 'node_2')
    G_pc.add_nodes_from(G.nodes(data=True))   # include distance-isolated patches (self-term aᵢ²/A²) -> denominator independent of 2·d0
    for node in G_pc.nodes():
        if node in G:
            G_pc.nodes[node].update(G.nodes[node])
    pc_real, G_lcp = conn.calculate_pc_index_lcp(G_pc, total_area_km2, specie, gdf_lcp)

    # Metrics: dPC, ebc, current_flow
    gdf_lcp_city = conn.calculate_edge_dpc(gdf_lcp_city, G_lcp, total_area_km2, pc_real)
    gdf_lcp_city = conn.calculate_edge_betweenness(gdf_lcp_city, G_lcp)
    gdf_lcp_city = conn.classify_corridors(gdf_lcp_city, 0.75)
    gdf_lcp_city = conn.calculate_pinch_points_network(gdf_lcp_city, G_lcp)
    gdf_lcp_city.to_file(paths.lcp_geojson(guild_key), driver='GeoJSON')
    
    # From LCP to corridors for management, urban planning segments
    gdf_urbanplan_segments_raw = conn.create_urban_planning_segments(gdf_lcp_city, df_nodes)
    gdf_urbanplan_segments_smoothed = rout.safe_smooth_lines(gdf_urbanplan_segments_raw)
    gdf_urbanplan_segments = conn.weld_segments(gdf_urbanplan_segments_smoothed)
    gdf_urbanplan_segments.to_file(paths.segments_geojson(guild_key), driver='GeoJSON')
    # da_heatmap = conn.lcp_heatmap(gdf_lcp_city, aoib_utm, res=10, crs_utm=utm_epsg)
    # da_heatmap.rio.to_raster(f"{guild_dir}/heatmap_{guild_key}_{CITY}.tif")

    # Nodes Metrics
    df_nodes = conn.calculate_node_betweenness(df_nodes, G_lcp, aoi_utm)
    df_nodes.to_file(paths.nodes_geojson(guild_key), driver='GeoJSON')

    # KPIs
    stats = {
    "nb_nodes": int(len(df_nodes)),
    "isolated_nodes_count": int(len(df_isolated_nodes_city)),
    "cores_count": int(len(gdf_cores)),
    "islets_count": int(len(gdf_islets)),
    "nb_corridors": int(len(gdf_lcp_city)),
    "nb_failed_corridors": int(len(gdf_lcp_city_failed)),
    "pc_theory": float(pc_value),
    "pc_real": float(pc_real),
    "connectivity_loss_pct": float((pc_value - pc_real) / pc_value * 100) if pc_value > 0 else 0,
    "median_tortuosity": float(gdf_lcp_city['tortuosity'].median()),
    "mean_tortuosity": float(gdf_lcp_city['tortuosity'].mean())
}

    pd.DataFrame([stats]).to_csv(paths.stats_csv(guild_key), index=False)

    print(f"--- FIN : Results saved in {guild_dir} ---")