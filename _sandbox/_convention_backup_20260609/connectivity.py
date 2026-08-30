import sys
import pandas as pd
import numpy as np
import xarray as xr
import geopandas as gpd
from scipy import ndimage
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
from typing import Optional, Union, Any, List, Union, Tuple
sys.path.insert(1, '../../Hugo/a_b_c_functions/spatial_analysis/')
from utils_raster import raster_to_polygon
from utils_raster import create_img_reference

#######################################
################ MSPA #################
#######################################

def get_binary_habitat(da_lc: xr.DataArray, habitat_codes: List[int]) -> xr.DataArray:
    """
    Binarise le raster d'occupation du sol selon les préférences de l'espèce.
    
    Args:
        da_lc (xr.DataArray): Raster d'occupation du sol.
        habitat_codes (list): Liste des codes considérés comme habitat.
        
    Returns:
        xr.DataArray: Raster binaire (1: Habitat / Foreground, 0: Matrice / Background).
    """
    binary = xr.where(da_lc.isin(habitat_codes), 1, 0)
    return binary.where(da_lc.notnull(), 0).astype('uint8')

def fast_mspa(da_binary: xr.DataArray, edge_width_pixels: int = 1) -> Tuple[xr.DataArray, xr.DataArray]:
    """
    Identifie les catégories morphologiques Cores et Islets.
    Permet de varier la sensibilité à la lisière via edge_width_pixels.
    
    Args:
        da_binary (xr.DataArray): Masque binaire (1: habitat, 0: reste).
        edge_width_pixels (int): Nombre de pixels à "raboter" sur le bord.
        
    Returns:
        Tuple[xr.DataArray, xr.DataArray]: (DataArray_Cores, DataArray_Islets).
    """
    binary_mask = da_binary.values 
    
    struct = np.ones((3,3)) # élément structurant, connectivité reine / 8 voisins
    # ÉROSION (Création du Core)
    core_arr = ndimage.binary_erosion(binary_mask, structure=struct, iterations=edge_width_pixels)
    labels, n_labels = ndimage.label(binary_mask)

    # Un Islet est une tache qui disparaît après l'érosion, aucun pixel Core à l'intérieur
    labels_with_core = np.unique(labels[core_arr > 0])
    is_core_patch = np.isin(labels, labels_with_core)
    islet_arr = (labels > 0) & (~is_core_patch)

    # Lisière
    edge_arr = (is_core_patch) & (core_arr == 0)
    
    # --- C. On ré-emballe dans des DataArrays (on copie les coordonnées de l'entrée) ---
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
    Identifie et classe les éléments de connectivité (Noyaux et Stepping Stones).
    Un Noyau est un patch dont le COEUR fait >= core_min_ha, mais la géométrie renvoyée inclut la lisière (Edge).
    Les Cores trop petits pour être des Noyaux sont déclassés en Stepping Stones.
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
    if not gdf_stepping_stones.empty:
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
    Merges core habitats and stepping stones into a unified dataset and extracts represnetative point (centroids forced to be inside the shape).

    Args:
        gdf_cores (gpd.GeoDataFrame): Large habitat patches (reservoirs).
        gdf_islets (gpd.GeoDataFrame): Small habitat patches (stepping stones).

    Returns:
        pd.DataFrame: Merged dataset with 'x', 'y' coordinates and 'node_type'.
    """
    nodes = pd.concat([
        gdf_cores.assign(node_type='core'), 
        gdf_islets.assign(node_type='islet')
    ], ignore_index=True)
    
    rep_points = nodes.geometry.representative_point()
    nodes['x'] = rep_points.x
    nodes['y'] = rep_points.y
    return nodes

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
#     for i, row in tqdm(nodes_df.iterrows(), total=len(nodes_df), desc="Étape 1/2: Recherche candidats"):
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

def build_gabriel_graph(nodes_df: gpd.GeoDataFrame, species_params: dict) -> nx.Graph:
    """
    Construit un Graphe de Gabriel basé sur les distances Edge-to-Edge.
    Moins restrictif que le RNG, il permet de garder des chemins alternatifs (boucles).
    """
    d0 = species_params['graph']['d0']
    max_dist = 2 * d0 

    # 1. Initialisation
    G_candidate = nx.Graph()
    for i, row in nodes_df.iterrows():
        G_candidate.add_node(i, area=row['total_area_ha'], type=row['node_type'], pos=(row['x'], row['y']))
    
    sindex = nodes_df.sindex
    candidate_edges = []

    # 2. Étape 1 : Recherche des candidats
    for i, row in tqdm(nodes_df.iterrows(), total=len(nodes_df), desc="Étape 1/2: Recherche candidats"):
        current_geom = row.geometry
        possible_neighbors = list(sindex.query(current_geom.buffer(max_dist)))
        
        for idx in possible_neighbors:
            if idx <= i: continue 
            
            target_geom = nodes_df.iloc[idx].geometry
            dist = current_geom.distance(target_geom)
            if 0.1 < dist <= max_dist:
                p1, p2 = nearest_points(current_geom, target_geom)
                candidate_edges.append({
                    'u': i, 'v': idx, 'dist': dist, 'p1': p1, 'p2': p2
                })

    # 3. Étape 2 : Filtrage Gabriel
    G_gab = nx.Graph()
    G_gab.add_nodes_from(G_candidate.nodes(data=True))

    for edge in tqdm(candidate_edges, desc="Étape 2/2: Filtrage Gabriel"):
        u, v, dist_uv = edge['u'], edge['v'], edge['dist']
        is_gabriel = True
        
        p_u, p_v = edge['p1'], edge['p2']
        
        # --- LOGIQUE GABRIEL ---
        # Le milieu du segment reliant les deux points les plus proches
        midpoint = Point((p_u.x + p_v.x)/2, (p_u.y + p_v.y)/2)
        radius = dist_uv / 2
        
        # Zone de recherche : le cercle de diamètre UV
        search_zone = midpoint.buffer(radius)
        potential_c = list(sindex.query(search_zone))
        
        for idx_c in potential_c:
            if idx_c in [u, v]: continue
            
            geom_c = nodes_df.iloc[idx_c].geometry
            # Si un patch C est plus proche du milieu que le rayon, on casse l'arête
            if geom_c.distance(midpoint) < radius:
                is_gabriel = False
                break
        
        if is_gabriel:
            prob = np.exp(-dist_uv / d0)
            G_gab.add_edge(u, v, 
                           dist_m=dist_uv, 
                           prob=prob, 
                           cost_log=-np.log(prob),
                           anchor_pts=(p_u, p_v))

    print(f"Graphe de Gabriel construit : {G_gab.number_of_nodes()} nœuds et {G_gab.number_of_edges()} arêtes.")
    return G_gab

def calculate_pc_index(G: nx.Graph, total_area_km2: float) -> float:
    """
    Calculates the Probability of Connectivity (PC) Index for the landscape. Measures the overall 'permeability' of the landscape for a given species.

    Args:
        G (nx.Graph): The connectivity graph.
        total_area_km2 (float): Total study area (AOI) surface in km2.

    Returns:
        float: PC Index value (0 to 1).
    """
    pc_sum = 0
    components = list(nx.connected_components(G))
    
    for comp in components:
        subgraph = G.subgraph(comp)
        # Find all shortest probabilistic paths (Dijkstra)
        path_lengths = dict(nx.all_pairs_dijkstra_path_length(subgraph, weight='cost_log'))
        nodes_dict = dict(subgraph.nodes(data=True))
        
        for n1 in nodes_dict:
            a_i = nodes_dict[n1]['area'] / 100 # ha to km2
            for n2 in nodes_dict:
                a_j = nodes_dict[n2]['area'] / 100 # ha to km2
                
                if n1 == n2:
                    prob_ij = 1.0
                elif n2 in path_lengths.get(n1, {}):
                    prob_ij = np.exp(-path_lengths[n1][n2])
                else:
                    prob_ij = 0.0
                
                pc_sum += a_i * a_j * prob_ij
                
    return pc_sum / (total_area_km2**2)

def graph_to_gdf_edges(G, crs):
    """Transforme toutes les arêtes d'un graphe NetworkX en GeoDataFrame."""
    edges = []
    for u, v, data in G.edges(data=True):
        p1, p2 = data['anchor_pts']
        edges.append({
            'node_1': u,
            'node_2': v,
            'dist_m': data['dist_m'],
            'cost_log': data['cost_log'],
            'geometry': LineString([p1, p2]) # now the actual gap, not the centroid distance
        })
    return gpd.GeoDataFrame(edges, crs=crs)
    
