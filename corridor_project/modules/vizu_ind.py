import networkx as nx
import matplotlib.pyplot as plt
import geopandas as gpd
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.colors as colors
from matplotlib.ticker import ScalarFormatter
from scipy import ndimage

def plot_connectivity_ruptures(gdf_lcp, aoi_utm, df_nodes):
    """
    Identifie les zones de rupture et les habitats isolés.
    Le graphe des succès est reconstruit dynamiquement à partir du GDF.
    """
    # 1. Identifier les corridors supprimés
    gdf_success = gdf_lcp[gdf_lcp['status'] == 'success']
    gdf_failed = gdf_lcp[gdf_lcp['status'] == 'failed']
    
    # 2. Identifier les nœuds isolés
    G_success = nx.from_pandas_edgelist(gdf_success, 'node_1', 'node_2')
    G_success.add_nodes_from(df_nodes.index) # Garantit que tous les habitats sont inclus
    isolated_nodes_list = list(nx.isolates(G_success))
    isolated_nodes_gdf = df_nodes[df_nodes.index.isin(isolated_nodes_list)]
    
    # 3. Préparation de la carte
    fig, ax = plt.subplots(figsize=(14, 12))
    aoi_utm.plot(ax=ax, color='#f8f9fa', edgecolor='#ced4da')
    
    # Corridors fonctionnels (Succès)
    if not gdf_success.empty:
        gdf_success.plot(ax=ax, color='#adb5bd', alpha=0.6, linewidth=1.4)
    # Zones de rupture (Échecs)
    if not gdf_failed.empty:
        gdf_failed.plot(ax=ax, color='#ff0055', alpha=0.6, linewidth=1.8, linestyle='--')
    
    # Tous les habitats (Nœuds)
    df_nodes.plot(ax=ax, color='#206c2c', markersize=10, alpha=0.6)
    # Bordure des habitats isolés
    if not isolated_nodes_gdf.empty:
        isolated_nodes_gdf.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1.5, markersize=100)

    # 4. Légende
    handles = [
        mlines.Line2D([], [], color='#adb5bd', linewidth=2, label=f'Corridors Fonctionnels ({len(gdf_success)})'),
        mlines.Line2D([], [], color='#ff0055', linewidth=2, linestyle='--', label=f'Zones de Rupture ({len(gdf_failed)})'),
        mlines.Line2D([], [], color='#206c2c', marker='o', linestyle='None', label=f'Habitat Patches ({len(df_nodes)})'),
        mlines.Line2D([], [], marker='o', markerfacecolor='none', markeredgecolor='black', linestyle='None', label=f'Habitats Isolés ({len(isolated_nodes_gdf)})')
    ]

    aoi_utm.plot(ax=ax, facecolor="none", edgecolor='black', alpha=0.6, linewidth=2)
    plt.title("Diagnostic : Zones de rupture et habitats isolés", fontsize=16, color='black', pad=20)
    plt.legend(handles=handles, loc='upper right', fontsize=12)
    ax.set_axis_off()
    plt.tight_layout()
    plt.show()

def plot_classified_corridors(gdf_lcp: gpd.GeoDataFrame, df_nodes: gpd.GeoDataFrame, aoi_utm: gpd.GeoDataFrame):
    """
    Generates a diagnostic map of four corridors types based on Flow and Rarity.
    """
    fig, ax = plt.subplots(figsize=(14, 12))
    aoi_utm.plot(ax=ax, color='#f8f9fa', edgecolor='#ced4da', zorder=1)
    
    style_map = {
        'Local link':           ('#adb5bd', 1.4, 2), 
        'Redundant mesh':       ('#0064d2', 1.6, 3),
        'Strategic bottleneck': ('#6200EA', 1.8, 4), 
        'Ecological highway':   ('#FF6D00', 2.0, 5) 
    }
    
    for cat, (color, lw, z) in style_map.items():
        subset = gdf_lcp[gdf_lcp['category'] == cat]
        if not subset.empty:
            subset.plot(ax=ax, color=color, linewidth=lw, alpha=0.7, zorder=z)

    # Nœuds (Habitats)
    df_nodes.plot(ax=ax, color='#206c2c', alpha=0.6, zorder=1)

    handles = [mlines.Line2D([], [], color=c, linewidth=2.5, label=f"{l}") 
               for l, (c, w, z) in style_map.items()]
    handles.append(mpatches.Patch(color='#206c2c', label='Habitats'))

    aoi_utm.plot(ax=ax, facecolor="none", edgecolor='black', alpha=0.6, linewidth=2, zorder=6)
    plt.legend(handles=handles, loc='upper right', fontsize=12, frameon=True)
    plt.title(f"Diagnostic de Connectivité : Hiérarchie des Corridors", fontsize=16, color='black', pad=20)
    ax.set_axis_off()
    plt.tight_layout()
    plt.show()

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
    aoi_utm.plot(ax=ax, facecolor="none", edgecolor='white', alpha=0.6, linewidth=2, zorder=3)
    ax.set_axis_off()
    plt.tight_layout()
    plt.show()