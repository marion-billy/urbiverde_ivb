"""Commented-out / deprecated functions extracted from utils/*.py on 2026-06-19.

Kept verbatim (still commented) as a trace of prior / alternative implementations:
KNN & RNG graph builders, circuit current-flow obstacle crossings, node dPC, old segment /
heatmap / priority-corridor variants, old safe_smooth_lines, connectivity heatmap plot.
None of these were imported anywhere; archived out of the live utils modules for tidiness.
"""

# ============== from utils/connectivity.py (was lines 167-288) ==============
# def build_connectivity_graph_knn(nodes_df: gpd.GeoDataFrame, species_params: dict[str, Any]) -> nx.Graph:
#     """
#     Builds a K-Nearest Neighbors (KNN) graph using species-specific dispersal parameters.
#     Use minimum distance between polygon boundaries (Edge-to-Edge) instead of centroids.

#     Args:
#         nodes_df (gpd.GeoDataFrame): Patches with centroids ('x', 'y') and 'total_area_ha'.
#         species_params (dict): Must contain 'd0' (dispersion_distance) and 'k_neighbors' (k).

#     Returns:
#         nx.Graph: Probabilistic connectivity network.
#     """
#     d0 = species_params['graph']['d0']
#     k = species_params['graph']['k_neighbors']
#     max_dist = 3 * d0  # Limite biologique de 3 * d0 (environ 13% de probabilité de survie)
    
#     # Squelette du graph
#     G = nx.Graph()
#     for i, row in nodes_df.iterrows():
#         G.add_node(i, area=row['total_area_ha'], type=row['node_type'], pos=(row['x'], row['y']))

#     sindex = nodes_df.sindex
#     for i, row in nodes_df.iterrows():
#         current_geom = row.geometry
#         possible_neighbors_idx = list(sindex.query(current_geom.buffer(max_dist))) 
        
#         # Calculate real geometry-to-geometry distances
#         neighbor_data = []
#         for idx in possible_neighbors_idx:
#             if idx == i: continue
#             target_geom = nodes_df.iloc[idx].geometry
#             dist = current_geom.distance(target_geom)
            
#             if dist <= max_dist:
#                 p1, p2 = nearest_points(current_geom, target_geom)
#                 neighbor_data.append((idx, dist, p1, p2))
        
#         # Sort by distance and take the K closest
#         neighbor_data.sort(key=lambda x: x[1])
#         for j_idx, d, p1, p2 in neighbor_data[:k]:
#             if not G.has_edge(i, j_idx):
#                 prob = np.exp(-d / d0) #probability of movement: exponential decay function
#                 G.add_edge(i, j_idx, dist_m=d, prob=prob, 
#                            cost_log=-np.log(prob), #transformer la proba en log pour l'algo Dijkstra, astuce mathématique
#                            anchor_pts=(p1, p2))

#     # --- DIAGNOSTIC ---
#     n_nodes = G.number_of_nodes()
#     n_edges = G.number_of_edges()
#     isolated_nodes = [n for n, deg in G.degree() if deg == 0]
#     n_isolated = len(isolated_nodes)
#     print(f"✓ Graphe construit : {n_nodes} nœuds et {n_edges} arêtes.")

#     if n_isolated > 0:
#         percent_isolated = (n_isolated / n_nodes) * 100
#         print(f"Warning : {n_isolated} réservoirs ({percent_isolated:.1f}%) sont totalement isolés.")
            
#     return G

# def build_rng_graph(nodes_df: gpd.GeoDataFrame, species_params: dict) -> nx.Graph:
#     """
#     Builds a Relative Neighborhood Graph (RNG) using geometry-to-geometry distances.
#     Prunes edges where an intermediate patch C provides a 'shorter' jump.
#     """
#     d0 = species_params['graph']['d0']
#     max_dist = 3 * d0 # Limite biologique de 3 * d0 (environ 13% de probabilité de survie)