def calculate_pc_index_lcp(G: nx.Graph, total_area_km2: float, species_params: dict, gdf_lcp: gpd.GeoDataFrame = None):
    """
    Calcule le PC réel en utilisant le coût accumulé comme poids biologique.
    Si gdf_lcp est fourni, met à jour le graphe. 
    Sinon, utilise le graphe tel quel (utile pour les itérations dPC).
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
                    cost_log = 999999 # Coût prohibitif si erreur de données
                else:
                    cost_log = max(0.0, acc_cost / d0)
                prob = np.exp(-cost_log)
                G_curr[u][v].update({'accumulated_cost': acc_cost, 'prob': prob, 'cost_log': cost_log})
                
    # Calcul du PC
    pc_sum = 0
    for comp in nx.connected_components(G_curr):
        subgraph = G_curr.subgraph(comp)
        path_costs = dict(nx.all_pairs_dijkstra_path_length(subgraph, weight='cost_log'))
        nodes_dict = dict(subgraph.nodes(data=True))
        
        for n1 in nodes_dict:
            a_i = nodes_dict[n1]['area'] / 100
            for n2 in nodes_dict:
                a_j = nodes_dict[n2]['area'] / 100
                prob_ij = np.exp(-path_costs[n1][n2]) if n2 in path_costs.get(n1, {}) else 0.0
                if n1 == n2: prob_ij = 1.0
                pc_sum += a_i * a_j * prob_ij

    pc_value = pc_sum / (total_area_km2**2)

    return pc_value, G_curr

def calculate_edge_dpc(gdf_lcp: gpd.GeoDataFrame, G_curr: nx.Graph, total_area_km2: float, pc_real: float) -> gpd.GeoDataFrame:
    """
    Calcule l'importance dPC pour chaque corridor réel (LCP).
    
    Args:
        gdf_lcp: GeoDataFrame des tracés LCP (doit contenir node_1, node_2 et real_dist).
        G_curr: Le graphe mis à jour avec les distances réelles.
        total_area_km2: Surface totale de la zone d'étude (AOI).
        pc_real: La valeur du PC réel.
    """
    df = gdf_lcp.copy()
    
    def compute_row(row):
        u, v = int(row['node_1']), int(row['node_2'])
        
        # Récupération des données depuis le graphe G_curr
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
    Calcule la centralité d'intermédiation pour chaque corridor.
    Identifie les corridors qui sont des passages obligés (Connecteurs).
    """
    df = gdf_lcp.copy()
    edge_centrality = nx.edge_betweenness_centrality(G_curr, weight='cost_log', normalized=True)
    
    def get_centrality(row):
        u, v = int(row['node_1']), int(row['node_2'])
        return edge_centrality.get((u, v)) or edge_centrality.get((v, u), 0)

    df['ebc_score'] = df.apply(get_centrality, axis=1)
    
    # 3. Normalisation de 0 à 100 
    if df['ebc_score'].max() > 0:
        df['ebc_score'] = (df['ebc_score'] / df['ebc_score'].max()) * 100
        
    return df.sort_values(by='ebc_score', ascending=False)

