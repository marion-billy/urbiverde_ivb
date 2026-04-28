import os
import geopandas as gpd
import xarray as xr

def run_guild_pipeline(guild_key, aoi_utm, da_lc, utm_epsg, aoi_raw):
    print(f"--- DÉBUT DU PIPELINE POUR : {guild_key} ---")
    
    # 1. Configurer les répertoires
    specie = species_params.SPECIES_CONFIG[guild_key]
    guild_dir = f"{OUTPUT_DIR}/{guild_key}"
    os.makedirs(guild_dir, exist_ok=True)
    
    # 2. Traitement (Adapté de votre notebook)
    # Binary habitat
    binary_wc = conn.get_binary_habitat(da_lc, specie['habitat_codes'])
    gdf_cores, gdf_islets = conn.get_connectivity_elements(binary_wc, core_min_ha=1.0, islet_min_ha=0.1)
    
    # Graph construction
    df_nodes = conn.prepare_graph_nodes(gdf_cores, gdf_islets)
    G = conn.build_gabriel_graph(df_nodes, specie)
    
    # LCP Network
    gdf_edges = conn.graph_to_gdf_edges(G, utm_epsg)
    gdf_lcp0 = rout.compute_lcp_network(gdf_edges, df_nodes, da_lc, specie['friction'])
    
    # PC Calculation
    pc_value = conn.calculate_pc_index(G, total_area_km2)
    pc_real, G_lcp = conn.calculate_pc_index_lcp(G, total_area_km2, specie, gdf_lcp0)
    
    # Metrics
    gdf_lcp = conn.calculate_edge_dpc(gdf_lcp0, G_lcp, total_area_km2, pc_real)
    gdf_lcp = conn.classify_corridors(gdf_lcp, 0.75)
    
    # 3. Exportation (crucial pour le dashboard)
    df_nodes.to_file(f"{guild_dir}/nodes.geojson", driver='GeoJSON')
    gdf_lcp.to_file(f"{guild_dir}/corridors.geojson", driver='GeoJSON')
    
    # Heatmap
    da_heatmap = conn.lcp_heatmap(gdf_lcp, aoi_utm, res=10, crs_utm=utm_epsg)
    da_heatmap.rio.to_raster(f"{guild_dir}/heatmap.tif")
    
    print(f"--- FIN : Résultats sauvegardés dans {guild_dir} ---")