#     # On commence par un graphe de base (tous les voisins dans le rayon max_dist)
#     G_candidate = nx.Graph()
#     for i, row in nodes_df.iterrows():
#         G_candidate.add_node(i, area=row['total_area_ha'], type=row['node_type'], pos=(row['x'], row['y']))
#     sindex = nodes_df.sindex
#     candidate_edges = []

#     # Trouver tous les candidats possibles (Recherche spatiale)
#     for i, row in tqdm(nodes_df.iterrows(), total=len(nodes_df), desc="Step 1/2: candidate search"):
#         current_geom = row.geometry
#         possible_neighbors = list(sindex.query(current_geom.buffer(max_dist)))
        
#         for idx in possible_neighbors:
#             if idx <= i: continue # On évite les doublons (A-B et B-A)
            
#             dist = current_geom.distance(nodes_df.iloc[idx].geometry)
#             if dist <= max_dist:
#                 p1, p2 = nearest_points(current_geom, nodes_df.iloc[idx].geometry)
#                 candidate_edges.append({
#                     'u': i, 'v': idx, 'dist': dist, 'p1': p1, 'p2': p2
#                 })

#     # Filtrage RNG
#     G_rng = nx.Graph()
#     G_rng.add_nodes_from(G_candidate.nodes(data=True))

#     for edge in tqdm(candidate_edges, desc="Étape 2/2: Filtrage RNG"):
#         u, v, dist_uv = edge['u'], edge['v'], edge['dist']
#         is_rng = True
        
#         # Critère RNG : Est-ce qu'il existe un patch C tel que dist(u,c) < dist(uv) ET dist(v,c) < dist(uv) ?
#         # On ne cherche que les C qui sont dans la zone d'intersection des deux cercles
#         p_u, p_v = edge['p1'], edge['p2']
#         search_zone = p_u.buffer(dist_uv).intersection(p_v.buffer(dist_uv))
#         potential_c = list(sindex.query(search_zone))
        
#         for idx_c in potential_c:
#             if idx_c in [u, v]: continue
            
#             geom_c = nodes_df.iloc[idx_c].geometry
#             if nodes_df.iloc[u].geometry.distance(geom_c) < dist_uv and \
#                nodes_df.iloc[v].geometry.distance(geom_c) < dist_uv:
#                 is_rng = False
#                 break
        
#         if is_rng:
#             prob = np.exp(-dist_uv / d0)
#             G_rng.add_edge(u, v, 
#                            dist_m=dist_uv, 
#                            prob=prob, 
#                            cost_log=-np.log(prob),
#                            anchor_pts=(p_u, p_v))

#     print(f"Graphe RNG construit : {G_rng.number_of_nodes()} nœuds et {G_rng.number_of_edges()} arêtes.")
#     return G_rng

# ============== from utils/connectivity.py (was lines 927-1156) ==============
# def extract_obstacle_crossings(
#     gdf_lcp: gpd.GeoDataFrame,
#     lc_osm: gpd.GeoDataFrame,
#     friction_dict: dict,
#     obstacle_codes: list[int] = None,
#     cluster_tolerance: float = 20.0,
# ) -> gpd.GeoDataFrame:
#     """
#     Extrait les points noirs (CEREMA) : croisements physiques entre corridors
#     LCP fonctionnels et infrastructures fragmentantes OSM.

#     Plusieurs LCPs traversant la même portion d'obstacle sont agrégés en un
#     seul point noir avec scores cumulés.

#     Parameters
#     ----------
#     gdf_lcp : gpd.GeoDataFrame
#         Corridors LCP fonctionnels uniquement (filtrer status='success' en amont).
#         Doit contenir : geometry (LineString), dPC_val, pinch_point_score,
#         ebc_score, node_1, node_2.
#     lc_osm : gpd.GeoDataFrame
#         Vecteurs OSM avec colonne 'wc_code'. Polygones tampons des infrastructures.
#     friction_dict : dict
#         Dictionnaire friction de la guilde (specie['friction']). Utilisé pour
#         déterminer obstacle_priority (NaN -> 'prioritaire', sinon 'secondaire').
#     obstacle_codes : list[int]
#         Codes OSM à considérer comme obstacles fragmentants.
#     cluster_tolerance : float, default 50.0
#         Distance en mètres pour fusionner des intersections proches en un seul
#         point noir.

