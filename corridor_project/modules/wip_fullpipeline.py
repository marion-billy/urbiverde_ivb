def run_full_connectivity_analysis(city_name, url_aoi, guild_key):
    # 1. SETUP
    specie = species_params.SPECIES_CONFIG[guild_key]
    
    # 2. LANDCOVER (GEE + OSM)
    da_lc = lc.get_city_landcover(aoi_ee, aoi_raw)

    # 3. MSPA (Morphologie)

    habitat_codes = specie['habitat_codes']
    binary_wc = conn.get_binary_habitat(da_lc, habitat_codes)

    core_arr, islet_arr = conn.fast_mspa(binary_wc.values, edge_width_pixels=1)

    # 3. Vectorisation et filtrage par surface
    # On récupère la transformation spatiale du raster original
    transform = da_lc.rio.transform()
    
    # Réservoirs (Cores) > 1 hectare
    gdf_cores = conn.vectoriser_et_filtrer(core_arr, transform, utm_epsg, min_area_ha=1.0, label_name="Core")
    # Stepping Stones (Islets) > 0.1 hectare
    gdf_islets = conn.vectoriser_et_filtrer(islet_arr, transform, utm_epsg, min_area_ha=0.1, label_name="Islet")

    # 4. GRAPH & LCP
    df_nodes = conn.prepare_graph_nodes(gdf_cores, gdf_islets)
    G = conn.build_connectivity_graph_knn(df_nodes, specie)
    gdf_corridors = conn.get_priority_corridors(G, crs=utm_epsg, percentile=10)
    gdf_lcp = rout.compute_lcp_network(gdf_corridors, df_nodes, da_lc, specie['friction'])
    total_area_km2 = aoi_utm.area.sum() / 1e6
    return {
        "pc_index": conn.calculate_pc_index(G, total_area_km2),
        "corridors": gdf_lcp,
        "cores": gdf_cores
    }

run_full_connectivity_analysis(CITY, url_aoi, GUILD_KEY)