def classify_corridors(gdf_lcp: gpd.GeoDataFrame, q: float = 0.5) -> gpd.GeoDataFrame:
    """
    Calcule les seuils et catégorise les corridors.
    Retourne le GeoDataFrame enrichi de la colonne 'category'.
    """
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

def calculate_node_betweenness(df_nodes: gpd.GeoDataFrame, G_curr: nx.Graph, aoi_gdf: gpd.GeoDataFrame = None) -> gpd.GeoDataFrame:
    """
    Calcule la Node Betweenness Centrality (NBC) pour chaque réservoir d'habitat.
    Identifie les patchs qui agissent comme hubs écologiques.
    Permet un filtrage sur l'AOI pour une normalisation locale.
    """
    df = df_nodes.copy()
    
    # 1. Calcul via NetworkX sur tout le graphe (Buffer inclus)
    node_centrality = nx.betweenness_centrality(G_curr, weight='cost_log', normalized=True)
    
    # 2. Assignation des scores bruts 
    df['nbc_score_raw'] = df.index.map(lambda node_id: node_centrality.get(node_id, 0))
    
    # 3. Filtrage spatial : On ne garde que les noeuds dans l'AOI (si fourni)
    if aoi_gdf is not None:
        df = gpd.sjoin(df, aoi_gdf[['geometry']], how='inner', predicate='intersects')
        df = df.drop(columns=['index_right'], errors='ignore')
        
    # 4. Normalisation de 0 à 100 (aoi city)
    max_score = df['nbc_score_raw'].max()
    if max_score > 0:
        df['nbc_score'] = (df['nbc_score_raw'] / max_score) * 100
    else:
        df['nbc_score'] = 0
    df = df.drop(columns=['nbc_score_raw'])
        
    return df.sort_values(by='nbc_score', ascending=False)