#     Returns
#     -------
#     gpd.GeoDataFrame
#         Points noirs (LineString ou MultiLineString) avec colonnes :
#         - pn_id : identifiant unique
#         - obstacle_code : 
#         - n_corridors : nombre de LCPs impactés
#         - sum_dPC : somme des dPC_val des corridors traversant le cluster
#         - max_pinch_point : max des pinch_point_score des corridors
#         - max_ebc : max des ebc_score des corridors
#         - corridor_ids : liste des index de LCPs impactés (str, pour GeoJSON)
#         - length_m : longueur cumulée d'intersection
#     """
#     empty_gdf = gpd.GeoDataFrame(
#         columns=['pn_id', 'obstacle_code',
#                  'n_corridors', 'sum_dPC', 'max_pinch_point',
#                  'max_ebc', 'corridor_ids', 'length_m', 'geometry'],
#         crs=gdf_lcp.crs
#     )

#     if gdf_lcp.empty:
#         return empty_gdf

#     # --- RÉCUPÉRATION DYNAMIQUE DES BARRIÈRES ---
#     if obstacle_codes is None:
#         obstacle_codes = [
#             k for k, v in friction_dict.items() 
#             if isinstance(v, float) and np.isnan(v)
#         ]
#     if not obstacle_codes:
#         return empty_gdf
        
#     # 1. Filtrage des obstacles pertinents
#     obstacles = lc_osm[lc_osm['wc_code'].isin(obstacle_codes)].copy()
#     if obstacles.empty:
#         return empty_gdf
        
#     # Alignement CRS
#     if obstacles.crs != gdf_lcp.crs:
#         obstacles = obstacles.to_crs(gdf_lcp.crs)

#     # 2. Préparation des LCPs (id explicite + colonnes nécessaires)
#     lcp = gdf_lcp.copy()
#     lcp['corridor_id'] = lcp.index.astype(str)
#     cols_lcp = ['corridor_id', 'dPC_val', 'pinch_point_score',
#                 'ebc_score', 'geometry']
#     lcp = lcp[cols_lcp]

#     # 3. Jointure spatiale : LCP x obstacles
#     joined = gpd.sjoin(
#         lcp,
#         obstacles[['wc_code', 'geometry']],
#         how='inner',
#         predicate='intersects'
#     )

#     if joined.empty:
#         return empty_gdf

#     # 4. Calcul des géométries d'intersection
#     # On force un index simple sur obstacles pour éviter les bugs de merge
#     obstacles_simple = obstacles[['geometry']].reset_index(drop=True)
#     obstacles_simple = obstacles_simple.rename(columns={'geometry': 'obstacle_geom'})

#     # Refaire sjoin avec un index simple côté obstacles
#     obstacles_for_join = obstacles[['wc_code', 'geometry']].reset_index(drop=True)
    
#     lcp_simple = lcp.reset_index(drop=True)
#     joined = gpd.sjoin(
#         lcp_simple,
#         obstacles_for_join,
#         how='inner',
#         predicate='intersects'
#     )

#     if joined.empty:
#         return empty_gdf

#     # Merge propre via index simple
#     joined = joined.merge(
#         obstacles_simple,
#         left_on='index_right', right_index=True, how='left'
#     )

#     # Calcul de la géométrie de croisement exact
#     joined['intersection'] = joined.apply(
#         lambda r: r['geometry'].intersection(r['obstacle_geom']), axis=1
#     )
#     joined = joined[~joined['intersection'].is_empty].copy()
#     joined = joined[joined['intersection'].geom_type.isin(
#         ['LineString', 'MultiLineString']
#     )].copy()

