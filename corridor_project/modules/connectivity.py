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
from shapely.ops import nearest_points
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

def build_connectivity_graph_knn(nodes_df: gpd.GeoDataFrame, species_params: dict[str, Any]) -> nx.Graph:
    """
    Builds a K-Nearest Neighbors (KNN) graph using species-specific dispersal parameters.
    Use minimum distance between polygon boundaries (Edge-to-Edge) instead of centroids.

    Args:
        nodes_df (gpd.GeoDataFrame): Patches with centroids ('x', 'y') and 'total_area_ha'.
        species_params (dict): Must contain 'd0' (dispersion_distance) and 'k_neighbors' (k).

    Returns:
        nx.Graph: Probabilistic connectivity network.
    """
    d0 = species_params['graph']['d0']
    k = species_params['graph']['k_neighbors']
    max_dist = 3 * d0  # Limite biologique de 3 * d0 (environ 13% de probabilité de survie)
    
    # Squelette du graph
    G = nx.Graph()
    for i, row in nodes_df.iterrows():
        G.add_node(i, area=row['total_area_ha'], type=row['node_type'], pos=(row['x'], row['y']))

    sindex = nodes_df.sindex
    for i, row in nodes_df.iterrows():
        current_geom = row.geometry
        possible_neighbors_idx = list(sindex.query(current_geom.buffer(max_dist))) 
        
        # Calculate real geometry-to-geometry distances
        neighbor_data = []
        for idx in possible_neighbors_idx:
            if idx == i: continue
            target_geom = nodes_df.iloc[idx].geometry
            dist = current_geom.distance(target_geom)
            
            if dist <= max_dist:
                p1, p2 = nearest_points(current_geom, target_geom)
                neighbor_data.append((idx, dist, p1, p2))
        
        # Sort by distance and take the K closest
        neighbor_data.sort(key=lambda x: x[1])
        for j_idx, d, p1, p2 in neighbor_data[:k]:
            if not G.has_edge(i, j_idx):
                prob = np.exp(-d / d0) #probability of movement: exponential decay function
                G.add_edge(i, j_idx, dist_m=d, prob=prob, 
                           cost_log=-np.log(prob), #transformer la proba en log pour l'algo Dijkstra, astuce mathématique
                           anchor_pts=(p1, p2))

    # --- DIAGNOSTIC ---
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    isolated_nodes = [n for n, deg in G.degree() if deg == 0]
    n_isolated = len(isolated_nodes)
    print(f"✓ Graphe construit : {n_nodes} nœuds et {n_edges} arêtes.")

    if n_isolated > 0:
        percent_isolated = (n_isolated / n_nodes) * 100
        print(f"Warning : {n_isolated} réservoirs ({percent_isolated:.1f}%) sont totalement isolés.")
            
    return G

