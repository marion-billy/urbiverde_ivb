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

    count_func = len(gdf_lcp)
    count_rupt = len(rupture_corridors) if not rupture_corridors.empty else 0
    count_nodes = len(df_nodes)
    count_iso = len(isolated_nodes_list)
    
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
        mlines.Line2D([], [], color='#adb5bd', linewidth=2, label=f'Corridors Fonctionnels ({count_func})'),
        mlines.Line2D([], [], color='#ff0055', linewidth=2, label=f'Zones de Rupture ({count_rupt})'),
        mpatches.Patch(color='#206c2c', label=f'Habitat Patches ({count_nodes})'),
        mpatches.Patch(facecolor='none', edgecolor='black', linewidth=2, label=f'Habitats Isolés ({count_iso})')
    ]
    
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
        'Local link':           ('#adb5bd', 1.4, 1), 
        'Redundant mesh':       ('#0064d2', 1.6, 2),
        'Strategic bottleneck': ('#6200EA', 1.8, 3), 
        'Ecological highway':   ('#FF6D00', 2.0, 4) 
    }
    
    for cat, (color, lw, z) in style_map.items():
        subset = gdf_lcp[gdf_lcp['category'] == cat]
        if not subset.empty:
            subset.plot(ax=ax, color=color, linewidth=lw, alpha=0.7, zorder=z)

    # Nœuds (Habitats)
    df_nodes.plot(ax=ax, color='#206c2c', alpha=0.6, zorder=5)

    handles = [mlines.Line2D([], [], color=c, linewidth=2.5, label=f"{l}") 
               for l, (c, w, z) in style_map.items()]
    handles.append(mpatches.Patch(color='#206c2c', label='Habitats'))
    
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
    aoi_utm.plot(ax=ax, facecolor="none", edgecolor='white', alpha=0.3, linewidth=1, zorder=3)
    ax.set_axis_off()
    plt.tight_layout()
    plt.show()