#     # Remplacer la géométrie globale du corridor par la géométrie locale de l'intersection
#     joined = joined.set_geometry('intersection')
#     joined = joined.drop(columns=['geometry']).rename_geometry('geometry')
    
#     joined.set_crs(gdf_lcp.crs, inplace=True)
#     joined['length_m'] = joined.geometry.length

#     # 5. Clustering β : bufferisation + union -> groupes spatiaux
#     # Maintenant que 'geometry' est bien l'intersection, on bufferise correctement la zone locale
#     buffered = joined.geometry.buffer(cluster_tolerance / 2)
#     merged_union = buffered.union_all()

#     if merged_union.geom_type == 'Polygon':
#         clusters_geom = [merged_union]
#     else:
#         clusters_geom = list(merged_union.geoms)

#     gdf_clusters = gpd.GeoDataFrame(
#         {'cluster_id': range(len(clusters_geom))},
#         geometry=clusters_geom,
#         crs=gdf_lcp.crs
#     )

#     # 6. Attribution de chaque intersection à un cluster
#     joined_idx = joined.reset_index(drop=True).drop(
#         columns=['index_right'], errors='ignore'
#     )
#     sjoin_clusters = gpd.sjoin(
#         joined_idx,
#         gdf_clusters,
#         how='left',
#         predicate='intersects'
#     )

#     # 7. Agrégation par cluster
#     agg = sjoin_clusters.groupby('cluster_id').agg(
#         n_corridors=('corridor_id', 'nunique'),
#         sum_dPC=('dPC_val', 'sum'),
#         max_pinch_point=('pinch_point_score', 'max'),
#         max_ebc=('ebc_score', 'max'),
#         length_m=('length_m', 'sum'),
#         corridor_ids=('corridor_id', lambda s: ','.join(sorted(set(s)))),
#         obstacle_code=('wc_code', lambda s: s.mode().iloc[0]),
#     ).reset_index()

#     # 8. Géométrie : union des intersections du cluster (ligne, pas polygone)
#     geoms_by_cluster = sjoin_clusters.groupby('cluster_id').apply(
#         lambda g: g.geometry.union_all(),
#         include_groups=False 
#     ).reset_index(name='geometry')

#     result = agg.merge(geoms_by_cluster, on='cluster_id')
#     result = gpd.GeoDataFrame(result, geometry='geometry', crs=gdf_lcp.crs)

#     # 9. Mise en forme finale
#     result = result.rename(columns={'cluster_id': 'pn_id'})
#     result = result[['pn_id', 'obstacle_code', 
#                      'n_corridors', 'sum_dPC', 'max_pinch_point',
#                      'max_ebc', 'corridor_ids', 'length_m', 'geometry']]
#     result = result.sort_values('sum_dPC', ascending=False).reset_index(drop=True)
#     result['pn_id'] = range(len(result))

#     return result
    
# def calculate_node_dpc(G_lcp: nx.Graph, total_area_km2: float, species_params: dict) -> pd.DataFrame:
#     """
#     Calcule spécifiquement la fraction 'Connector' du dPC pour chaque nœud.
#     """
#     # 1. Calcul du PC de référence (Réseau complet)
#     pc_ref, _ = calculate_pc_index_lcp(G_lcp, total_area_km2, species_params)
#     nodes = list(G_lcp.nodes())
#     results = []

#     print(f"Analyse de connectivité pour {len(nodes)} noyaux...")
#     for node_i in tqdm(nodes, desc="Calcul dPC Nodes", unit="node"):
#         # A. Fraction Intra : Importance de la surface propre (ai * ai)
#         a_i = G_lcp.nodes[node_i]['area'] / 100
#         dpc_intra = (a_i * a_i) / (total_area_km2**2)
        
#         # B. Calcul du PC sans le noeud i pour isoler le reste
#         G_temp = G_lcp.copy()
#         G_temp.remove_node(node_i)


#         pc_res = calculate_pc_index_lcp(G_temp, total_area_km2, species_params)
#         pc_minus_i = pc_res[0] if isinstance(pc_res, tuple) else pc_res
        
