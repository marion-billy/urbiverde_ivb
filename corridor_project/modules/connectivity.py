import sys
import pandas as pd
import numpy as np
import xarray as xr
import geopandas as gpd
from scipy import ndimage
from tqdm import tqdm
from rasterio import features
from shapely.geometry import shape
from affine import Affine
import networkx as nx
from sklearn.neighbors import BallTree
from shapely.geometry import LineString, Point
from typing import Optional, Union, Any, List, Union, Tuple
sys.path.insert(1, '../../Hugo/a_b_c_functions/spatial_analysis/')
from utils_raster import raster_to_polygon

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
    
    # --- C. On ré-emballe dans des DataArrays (on copie les coordonnées de l'entrée) ---
    da_core = da_binary.copy(data=core_arr.astype('uint8'))
    da_islet = da_binary.copy(data=islet_arr.astype('uint8'))
    
    return da_core, da_islet

def get_connectivity_elements(
    da_binary: xr.DataArray, 
    core_min_ha: float = 1.0, 
    islet_min_ha: float = 0.1
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Identifie et classe les éléments de connectivité (Noyaux et Stepping Stones).
    Les Cores trop petits pour être des Noyaux sont déclassés en Stepping Stones.
    """
    
    # 1. Calcul MSPA
    da_core, da_islet = fast_mspa(da_binary, edge_width_pixels=1)
    
    # 2. Vectorisation des Cores
    gdf_cores_all = raster_to_polygon(da_core, data_type='uint8')
    gdf_cores_all = gdf_cores_all[gdf_cores_all['value'] == 1].copy()
    gdf_cores_all['area_ha'] = gdf_cores_all.geometry.area / 10000
    
    # 3. Séparation des Cores selon le seuil de surface
    gdf_cores_final = gdf_cores_all[gdf_cores_all['area_ha'] >= core_min_ha].copy()
    gdf_cores_final['class'] = "Core (Noyau)"
    # Les Cores déclassés
    gdf_cores_small = gdf_cores_all[
        (gdf_cores_all['area_ha'] < core_min_ha) & 
        (gdf_cores_all['area_ha'] >= islet_min_ha)
    ].copy()
    gdf_cores_small['class'] = "Stepping Stone (Small Core)"

    # 4. Extraction des Islets (sans core)
    gdf_islets_raw = raster_to_polygon(da_islet, data_type='uint8')
    gdf_islets_raw = gdf_islets_raw[gdf_islets_raw['value'] == 1].copy()
    gdf_islets_raw['area_ha'] = gdf_islets_raw.geometry.area / 10000
    # Filtre de surface pour les Islets
    gdf_islets_raw = gdf_islets_raw[gdf_islets_raw['area_ha'] >= islet_min_ha].copy()
    gdf_islets_raw['class'] = "Stepping Stone (Islet)"

    # 5. Fusion pour créer la couche finale des Stepping Stones
    gdf_stepping_stones = pd.concat([gdf_islets_raw, gdf_cores_small], ignore_index=True)

    return gdf_cores_final, gdf_stepping_stones
    
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

def build_connectivity_graph_knn(nodes_df: pd.DataFrame, species_params: dict[str, Any]) -> nx.Graph:
    """
    Builds a K-Nearest Neighbors (KNN) graph using species-specific dispersal parameters.

    Args:
        nodes_df (pd.DataFrame): Patches with centroids ('x', 'y') and 'area_ha'.
        species_params (dict): Must contain 'd0' (dispersion_distance) and 'k_neighbors' (k).

    Returns:
        nx.Graph: Probabilistic connectivity network.
    """
    graph_params = species_params['graph'] 
    d0 = graph_params['d0']
    k = graph_params['k_neighbors']

    # Squelette du graph
    G = nx.Graph()
    for i, row in nodes_df.iterrows():
        G.add_node(i, area=row['area_ha'], type=row['node_type'], pos=(row['x'], row['y']))

    # Recherche de voisinage
    coords = nodes_df[['x', 'y']].values
    tree = BallTree(coords)
    distances, indices = tree.query(coords, k=k+1)

    # Création des liens et calcul des probabilités
    for i in range(len(coords)):
        for d, j_idx in zip(distances[i][1:], indices[i][1:]):
            if d > (2 * d0): # Limite biologique de 3 * d0 (environ 13% de probabilité de survie)
                continue

            prob = np.exp(-d / d0) #probability of movement: exponential decay function
            cost_val = -np.log(prob) #transformer la proba en log pour l'algo Dijkstra, astuce mathématique
            G.add_edge(i, j_idx, 
                       dist_m=d, 
                       prob=prob, 
                       cost_log=cost_val)
            
    #  DIAGNOSTIC
    isolated_nodes = [n for n, deg in G.degree() if deg == 0]
    n_isolated = len(isolated_nodes)
    print(f"Graphe construit : {G.number_of_nodes()} nœuds et {G.number_of_edges()} arêtes.")
    if n_isolated > 0:
        print(f"Alerte : {n_isolated} réservoirs sont totalement isolés.")
        
    return G
    
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
    
def graph_to_gdf_edges(G, crs):
    """Transforme toutes les arêtes d'un graphe NetworkX en GeoDataFrame."""
    edges = []
    for u, v, data in G.edges(data=True):
        edges.append({
            'node_1': u,
            'node_2': v,
            'dist_m': data['dist_m'],
            'cost_log': data['cost_log'],
            'geometry': LineString([Point(G.nodes[u]['pos']), Point(G.nodes[v]['pos'])])
        })
    return gpd.GeoDataFrame(edges, crs=crs)

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
    
    # Déballage des résultats dans les nouvelles colonnes
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
    
    # 3. Normalisation de 0 à 100 pour la lisibilité
    if df['ebc_score'].max() > 0:
        df['ebc_score'] = (df['ebc_score'] / df['ebc_score'].max()) * 100
        
    return df.sort_values(by='ebc_score', ascending=False)

def calculate_node_dpc(G_curr: nx.Graph, total_area_km2: float, species_params: dict) -> pd.DataFrame:
    """
    Calcule spécifiquement la fraction 'Connector' du dPC pour chaque nœud.
    Identifie les stepping stones vitaux de Nancy.
    """
    # 1. Calcul du PC de référence (Réseau complet)
    pc_ref, _ = calculate_pc_index_lcp(G_curr, total_area_km2, species_params)
    nodes = list(G_curr.nodes())
    results = []

    print(f"Analyse de connectivité pour {len(nodes)} noyaux...")
    for node_i in tqdm(nodes, desc="Calcul dPC Nodes", unit="node"):
        # A. Fraction Intra : Importance de la surface propre (ai * ai)
        a_i = G_curr.nodes[node_i]['area'] / 100
        dpc_intra = (a_i * a_i) / (total_area_km2**2)
        
        # B. Calcul du PC sans le noeud i pour isoler le reste
        G_temp = G_curr.copy()
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
            'area_ha': G_curr.nodes[node_i]['area'],
            'dPC_total': (dpc_total / pc_ref) * 100,
            'dPC_connector': (dpc_connector / pc_ref) * 100
        })

    return pd.DataFrame(results).sort_values('dPC_connector', ascending=False)
    
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