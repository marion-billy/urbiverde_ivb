import networkx as nx
import matplotlib.pyplot as plt
import geopandas as gpd
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.colors as colors
from matplotlib.ticker import ScalarFormatter
from scipy import ndimage

def plot_connectivity_ruptures(gdf_lcp0, gdf_lcp, aoi_utm, df_nodes, G_lcp):
    """
    Identifie les zones de rupture et les habitats isolés.
    """
    # 1. Identifier les corridors supprimés
    lcp_all = gdf_lcp0.set_index(['node_1', 'node_2'])
    lcp_clean = gdf_lcp.set_index(['node_1', 'node_2'])
    rupture_corridors = lcp_all.drop(lcp_clean.index, errors='ignore')
    
    # 2. Identifier les nœuds isolés 
    isolated_nodes_list = list(nx.isolates(G_lcp))
    isolated_nodes_gdf = df_nodes[df_nodes.index.isin(isolated_nodes_list)]
    
    # 3. Préparation de la carte
    fig, ax = plt.subplots(figsize=(14, 12))
    aoi_utm.plot(ax=ax, color='#f8f9fa', edgecolor='#ced4da')
    
    # Corridors fonctionnels
    gdf_lcp.plot(ax=ax, color='#adb5bd', alpha=0.6, linewidth=1.4)
    # Zones de rupture
    if not rupture_corridors.empty:
        gpd.GeoDataFrame(rupture_corridors, crs=gdf_lcp0.crs).plot(
            ax=ax, color='#ff0055', alpha=0.6, linewidth=1.8)
    
    # Tous les habitats
    df_nodes.plot(ax=ax, color='#206c2c', markersize=5, alpha=0.6)
    # Bordure des habitats isolés
    if not isolated_nodes_gdf.empty:
        isolated_nodes_gdf.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=2, markersize=100)

    handles = [
        mlines.Line2D([], [], color='#adb5bd', linewidth=2, label='Corridors Fonctionnels'),
        mlines.Line2D([], [], color='#ff0055', linewidth=2, label='Zones de Rupture'),
        mpatches.Patch(color='#206c2c', label='Habitat Patches'),
        mpatches.Patch(facecolor='none', edgecolor='black', linewidth=2, label='Habitat Isolé')
    ]
    
    plt.title("Diagnostic : Zones de rupture et habitats isolés", fontsize=16, color='black', pad=20)
    plt.legend(handles=handles, loc='upper right', fontsize=12)
    ax.set_axis_off()
    plt.tight_layout()
    plt.show()

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
    fig, ax = plt.subplots(figsize=(14, 12))
    aoi_utm.plot(ax=ax, color='#f8f9fa', edgecolor='#ced4da', zorder=1)
    
    style_map = {
        'Local link': ('#adb5bd', 1.4),
        'Redundant mesh': ('#3f37c9', 1.6),
        'Strategic bottleneck': ('#ffba08', 1.8),
        'Ecological highway': ('purple', 2.0)
    }  
    for cat, (color, lw) in style_map.items():
        subset = gdf_lcp[gdf_lcp['category'] == cat]
        if not subset.empty:
            subset.plot(ax=ax, color=color, linewidth=lw, alpha=0.6, zorder=3)

    df_nodes.plot(ax=ax, color='#206c2c', alpha=0.6, label='Habitats', zorder=2)

    handles = [mlines.Line2D([], [], color=c, label=f"{l}") for l, (c, w) in style_map.items()]
    handles.append(mpatches.Patch(color='#206c2c', label='Habitats'))
    
    plt.legend(handles=handles, loc='upper right', fontsize=12)
    plt.title(f"Diagnostic de Connectivité : Hiérarchie des Corridors", fontsize=16, color='black', pad=20)
    ax.set_axis_off()
    plt.tight_layout()
    return gdf_lcp

def plot_connectivity_heatmap(da_heatmap, df_nodes, aoi_utm, filter_size=3):
    """
    Génère et affiche la heatmap de connectivité avec les réservoirs superposés.
    
    Args:
        da_heatmap (xr.DataArray): La heatmap de densité LCP.
        df_nodes (gpd.GeoDataFrame): Les réservoirs/nœuds de biodiversité.
        aoi_utm (gpd.GeoDataFrame): La limite de la zone d'étude.
        filter_size (int): Taille du filtre maximum pour épaissir les corridors.
    """
    # 1. Préparation de la heatmap (Épaississement visuel)
    dilated_data = ndimage.maximum_filter(da_heatmap.values, size=filter_size) 
    da_heatmap_thick = da_heatmap.copy(data=dilated_data)
    heatmap_plot = da_heatmap_thick.where(da_heatmap_thick > 0)

    # 2. Configuration du graphique
    fig, ax = plt.subplots(figsize=(14, 12))
    fig.patch.set_facecolor('#2d2d2d') 
    ax.set_facecolor('#2d2d2d')

    # 3. Affichage des Réservoirs et Islets (Zorder 1)
    if df_nodes.crs is None:
        df_nodes.set_crs(aoi_utm.crs, inplace=True)
    # Reprojection vers le système de coordonnées de la heatmap
    nodes_to_plot = df_nodes.to_crs(da_heatmap.rio.crs)

    nodes_to_plot.plot(ax=ax, color='#206c2c', alpha=0.6, edgecolor='none', linewidth=0.5, markersize=20, zorder=1)

    # 4. Affichage de la Heatmap (Zorder 2)
    vmax = int(da_heatmap_thick.max())
    mappable = heatmap_plot.plot(
        ax=ax,
        cmap='inferno', 
        norm=colors.LogNorm(vmin=1, vmax=vmax),
        add_colorbar=True,
        add_labels=False,
        zorder=2,
        cbar_kwargs={
            'label': 'Nombre de passages',
            'format': ScalarFormatter(),
            'ticks': [1, 2, 5, 10, vmax]
        }
    )

    cbar = mappable.colorbar
    cbar.ax.tick_params(axis='y', colors='white')
    cbar.set_label('Nombre de passages', color='white')
    for label in cbar.ax.yaxis.get_ticklabels():
        label.set_color('white')

    # 5. Habillage (Zorder 3)
    aoi_utm.plot(ax=ax, facecolor="none", edgecolor='white', alpha=0.3, linewidth=1, zorder=3)
    ax.set_axis_off()
    plt.tight_layout()
    plt.show()