#         # C. dPC Total de ce noeud
#         dpc_total = pc_ref - pc_minus_i
        
#         # D. Calcul du Flux (contribution aux chemins où i est source ou destination)
#         # Dans la pratique, on simplifie souvent : Connector = Total - Intra - Flux
#         # Mais mathématiquement, le Connector est le rôle de "relais" entre j et k via i
        
#         # Pour isoler le Connector pur : 
#         # C'est la part du PC qui s'effondre car i servait de pont entre d'autres noeuds
#         dpc_connector = max(0, dpc_total - dpc_intra) # Simplification courante (Flux inclus souvent dans le résiduel)
        
#         results.append({
#             'node_id': node_i,
#             'area_ha': G_lcp.nodes[node_i]['area'],
#             'dPC_total': (dpc_total / pc_ref) * 100,
#             'dPC_connector': (dpc_connector / pc_ref) * 100
#         })

#     return pd.DataFrame(results).sort_values('dPC_connector', ascending=False)

# ============== from utils/connectivity.py (was lines 1317-1557) ==============
# def create_urban_planning_segments(gdf_lcp, df_nodes, tolerance=0.1, artifact_threshold=14.5):
#     """
#     Transform LCP corridors into unique urban-planning segments.
#     - Gommage des parties dans les habitats
#     - Découpage topologique aux intersections
#     - Agrégation des scores (dPC, EBC, Pinch Point)
#     - Nettoyage des micro-segments, filtrage des artefacts de bordure (14.14m)
#     """
#     # 1. Nettoyage des corridors (Gommage habitats)
#     habitats_union = df_nodes.geometry.union_all()
#     gdf_matrix = gdf_lcp.copy()
#     gdf_matrix['geometry'] = gdf_matrix.geometry.difference(habitats_union)
#     gdf_matrix = gdf_matrix[~gdf_matrix.geometry.is_empty].copy()
    
#     # Explode the line into all its fragments (MultiLineString -> LineStrings)
#     exploded = gdf_matrix.explode(index_parts=False)
#     exploded['lcp_id'] = exploded.index  # Sauvegarde de l'ID parent (le LCP global)
#     exploded = exploded.reset_index(drop=True)

#     # Sécurité: ignorer les points isolés générés par les frôlements de polygones
#     exploded = exploded[exploded.geometry.geom_type == 'LineString'].copy()
#     if exploded.empty:
#         return gpd.GeoDataFrame()

#     exploded['frag_len'] = exploded.geometry.length

#     # --- FILTRAGE TOPOLOGIQUE INTELLIGENT ---
#     # a. Extraire les points de départ et de fin de chaque fragment avec un micro-buffer
#     starts = gpd.GeoDataFrame({'frag_idx': exploded.index}, 
#                               geometry=exploded.geometry.apply(lambda g: Point(g.coords[0])).buffer(1.0), 
#                               crs=exploded.crs)
#     ends = gpd.GeoDataFrame({'frag_idx': exploded.index}, 
#                             geometry=exploded.geometry.apply(lambda g: Point(g.coords[-1])).buffer(1.0), 
#                             crs=exploded.crs)

#     # b. Assigner un ID temporaire aux habitats
#     nodes_temp = df_nodes.copy().reset_index(drop=True)
#     nodes_temp['node_id'] = nodes_temp.index

#     # c. Vérifier quel patch d'habitat chaque extrémité du fragment touche
#     starts_join = gpd.sjoin(starts, nodes_temp[['node_id', 'geometry']], how='left', predicate='intersects')
#     ends_join = gpd.sjoin(ends, nodes_temp[['node_id', 'geometry']], how='left', predicate='intersects')

#     starts_node = starts_join.groupby('frag_idx')['node_id'].first()
#     ends_node = ends_join.groupby('frag_idx')['node_id'].first()

#     # RÈGLE 1 : Le fragment est plus grand qu'une diagonale de pixel (Ce n'est pas un artefact)
#     mask_long = exploded['frag_len'] > artifact_threshold