def calculate_pinch_points_network(gdf_lcp: gpd.GeoDataFrame, G_curr: nx.Graph) -> gpd.GeoDataFrame:
    """
    Calcule les Pinch Points (Goulots d'étranglement) via la théorie des circuits (Current-Flow).
    Équivalent vectoriel de Circuitscape.
    """
    df = gdf_lcp.copy()
    edge_current_flow = {}

    G_clean = G_curr.copy()

    # 1. Supprimer les liens avec une probabilité nulle ou quasi-nulle pour l'inversion de matrice
    edges_to_remove = [(u, v) for u, v, d in G_clean.edges(data=True) if d.get('prob', 0) <= 1e-12]
    G_clean.remove_edges_from(edges_to_remove)
    
    # 2. Itération sur les composantes connectées du graphe 
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
                print(f" Ignoré: Composante de {len(subgraph.nodes)} noeuds ({e})")

    # 3. Extraire score
    def get_current_flow(row):
        u, v = int(row['node_1']), int(row['node_2'])
        return edge_current_flow.get((u, v)) or edge_current_flow.get((v, u), 0)

    # 4. Assigner score
    df['pinch_point_score'] = df.apply(get_current_flow, axis=1)
    
    # 5. Normalisation de 0 à 100
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
    cluster_tolerance: float = 15.0
) -> gpd.GeoDataFrame:
    """
    Extrait les points de rupture : intersections entre les lignes de désir 
    des corridors ayant ÉCHOUÉ et les obstacles OSM infranchissables.
    """
    # 1. On ne garde que les échecs causés par des barrières
    gdf_failed = gdf_lcp[
        (gdf_lcp['status'] == 'failed') & 
        (gdf_lcp['fail_reason'] == 'uncrossable_barrier')
    ].copy()

    empty_gdf = gpd.GeoDataFrame(columns=['pn_id', 'geometry'], crs=gdf_lcp.crs)
    if gdf_failed.empty:
        return empty_gdf

    # 2. Identification dynamique des barrières (sans les bâtiments)
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

    # 4. SJOIN unique : Ligne (échec) x Obstacle
    obstacles_simple   = obstacles[['geometry']].reset_index(drop=True).rename(columns={'geometry': 'obs_geom'})
    obstacles_for_join = obstacles[['wc_code', 'geometry']].reset_index(drop=True)
    failed_simple      = gdf_failed.reset_index(drop=True)

    joined_exact = gpd.sjoin(failed_simple, obstacles_for_join, how='inner', predicate='intersects')
    if joined_exact.empty:
        return empty_gdf
    joined_exact = joined_exact.merge(obstacles_simple, left_on='index_right', right_index=True, how='left')

    # 5. Calcul des centroïdes de collision (le point noir géographique)
    obstacles_simple = obstacles[['geometry']].reset_index(drop=True).rename(columns={'geometry': 'obs_geom'})
    obstacles_for_join = obstacles[['wc_code', 'geometry']].reset_index(drop=True)
    
    failed_simple = gdf_failed.reset_index(drop=True)
    joined_exact = gpd.sjoin(failed_simple, obstacles_for_join, how='inner', predicate='intersects')
    joined_exact = joined_exact.merge(obstacles_simple, left_on='index_right', right_index=True, how='left')
    
    # L'intersection exacte entre la ligne droite et l'obstacle
    joined_exact['intersection'] = joined_exact.apply(
        lambda r: r['geometry'].intersection(r['obs_geom']), axis=1
    )
    
    # Nettoyage des géométries vides
    joined_exact = joined_exact[~joined_exact['intersection'].is_empty].copy()
    
    # 5. CLUSTERING : Regrouper les impacts proches
    joined_exact = joined_exact.set_geometry('intersection')
    joined_exact.set_crs(gdf_lcp.crs, inplace=True)
    
    # On bufferise les petits segments de croisement et on les fusionne
    buffered = joined_exact.geometry.buffer(cluster_tolerance / 2)
    merged_union = buffered.union_all()

    if merged_union.geom_type == 'Polygon':
        clusters_geom = [merged_union]
    else:
        clusters_geom = list(merged_union.geoms)

    gdf_clusters = gpd.GeoDataFrame(
        {'cluster_id': range(len(clusters_geom))},
        geometry=clusters_geom,
        crs=gdf_lcp.crs
    )

    # 6. Assigner chaque impact à son groupe fusionné
    joined_idx = joined_exact.reset_index(drop=True).drop(columns=['index_right'], errors='ignore')
    sjoin_clusters = gpd.sjoin(joined_idx, gdf_clusters, how='left', predicate='intersects')

    # 7. Agrégation finale
    # On fusionne les infos textuelles
    agg = sjoin_clusters.groupby('cluster_id').agg(
        wc_code=('wc_code', lambda s: s.mode().iloc[0]),
        node_1=('node_1', 'first'),
        node_2=('node_2', 'first')
    ).reset_index()

    # Création du point géographique définitif (le centroïde du cluster entier)
    geoms_by_cluster = sjoin_clusters.groupby('cluster_id').apply(
        lambda g: g.geometry.union_all().centroid,
        include_groups=False 
    ).reset_index(name='geometry')

    result = agg.merge(geoms_by_cluster, on='cluster_id')
    result = gpd.GeoDataFrame(result, geometry='geometry', crs=gdf_lcp.crs)
    result = result.rename(columns={'cluster_id': 'pn_id'})

    return result
    
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
#         déterminer obstacle_priority (NaN → 'prioritaire', sinon 'secondaire').
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