def build_rng_graph(nodes_df: gpd.GeoDataFrame, species_params: dict) -> nx.Graph:
    """
    Builds a Relative Neighborhood Graph (RNG) using geometry-to-geometry distances.
    Prunes edges where an intermediate patch C provides a 'shorter' jump.
    """
    d0 = species_params['graph']['d0']
    max_dist = 3 * d0 # Limite biologique de 3 * d0 (environ 13% de probabilité de survie)

    # On commence par un graphe de base (tous les voisins dans le rayon max_dist)
    G_candidate = nx.Graph()
    for i, row in nodes_df.iterrows():
        G_candidate.add_node(i, area=row['total_area_ha'], type=row['node_type'], pos=(row['x'], row['y']))
    sindex = nodes_df.sindex
    candidate_edges = []

    # Trouver tous les candidats possibles (Recherche spatiale)
    for i, row in tqdm(nodes_df.iterrows(), total=len(nodes_df), desc="Étape 1/2: Recherche candidats"):
        current_geom = row.geometry
        possible_neighbors = list(sindex.query(current_geom.buffer(max_dist)))
        
        for idx in possible_neighbors:
            if idx <= i: continue # On évite les doublons (A-B et B-A)
            
            dist = current_geom.distance(nodes_df.iloc[idx].geometry)
            if dist <= max_dist:
                p1, p2 = nearest_points(current_geom, nodes_df.iloc[idx].geometry)
                candidate_edges.append({
                    'u': i, 'v': idx, 'dist': dist, 'p1': p1, 'p2': p2
                })

    # Filtrage RNG
    G_rng = nx.Graph()
    G_rng.add_nodes_from(G_candidate.nodes(data=True))

    for edge in tqdm(candidate_edges, desc="Étape 2/2: Filtrage RNG"):
        u, v, dist_uv = edge['u'], edge['v'], edge['dist']
        is_rng = True
        
        # Critère RNG : Est-ce qu'il existe un patch C tel que dist(u,c) < dist(uv) ET dist(v,c) < dist(uv) ?
        # On ne cherche que les C qui sont dans la zone d'intersection des deux cercles
        p_u, p_v = edge['p1'], edge['p2']
        search_zone = p_u.buffer(dist_uv).intersection(p_v.buffer(dist_uv))
        potential_c = list(sindex.query(search_zone))
        
        for idx_c in potential_c:
            if idx_c in [u, v]: continue
            
            geom_c = nodes_df.iloc[idx_c].geometry
            if nodes_df.iloc[u].geometry.distance(geom_c) < dist_uv and \
               nodes_df.iloc[v].geometry.distance(geom_c) < dist_uv:
                is_rng = False
                break
        
        if is_rng:
            prob = np.exp(-dist_uv / d0)
            G_rng.add_edge(u, v, 
                           dist_m=dist_uv, 
                           prob=prob, 
                           cost_log=-np.log(prob),
                           anchor_pts=(p_u, p_v))

    print(f"Graphe RNG construit : {G_rng.number_of_nodes()} nœuds et {G_rng.number_of_edges()} arêtes.")
    return G_rng

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
    Calcule le PC réel.
    Si gdf_lcp est fourni, met à jour le graphe. 
    Sinon, utilise le graphe tel quel (utile pour les itérations dPC).
    """
    d0 = species_params['graph']['d0']
    G_curr = G.copy()
    
    # Mise à jour seulement si on passe un nouveau GeoDataFrame (premier appel)
    if gdf_lcp is not None:
        lcp_lookup = {(int(row['node_1']), int(row['node_2'])): row['real_dist'] 
                      for _, row in gdf_lcp.iterrows()}
        for u, v in G_curr.edges():
            dist = lcp_lookup.get((u, v)) or lcp_lookup.get((v, u))
            if dist is not None:
                cost = dist / d0
                G_curr[u][v].update({'dist_m': dist, 'prob': np.exp(-cost), 'cost_log': cost})
                
    # Calcul mathématique du PC
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

def calculate_node_dpc(G_lcp: nx.Graph, total_area_km2: float, species_params: dict) -> pd.DataFrame:
    """
    Calcule spécifiquement la fraction 'Connector' du dPC pour chaque nœud.
    """
    # 1. Calcul du PC de référence (Réseau complet)
    pc_ref, _ = calculate_pc_index_lcp(G_lcp, total_area_km2, species_params)
    nodes = list(G_lcp.nodes())
    results = []

    print(f"Analyse de connectivité pour {len(nodes)} noyaux...")
    for node_i in tqdm(nodes, desc="Calcul dPC Nodes", unit="node"):
        # A. Fraction Intra : Importance de la surface propre (ai * ai)
        a_i = G_lcp.nodes[node_i]['area'] / 100
        dpc_intra = (a_i * a_i) / (total_area_km2**2)
        
        # B. Calcul du PC sans le noeud i pour isoler le reste
        G_temp = G_lcp.copy()
        G_temp.remove_node(node_i)


        pc_res = calculate_pc_index_lcp(G_temp, total_area_km2, species_params)
        pc_minus_i = pc_res[0] if isinstance(pc_res, tuple) else pc_res
        
        # C. dPC Total de ce noeud
        dpc_total = pc_ref - pc_minus_i
        
        # D. Calcul du Flux (contribution aux chemins où i est source ou destination)
        # Dans la pratique, on simplifie souvent : Connector = Total - Intra - Flux
        # Mais mathématiquement, le Connector est le rôle de "relais" entre j et k via i
        
        # Pour isoler le Connector pur : 
        # C'est la part du PC qui s'effondre car i servait de pont entre d'autres noeuds
        dpc_connector = max(0, dpc_total - dpc_intra) # Simplification courante (Flux inclus souvent dans le résiduel)
        
        results.append({
            'node_id': node_i,
            'area_ha': G_lcp.nodes[node_i]['area'],
            'dPC_total': (dpc_total / pc_ref) * 100,
            'dPC_connector': (dpc_connector / pc_ref) * 100
        })

    return pd.DataFrame(results).sort_values('dPC_connector', ascending=False)

def classify_and_plot_corridors(gdf_lcp: gpd.GeoDataFrame, df_nodes: gpd.GeoDataFrame, aoi_utm: gpd.GeoDataFrame, q: float = 0.5):
    """
    Categorizes corridors into four strategic types based on Flow and Rarity,
    and generates a diagnostic map.
    
    Args:
        gdf_lcp: GeoDataFrame containing dPC_relative and ebc_score.
        aoi_utm: GeoDataFrame of the study area boundary.
        q: Quantile threshold for classification (default 0.5 for median).
    """
    # 1. Define thresholds
    flow_threshold = gdf_lcp['dPC_relative'].quantile(q)
    rarity_threshold = gdf_lcp['ebc_score'].quantile(q)

    # 2. Assign Categories
    def _classify(row):
        hi_flow = row['dPC_relative'] > flow_threshold
        hi_rarity = row['ebc_score'] > rarity_threshold
        
        if hi_flow and hi_rarity: return 'Ecological highway'
        if not hi_flow and hi_rarity: return 'Strategic bottleneck'
        if hi_flow and not hi_rarity: return 'Redundant mesh'
        return 'Local link'

    gdf_lcp['category'] = gdf_lcp.apply(_classify, axis=1)

    # 3. Visualization
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.set_facecolor('white')
    aoi_utm.plot(ax=ax, color='#f8f9fa', edgecolor='#ced4da', zorder=1)
    df_nodes.plot(ax=ax, color='#2d6a4f', alpha=0.5, label='Habitats', zorder=2)

    order = [
        ('Local link', '#adb5bd', 0.6, 1.4),       # Gris, fin
        ('Redundant mesh', '#3f37c9', 0.7, 1.6),    # Bleu
        ('Strategic bottleneck', '#ffba08', 0.9, 1.8), # Or/Orange, plus épais
        ('Ecological highway', '#d00000', 1.0, 2)    # Rouge, au-dessus
    ]
    
    for cat, color, alpha, linewidth in order:
            subset = gdf_lcp[gdf_lcp['category'] == cat]
            if not subset.empty:
                subset.plot(
                    ax=ax, 
                    color=color, 
                    linewidth=linewidth, 
                    alpha=alpha, 
                    label=f"{cat} ({len(subset)})", 
                    zorder=3 if cat in ['Local link', 'Redundant mesh'] else 4
                )

    plt.legend(title="Catégories de Corridors", loc='lower right', frameon=True, fontsize=10)
    plt.title(f"Diagnostic de Connectivité : Hiérarchie des Corridors LCP", fontsize=15, pad=20)
    ax.set_axis_off()
    plt.tight_layout()
    
    return gdf_lcp

def lcp_heatmap(gdf_lcp: gpd.GeoDataFrame, aoi_utm: gpd.GeoDataFrame, res: int = 10, crs_utm: str = None) -> xr.DataArray:
    """
    Génère une heatmap de densité des chemins LCP.
    Chaque pixel contient le nombre de chemins qui le traversent.
    
    Args:
        gdf_lcp: GeoDataFrame des chemins (LCP).
        aoi_utm: GeoDataFrame de la zone d'étude (pour cadrer le raster).
        res: Résolution spatiale en mètres (par défaut 10m).
        crs_utm
    """
    
    # 1. Création du template vide (Image de référence)
    da_ref = create_img_reference(aoi_utm, spatial_resolution=res, output_crs=crs_utm)
    
    # 2. Alignement des données
    gdf_lcp_utm = gdf_lcp.to_crs(da_ref.rio.crs)
    
    # 3. Préparation des formes pour la rasterisation
    # On attribue la valeur 1 à chaque géométrie
    shapes = [(geom, 1) for geom in gdf_lcp_utm.geometry if geom is not None]

    # 4. Rasterisation par accumulation 
    heatmap_arr = features.rasterize(
        shapes=shapes,
        out_shape=(da_ref.rio.height, da_ref.rio.width),
        transform=da_ref.rio.transform(),
        fill=0,
        all_touched=True, 
        merge_alg=MergeAlg.add,
        dtype='uint32'
    )

    # 5. Conversion en DataArray
    da_heatmap = xr.DataArray(
        heatmap_arr,
        coords={"y": da_ref.y, "x": da_ref.x},
        dims=("y", "x"),
        name="lcp_density"
    ).rio.write_crs(da_ref.rio.crs)
    
    return da_heatmap
    
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