#     # RÈGLE 2 : Le fragment est court, MAIS c'est un VRAI PONT entre deux habitats !
#     # Il a un habitat au départ (notna), un habitat à la fin (notna), et ce sont des habitats différents.
#     mask_valid_short = starts_node.notna() & ends_node.notna() & (starts_node != ends_node)

#     # d. On garde le fragment s'il valide l'une des deux règles
#     exploded_clean = exploded[mask_long | mask_valid_short].copy()
    
#     # On ressoude les morceaux conservés pour recréer le LCP propre
#     gdf_matrix = exploded_clean.dissolve(by='lcp_id')
#     # ----------------------------------------
    
#     # 2. Topological splitting at intersections
#     merged = unary_union(gdf_matrix.geometry.tolist())
#     if hasattr(merged, 'geoms'):
#         lines = [g for g in merged.geoms if g.geom_type == 'LineString']
#         for mg in [g for g in merged.geoms if g.geom_type == 'MultiLineString']:
#             lines.extend(list(mg.geoms))
#     else:
#         lines = [merged]
        
#     gdf_segments = gpd.GeoDataFrame(geometry=lines, crs=gdf_lcp.crs)
#     gdf_segments['segment_id'] = range(len(gdf_segments))

#     # 3. Spatial aggregation of metrics (dPC, EBC, pinch point)
#     gdf_seg_buf = gdf_segments.copy()
#     gdf_seg_buf.geometry = gdf_segments.geometry.buffer(tolerance)
#     join_df = gpd.sjoin(gdf_seg_buf, gdf_matrix, how='left', predicate='intersects')

#     metrics = join_df.groupby('segment_id').agg(
#         corridor_count=('node_1', 'count'),
#         sum_dPC=('dPC_val', 'sum') if 'dPC_val' in join_df.columns else ('node_1', 'count'),
#         max_ebc=('ebc_score', 'max') if 'ebc_score' in join_df.columns else ('node_1', 'max'),
#         max_pinch_point=('pinch_point_score', 'max') if 'pinch_point_score' in join_df.columns else ('node_1', 'max')
#     ).reset_index()
#     gdf_final = gdf_segments.merge(metrics, on='segment_id')

#     # 4. Soudure des segments
#     for col in ['sum_dPC', 'max_ebc', 'max_pinch_point']:
#         if col in gdf_final.columns:
#             gdf_final[f'grp_{col}'] = gdf_final[col].round(6)
            
#     dissolve_cols = ['corridor_count'] + [f'grp_{col}' for col in ['sum_dPC', 'max_ebc', 'max_pinch_point'] if col in gdf_final.columns]
    
#     gdf_clean = gdf_final.dissolve(by=dissolve_cols).reset_index()
    
#     gdf_clean['geometry'] = gdf_clean['geometry'].apply(
#         lambda g: linemerge(g) if g.geom_type == 'MultiLineString' else g
#     )
#     gdf_clean = gdf_clean.explode(index_parts=False).reset_index(drop=True)
    
#     cols_to_drop = [c for c in gdf_clean.columns if 'grp_' in c]
#     gdf_clean = gdf_clean.drop(columns=cols_to_drop + ['segment_id'], errors='ignore')
#     gdf_clean['segment_id'] = range(len(gdf_clean))

#     return gdf_clean
    
# def lcp_heatmap(gdf_lcp: gpd.GeoDataFrame, aoi_utm: gpd.GeoDataFrame, res: int = 10, crs_utm: str = None) -> xr.DataArray:
#     """
#     Génère une heatmap de densité des chemins LCP.
#     Chaque pixel contient le nombre de chemins qui le traversent.
    
#     Args:
#         gdf_lcp: GeoDataFrame des chemins (LCP).
#         aoi_utm: GeoDataFrame de la zone d'étude (pour cadrer le raster).
#         res: Résolution spatiale en mètres (par défaut 10m).
#         crs_utm
#     """
    
