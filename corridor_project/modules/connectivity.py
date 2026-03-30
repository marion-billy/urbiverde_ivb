import pandas as pd
import numpy as np
import xarray as xr
import geopandas as gpd
from scipy import ndimage
from rasterio import features
from shapely.geometry import shape
from affine import Affine
import networkx as nx
from sklearn.neighbors import BallTree
from shapely.geometry import LineString, Point
from typing import Optional, Union, Any, List, Union, Tuple

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

def fast_mspa(binary_mask: np.ndarray, edge_width_pixels: int = 1) -> Tuple[np.ndarray, np.ndarray]:
    """
    Identifie les catégories morphologiques Cores et Islets.
    Permet de varier la sensibilité à la lisière via edge_width_pixels.
    
    Args:
        binary_mask (np.array): Masque binaire de l'habitat (1: habitat, 0: reste).
        edge_width_pixels (int): Nombre de pixels à "raboter" sur le bord.
            Ex: 1 pixel = 10m de lisière, 2 pixels = 20m.
        
    Returns:
        tuple: (core_array, islet_array)
    """
    # 1. ÉLÉMENT STRUCTURANT (Connectivité Reine / 8 voisins)
    # np.ones((3,3)) définit un voisinage complet (côtés + diagonales)
    struct = np.ones((3,3))
    
    # 2. ÉROSION (Création du Core)
    # On répète l'érosion selon la largeur de lisière souhaitée
    # Plus on augmente 'iterations', plus le Core rétrécit
    core = ndimage.binary_erosion(binary_mask, structure=struct, iterations=edge_width_pixels)
    
    # 3. LABELLISATION (Identification des taches d'origine)
    labels, n_labels = ndimage.label(binary_mask)
    
    # 4. IDENTIFICATION DES ISLETS
    # Un Islet est une tache qui disparaît COMPLÈTEMENT après l'érosion.
    # On trouve les IDs des taches qui ont survécu (qui contiennent du Core)
    labels_with_core = np.unique(labels[core > 0])
    
    # Masque des taches contenant un Core
    is_core_patch = np.isin(labels, labels_with_core)
    
    # Islet = C'est de l'habitat (label > 0) mais sans aucun pixel Core à l'intérieur
    islet = (labels > 0) & (~is_core_patch)
    
    return core.astype('uint8'), islet.astype('uint8')
    
def vectoriser_et_filtrer(
    array: np.ndarray, 
    transform: Affine, 
    crs: str, 
    min_area_ha: float, 
    label_name: str = "type"
) -> gpd.GeoDataFrame:
    """
    Transforme un masque raster en GeoDataFrame vectoriel filtré par surface.
    
    Args:
        array (np.array): Masque binaire à vectoriser.
        transform (affine.Affine): Transformation affine du raster (rio.transform()).
        crs (str): Système de projection (ex: 'EPSG:2154').
        min_area_ha (float): Seuil de surface minimale en hectares.
        label_name (str): Nom de la classe pour la colonne 'class'.
        
    Returns:
        gpd.GeoDataFrame: Polygones filtrés avec calcul de surface.
    """
    # Extraction des géométries (uniquement pour les valeurs 1)
    shapes = features.shapes(array, mask=(array > 0), transform=transform)
    
    polygons = []
    for geom, val in shapes:
        poly_geom = shape(geom)
        area_ha = poly_geom.area / 10000 # Conversion m² vers Hectares
        
        # Filtre sur la taille critique (Réservoir vs Stepping Stone)
        if area_ha >= min_area_ha:
            polygons.append({
                'geometry': poly_geom,
                'area_ha': area_ha,
                'class': label_name
            })
    
    # Gestion du cas où aucun polygone ne dépasse le seuil
    if not polygons:
        return gpd.GeoDataFrame(columns=['geometry', 'area_ha', 'class'], crs=crs)
        
    return gpd.GeoDataFrame(polygons, crs=crs)

def prepare_graph_nodes(gdf_cores: gpd.GeoDataFrame, gdf_islets: gpd.GeoDataFrame) -> pd.DataFrame:
    """
    Merges core habitats and stepping stones into a unified dataset and extracts centroids.

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
    
    # Use centroids for nodal representation in the graph
    centroids = nodes.geometry.centroid
    nodes['x'] = centroids.x
    nodes['y'] = centroids.y
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
    
    G = nx.Graph()

    # Initialize nodes with attributes
    for i, row in nodes_df.iterrows():
        G.add_node(i, 
                   area=row['area_ha'], 
                   type=row['node_type'], 
                   pos=(row['x'], row['y']))
    
    coords = nodes_df[['x', 'y']].values
    tree = BallTree(coords)
    
    # Query K+1 neighbors to find the K nearest (excluding self)
    distances, indices = tree.query(coords, k=k+1)

    for i in range(len(coords)):
        # Skip the first result as it is the node itself
        for d, j_idx in zip(distances[i][1:], indices[i][1:]):
            # Probability of movement: exponential decay function
            prob = np.exp(-d / d0)
            
            # cost_log = -ln(prob). Lower cost = higher probability.
            G.add_edge(i, j_idx, 
                       weight=d, 
                       prob=prob, 
                       cost_log=-np.log(prob))
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
    # Optimization: Calculate by connected components
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
                elif n2 in path_lengths[n1]:
                    # Convert log-cost back to probability
                    prob_ij = np.exp(-path_lengths[n1][n2])
                else:
                    prob_ij = 0.0
                
                pc_sum += a_i * a_j * prob_ij
                
    return pc_sum / (total_area_km2**2)

def get_priority_corridors(
    G: nx.Graph, 
    crs: Any, 
    n_top: Optional[int] = None, 
    percentile: Optional[float] = None
) -> gpd.GeoDataFrame:
    """
    Identifies critical links based on Edge Betweenness Centrality.

    Args:
        G (nx.Graph): The connectivity graph.
        crs: CRS of the study area (e.g., 'EPSG:2154').
        n_top (int, optional): Fixed number of top corridors.
        percentile (float, optional): Percentage of top corridors (0-100).

    Returns:
        gpd.GeoDataFrame: Priority corridors represented as straight lines.
    """
    if G.number_of_edges() == 0:
        return gpd.GeoDataFrame(columns=['node_1', 'node_2', 'importance_score', 'geometry'], crs=crs)

    # Centrality measures the importance of a link for the global flow
    edge_centrality = nx.edge_betweenness_centrality(G, weight='cost_log')
    sorted_edges = sorted(edge_centrality.items(), key=lambda x: x[1], reverse=True)
    
    # Determine selection threshold
    if percentile is not None:
        limit = max(1, int(len(sorted_edges) * (percentile / 100)))
    elif n_top is not None:
        limit = min(n_top, len(sorted_edges))
    else:
        limit = len(sorted_edges)

    corridors = []
    for (u, v), score in sorted_edges[:limit]:
        corridors.append({
            'node_1': u,
            'node_2': v,
            'importance_score': score,
            'dist_m': G[u][v]['weight'],
            'geometry': LineString([Point(G.nodes[u]['pos']), Point(G.nodes[v]['pos'])])
        })
    
    return gpd.GeoDataFrame(corridors, crs=crs)