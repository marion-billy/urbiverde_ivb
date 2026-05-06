import os
import geopandas as gpd
import xarray as xr
from shapely.geometry import LineString
from rasterio import features
import sys
sys.path.insert(1, '../../marion/corridor_project/config/')
import species_params
sys.path.insert(1, '../../marion/corridor_project/modules/')
import importlib
import landcover as lc
importlib.reload(lc)
import connectivity as conn
import routing as rout

def sp_pipeline(guild_key, aoi_utm, da_lc, utm_epsg, aoi_raw, total_area_km2, CITY, OUTPUT_DIR):
    print(f"--- DÉBUT DU PIPELINE POUR : {guild_key} ---")

    # 1. Configurer les répertoires et récupérer la config
    specie = species_params.SPECIES_CONFIG[guild_key]
    guild_dir = f"{OUTPUT_DIR}/{guild_key}"
    os.makedirs(guild_dir, exist_ok=True)
    
    # 2. Traitement spécifique à la guilde
    # Landcover
    _, aoi_ee, _ = lc.setup_aoi(aoi_raw)
    da_lc = lc.get_city_landcover(aoi_ee, aoi_utm, aoi_raw, utm_epsg, specie['habitat_codes'])
    da_export = da_lc.fillna(0).astype('uint8')
    da_export.rio.to_raster(f"{guild_dir}/landcover_{guild_key}_{CITY}.tif")

    # Binary habitat
    binary_wc = conn.get_binary_habitat(da_lc, specie['habitat_codes'])
    gdf_cores, gdf_islets = conn.get_connectivity_elements(binary_wc, core_min_ha=1.0, islet_min_ha=0.1)
    binary_wc.rio.to_raster(f"{guild_dir}/binary_habitat_{guild_key}_{CITY}.tif")

    # Graph construction
    df_nodes = conn.prepare_graph_nodes(gdf_cores, gdf_islets)
    df_nodes.to_file(f"{guild_dir}/nodes_{guild_key}_{CITY}.geojson", driver='GeoJSON')
    G = conn.build_gabriel_graph(df_nodes, specie)
    
    # LCP Network
    pc_value = conn.calculate_pc_index(G, total_area_km2)
    gdf_edges = conn.graph_to_gdf_edges(G, utm_epsg)
    gdf_edges.to_file(f"{guild_dir}/edges_{guild_key}_{CITY}.json", driver='GeoJSON')
    
    resistance_raster = rout.create_resistance_surface(da_lc, specie['friction'])
    resistance_raster.rio.to_raster(f"{guild_dir}/friction_{guild_key}_{CITY}.tif")

    gdf_lcp = rout.compute_lcp_network(gdf_edges, df_nodes, da_lc, specie['friction'])
    # gdf_lcp0['tortuosity'] = gdf_lcp0['real_dist'] / gdf_lcp0['theoretical_dist']
    # pc_real0, G_lcp0 = conn.calculate_pc_index_lcp(G=G, total_area_km2=total_area_km2, species_params=specie, gdf_lcp=gdf_lcp0)

    d0 = specie['graph']['d0']
    threshold = 3 * d0
    # gdf_lcp = gdf_lcp0[gdf_lcp0['accumulated_cost'] <= threshold].copy()
    gdf_lcp['tortuosity'] = gdf_lcp['real_dist'] / gdf_lcp['theoretical_dist']
    pc_real, G_lcp = conn.calculate_pc_index_lcp(G, total_area_km2, specie, gdf_lcp)
    
    # Metrics
    # gdf_lcp0 = conn.calculate_edge_dpc(gdf_lcp0, G_lcp0, total_area_km2, pc_real)
    # gdf_lcp0 = conn.calculate_edge_betweenness(gdf_lcp0, G_lcp0)
    # gdf_lcp0 = conn.classify_corridors(gdf_lcp0, 0.75)
    
    gdf_lcp = conn.calculate_edge_dpc(gdf_lcp, G_lcp, total_area_km2, pc_real)
    gdf_lcp = conn.calculate_edge_betweenness(gdf_lcp, G_lcp)
    gdf_lcp = conn.classify_corridors(gdf_lcp, 0.75)
    gdf_lcp.to_file(f"{guild_dir}/lcp_{guild_key}_{CITY}.json", driver='GeoJSON')
    
    lcp_all = gdf_lcp0.set_index(['node_1', 'node_2'])
    lcp_clean = gdf_lcp.set_index(['node_1', 'node_2'])
    rupture_corridors = lcp_all.drop(lcp_clean.index, errors='ignore').reset_index()
    rupture_corridors.to_file(f"{guild_dir}/barriers_{guild_key}_{CITY}.json", driver='GeoJSON')
    
    # Heatmap
    da_heatmap = conn.lcp_heatmap(gdf_lcp, aoi_utm, res=10, crs_utm=utm_epsg)
    da_heatmap.rio.to_raster(f"{guild_dir}/heatmap_{guild_key}_{CITY}.tif")
    
    print(f"--- FIN : Résultats sauvegardés dans {guild_dir} ---")