#     # 1. Création du template vide (Image de référence)
#     da_ref = create_img_reference(aoi_utm, spatial_resolution=res, output_crs=crs_utm)
    
#     # 2. Alignement des données
#     gdf_lcp_utm = gdf_lcp.to_crs(da_ref.rio.crs)
    
#     # 3. Préparation des formes pour la rasterisation
#     # On attribue la valeur 1 à chaque géométrie
#     shapes = [(geom, 1) for geom in gdf_lcp_utm.geometry if geom is not None]

#     # 4. Rasterisation par accumulation 
#     heatmap_arr = features.rasterize(
#         shapes=shapes,
#         out_shape=(da_ref.rio.height, da_ref.rio.width),
#         transform=da_ref.rio.transform(),
#         fill=0,
#         all_touched=True, 
#         merge_alg=MergeAlg.add,
#         dtype='uint32'
#     )

#     # 5. Conversion en DataArray
#     da_heatmap = xr.DataArray(
#         heatmap_arr,
#         coords={"y": da_ref.y, "x": da_ref.x},
#         dims=("y", "x"),
#         name="lcp_density"
#     ).rio.write_crs(da_ref.rio.crs)
    
#     return da_heatmap

# def get_priority_corridors_ebc(
#     G: nx.Graph, 
#     crs: Any, 
#     n_top: Optional[int] = None, 
#     percentile: Optional[float] = None
# ) -> gpd.GeoDataFrame:
#     """
#     Identifies critical links based on Edge Betweenness Centrality.

#     Args:
#         G (nx.Graph): The connectivity graph.
#         crs: CRS of the study area (e.g., 'EPSG:2154').
#         n_top (int, optional): Fixed number of top corridors.
#         percentile (float, optional): Percentage of top corridors (0-100).

#     Returns:
#         gpd.GeoDataFrame: Priority corridors represented as straight lines.
#     """
#     if G.number_of_edges() == 0:
#         return gpd.GeoDataFrame(columns=['node_1', 'node_2', 'importance_score', 'geometry'], crs=crs)

#     # Centrality measures the importance of a link for the global flow
#     edge_centrality = nx.edge_betweenness_centrality(G, weight='cost_log')
#     sorted_edges = sorted(edge_centrality.items(), key=lambda x: x[1], reverse=True)

#     # Determine selection threshold
#     if percentile is not None:
#         limit = max(1, int(len(sorted_edges) * (percentile / 100)))
#     elif n_top is not None:
#         limit = min(n_top, len(sorted_edges))
#     else:
#         limit = len(sorted_edges)

#     corridors = []
#     for (u, v), score in sorted_edges[:limit]:
#         corridors.append({
#             'node_1': u,
#             'node_2': v,
#             'importance_score': score,
#             'dist_m': G[u][v]['dist_m'],
#             'cost_bio': G[u][v]['cost_log'],
#             'geometry': LineString([Point(G.nodes[u]['pos']), Point(G.nodes[v]['pos'])])
#         })
    
#     return gpd.GeoDataFrame(corridors, crs=crs)

# def get_priority_corridors_dpc(
#     G: nx.Graph, 
#     total_area_km2: float,
#     crs: Any, 
#     n_top: Optional[int] = None, 
#     percentile: Optional[float] = None
# ) -> gpd.GeoDataFrame:
#     """
#     Identifie les corridors prioritaires en utilisant une approche par flux (dPC).
#     """
#     if G.number_of_edges() == 0:
#         return gpd.GeoDataFrame(columns=['node_1', 'node_2', 'importance_score', 'geometry'], crs=crs)

#     # 1. Calcul du flux (dPC) pour chaque arête
#     flow_dict = {}
#     for u, v, data in G.edges(data=True):
#         area_u = G.nodes[u]['area'] / 100 # ha -> km2
#         area_v = G.nodes[v]['area'] / 100 # ha -> km2
#         prob_uv = data['prob']
        
