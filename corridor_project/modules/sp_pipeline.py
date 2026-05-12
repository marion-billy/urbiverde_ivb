import os
import geopandas as gpd
import xarray as xr
from shapely.geometry import LineString
from rasterio import features
import json
import networkx as nx
import sys
sys.path.insert(1, '../../marion/corridor_project/config/')
import species_params
sys.path.insert(1, '../../marion/corridor_project/modules/')
import importlib
import landcover as lc
importlib.reload(lc)
import connectivity as conn
import routing as rout

def sp_pipeline(guild_key, aoi_raw,  CITY, OUTPUT_DIR):
    print(f"--- DÉBUT DU PIPELINE POUR : {guild_key} ---")

    # 1. Configurer les répertoires et récupérer la config
    specie = species_params.SPECIES_CONFIG[guild_key]
    guild_dir = f"{OUTPUT_DIR}/{guild_key}"
    os.makedirs(guild_dir, exist_ok=True)
    
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
    
    da_lc = lc.get_city_landcover(aoib_ee, aoib_utm, aoi_buffered, utmb_epsg, specie['habitat_codes'])
    da_export = da_lc.fillna(0).astype('uint8')
    da_export.rio.to_raster(f"{guild_dir}/landcover_{guild_key}_{CITY}.tif")

    # Binary habitat
    binary_wc = conn.get_binary_habitat(da_lc, specie['habitat_codes'])
    gdf_cores, gdf_islets = conn.get_connectivity_elements(binary_wc, core_min_ha=1.0, islet_min_ha=0.1)
    gdf_islets = gdf_islets[gdf_islets['class'] == "Stepping Stone (Small Core)"].copy()
    print(f"✓ {len(gdf_cores)} Reservoirs et {len(gdf_islets)} Stepping Stones (Small Cores) identified")
    binary_wc.rio.to_raster(f"{guild_dir}/binary_habitat_{guild_key}_{CITY}.tif")

    # Graph construction
    df_nodes = conn.prepare_graph_nodes(gdf_cores, gdf_islets)
    G = conn.build_gabriel_graph(df_nodes, specie)
    
    # LCP Network
    pc_value = conn.calculate_pc_index(G, total_area_km2)
    gdf_edges = conn.graph_to_gdf_edges(G, utmb_epsg)
    gdf_edges.to_file(f"{guild_dir}/edges_{guild_key}_{CITY}.json", driver='GeoJSON')
    
    resistance_raster = rout.create_resistance_surface(da_lc, specie['friction'])
    resistance_raster.rio.to_raster(f"{guild_dir}/friction_{guild_key}_{CITY}.tif")

    threshold = 3 * d0
    gdf_lcp = rout.compute_lcp_network(gdf_edges, df_nodes, da_lc, specie['friction'], max_cost_threshold=threshold)
    gdf_lcp_city = gdf_lcp[gdf_lcp.geometry.intersects(aoi_utm.unary_union)].copy()
    #enregister  patchs isolés
    gdf_lcp_city_failed = gdf_lcp_city[gdf_lcp_city['status'] == 'failed'].copy()
    gdf_lcp_city = gdf_lcp_city[gdf_lcp_city['status'] == 'success'].copy()
    if not gdf_lcp_city_failed.empty:
        gdf_lcp_city_failed.to_file(f"{guild_dir}/barriers_{guild_key}_{CITY}.json", driver='GeoJSON')
    gdf_lcp_city['tortuosity'] = gdf_lcp_city['real_dist'] / gdf_lcp_city['theoretical_dist']

    G_success = nx.from_pandas_edgelist(gdf_lcp, 'node_1', 'node_2')
    for node in G_success.nodes():
        if node in G:
            G_success.nodes[node].update(G.nodes[node])
    pc_real, G_lcp = conn.calculate_pc_index_lcp(G_success, total_area_km2, specie, gdf_lcp)

    # Metrics: dPC, ebc, current_flow
    gdf_lcp_city = conn.calculate_edge_dpc(gdf_lcp_city, G_lcp, total_area_km2, pc_real)
    gdf_lcp_city = conn.calculate_edge_betweenness(gdf_lcp_city, G_lcp)
    gdf_lcp_city = conn.classify_corridors(gdf_lcp_city, 0.75)
    gdf_lcp_city = conn.calculate_pinch_points_network(gdf_lcp_city, G_lcp)
    gdf_lcp_city.to_file(f"{guild_dir}/lcp_{guild_key}_{CITY}.json", driver='GeoJSON')
    
    # From LCP to corridors for management, urban planning segments
    gdf_urbanplan_segments = conn.create_urban_planning_segments(gdf_lcp_city, df_nodes)
    gdf_urbanplan_segments.to_file(f"{guild_dir}/segments_amenagement_{guild_key}_{CITY}.json", driver='GeoJSON')
    # da_heatmap = conn.lcp_heatmap(gdf_lcp_city, aoib_utm, res=10, crs_utm=utm_epsg)
    # da_heatmap.rio.to_raster(f"{guild_dir}/heatmap_{guild_key}_{CITY}.tif")

    # Nodes Metrics
    df_nodes = conn.calculate_node_betweenness(df_nodes, G_lcp, aoi_utm)
    df_nodes.to_file(f"{OUTPUT_DIR}/nodes_{CITY}.geojson", driver='GeoJSON')

    # KPIs
    stats = {
    "nb_nodes": int(len(df_nodes)),
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

    with open(f"{guild_dir}/stats_{guild_key}_{CITY}.json", 'w') as f:
        json.dump(stats, f, indent=4)
    
    print(f"--- FIN : Résultats sauvegardés dans {guild_dir} ---")