#     # 3. Jointure spatiale : LCP × obstacles
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

#     # 5. Clustering β : bufferisation + union → groupes spatiaux
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

def create_urban_planning_segments(gdf_lcp, df_nodes, tolerance=0.1, buffer_dist=15.0):
    """
    Transforme les corridors LCP en segments d'aménagement urbain uniques.
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
            
        # On récupère toutes les coordonnées de la ligne
        coords = list(geom.coords)
        start_pt = Point(coords[0])
        end_pt = Point(coords[-1])
        
        # On trouve le point exact le plus proche sur le polygone d'habitat
        # nearest_points renvoie (point_sur_ligne, point_sur_polygone)
        _, snap_start = nearest_points(start_pt, habitats_union)
        _, snap_end = nearest_points(end_pt, habitats_union)
        
        # On ajoute ces points aux extrémités de la ligne pour forcer le contact
        extended_coords = [snap_start.coords[0]] + coords + [snap_end.coords[0]]
        new_geoms.append(LineString(extended_coords))
        
    gdf_matrix['geometry'] = new_geoms
    # -------------------------------------------

    # Maintenant, le difference va trancher net toutes les lignes !
    # Puisqu'on les a forcées à toucher/rentrer dans le polygone, 
    # la coupe sera absolument parfaite et alignée avec la bordure.
    gdf_matrix['geometry'] = gdf_matrix.geometry.difference(habitats_union)
    gdf_matrix = gdf_matrix[~gdf_matrix.geometry.is_empty].copy()
    
    # Éclater la ligne en tous ses fragments
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

    # b) Identifier ce qui "rase les murs" (entièrement coincé dans le buffer de 15m)
    habitats_buffered = habitats_union.buffer(buffer_dist)
    exploded['is_skirting'] = exploded.geometry.within(habitats_buffered)

    # c)
    # Est un artefact : Une ligne qui rase les murs (is_skirting = True) ET qui ne connecte pas 2 habitats (num_nodes < 2).
    # On jette également par sécurité toutes les microscopiques scories de moins de 2 mètres.
    mask_artifact = (exploded['is_skirting'] & (exploded['num_nodes'] < 2)) | (exploded.geometry.length < 2.0)

    # On ne garde que ce qui n'est PAS un artefact
    exploded_clean = exploded[~mask_artifact].copy()
    
    # On ressoude le tout pour repasser à l'étape suivante
    gdf_matrix = exploded_clean.dissolve(by='lcp_id')
    gdf_matrix['geometry'] = gdf_matrix['geometry'].apply(
        lambda g: linemerge(g) if g.geom_type == 'MultiLineString' else g
    )

    # On simplifie les LCP pour tuer le bruit raster (les pixels en escalier).
    # tolerance=2.0 (mètres). 
    gdf_matrix['geometry'] = gdf_matrix.geometry.simplify(tolerance=2.0, preserve_topology=True)

    # 2. Découpage topologique aux intersections
    merged = unary_union(gdf_matrix.geometry.tolist())
    if hasattr(merged, 'geoms'):
        lines = [g for g in merged.geoms if g.geom_type == 'LineString']
        for mg in [g for g in merged.geoms if g.geom_type == 'MultiLineString']:
            lines.extend(list(mg.geoms))
    else:
        lines = [merged]
        
    gdf_segments = gpd.GeoDataFrame(geometry=lines, crs=gdf_lcp.crs)
    gdf_segments['segment_id'] = range(len(gdf_segments))

    # 3. Agrégation spatiale des métriques (dPC, EBC, Pinch Point)
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

    # On définit des règles d'arrondi logiques pour le regroupement (weld)
    rounding_rules = {
        'sum_dPC': 12,          # On passe à 12 décimales pour ne pas tuer le dPC (ex: 0.000000508736)
        'max_ebc': 3,           # Échelle 0-1 : 3 décimales suffisent (ex: 0.293)
        'max_pinch_point': 2    # Grande échelle : 1 décimale suffit pour lisser le bruit (ex: 26.9)
    }

    for col, decimals in rounding_rules.items():
        if col in gdf_final.columns:
            # On crée la colonne de groupe avec l'arrondi personnalisé
            gdf_final[f'grp_{col}'] = gdf_final[col].round(decimals)
            
    return gdf_final

def weld_segments(gdf_final):
    """Soude les segments géométriques ayant les mêmes attributs"""
    dissolve_cols = ['corridor_count'] + [c for c in gdf_final.columns if 'grp_' in c]
    
    gdf_clean = gdf_final.dissolve(by=dissolve_cols).reset_index()
    
    # Le linemerge va fonctionner parfaitement car les points d'ancrage lissés 
    # ont exactement les mêmes coordonnées flottantes !
    gdf_clean['geometry'] = gdf_clean['geometry'].apply(
        lambda g: linemerge(g) if g.geom_type == 'MultiLineString' else g
    )
    gdf_clean = gdf_clean.explode(index_parts=False).reset_index(drop=True)
    
    cols_to_drop = [c for c in gdf_clean.columns if 'grp_' in c]
    gdf_clean = gdf_clean.drop(columns=cols_to_drop + ['segment_id'], errors='ignore')
    gdf_clean['segment_id'] = range(len(gdf_clean))
    
    return gdf_clean

# def create_urban_planning_segments(gdf_lcp, df_nodes, tolerance=0.1, artifact_threshold=14.5):
#     """
#     Transforme les corridors LCP en segments d'aménagement urbain uniques.
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
    
#     # Éclater la ligne en tous ses fragments (MultiLineString -> LineStrings)
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
    
#     # 2. Découpage topologique aux intersections
#     merged = unary_union(gdf_matrix.geometry.tolist())
#     if hasattr(merged, 'geoms'):
#         lines = [g for g in merged.geoms if g.geom_type == 'LineString']
#         for mg in [g for g in merged.geoms if g.geom_type == 'MultiLineString']:
#             lines.extend(list(mg.geoms))
#     else:
#         lines = [merged]
        
#     gdf_segments = gpd.GeoDataFrame(geometry=lines, crs=gdf_lcp.crs)
#     gdf_segments['segment_id'] = range(len(gdf_segments))

#     # 3. Agrégation spatiale des métriques (dPC, EBC, Pinch Point)
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