#         # Formule du flux
#         score = (area_u * area_v * prob_uv) / (total_area_km2**2)
#         flow_dict[(u, v)] = score

#     # 2. Tri des arêtes par score
#     sorted_edges = sorted(flow_dict.items(), key=lambda x: x[1], reverse=True)
    
#     # 3. Determine selection threshold
#     if percentile is not None:
#         limit = max(1, int(len(sorted_edges) * (percentile / 100)))
#     elif n_top is not None:
#         limit = min(n_top, len(sorted_edges))
#     else:
#         limit = len(sorted_edges)

#     corridors = []
#     for (u, v), score in sorted_edges[:limit]:
#         corridors.append({
#             'node_1': u,
#             'node_2': v,
#             'importance_score': score,
#             'dist_m': G[u][v]['dist_m'],
#             'cost_bio': G[u][v]['cost_log'],
#             'geometry': LineString([Point(G.nodes[u]['pos']), Point(G.nodes[v]['pos'])])
#         })
    
#     return gpd.GeoDataFrame(corridors, crs=crs)

# ============== from utils/routing.py (was lines 457-515) ==============
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

# ============== from utils/vizu_ind.py (was lines 278-335) ==============
# def plot_connectivity_heatmap(da_heatmap, df_nodes, aoi_utm):
#     """
#     Génère et affiche la heatmap de connectivité avec les réservoirs superposés.
    
#     Args:
#         da_heatmap (xr.DataArray): La heatmap de densité LCP.
#         df_nodes (gpd.GeoDataFrame): Les réservoirs/nœuds de biodiversité.
#         aoi_utm (gpd.GeoDataFrame): La limite de la zone d'étude.
#     """
#     # 1. Préparation de la heatmap (Épaississement visuel)
#     data = da_heatmap.values.astype(float)
#     vmax_abs = data.max()
#     mask = data >= 1
#     dist_map = ndimage.distance_transform_edt(~mask)
#     max_intensity_map = ndimage.maximum_filter(data, size=8)
#     ratio = max_intensity_map / vmax_abs
#     variable_width_threshold = 1 + (ratio**2 * 7) # px min px max
#     continuous_thick = np.where(dist_map <= variable_width_threshold, max_intensity_map, 0)
#     da_heatmap_thick = da_heatmap.copy(data=continuous_thick)
#     heatmap_plot = da_heatmap_thick.where(da_heatmap_thick >= 1)

#     # 2. Configuration du graphique
#     fig, ax = plt.subplots(figsize=(14, 12))
#     # fig.patch.set_facecolor('#2d2d2d') 
#     # ax.set_facecolor('#2d2d2d')
    
#     # 3. Affichage des Réservoirs et Islets 
#     if df_nodes.crs is None:
#         df_nodes.set_crs(aoi_utm.crs, inplace=True)
#     nodes_to_plot = df_nodes.to_crs(da_heatmap.rio.crs)
#     nodes_to_plot.plot(ax=ax, color='#206c2c', alpha=0.6, edgecolor='none', zorder=1)
#     aoi_utm.plot(ax=ax, facecolor="none", edgecolor='black', alpha=0.6, linewidth=2, zorder=2)

#     # 4. Affichage de la Heatmap 
#     mappable = heatmap_plot.plot(
#         ax=ax,
#         cmap='plasma', 
#         norm=colors.Normalize(vmin=1, vmax=vmax_abs),
#         add_colorbar=True,
#         add_labels=False,
#         zorder=3,
#         cbar_kwargs={
#             'label': 'Nombre de passages',
#             'format': ScalarFormatter(),
#             'ticks': [1, 2, 5, 10, int(vmax_abs)]
#         }
#     )

#     cbar = mappable.colorbar
#     cbar.ax.tick_params(axis='y', colors='black')
#     cbar.set_label('Nombre de passages', color='black')
#     for label in cbar.ax.yaxis.get_ticklabels():
#         label.set_color('black')

#     # 5. Habillage 
#     ax.set_axis_off()
#     plt.tight_layout()
#     plt.show()
