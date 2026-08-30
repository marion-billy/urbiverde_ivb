import networkx as nx
import matplotlib.pyplot as plt
import geopandas as gpd
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import matplotlib.colors as colors
from matplotlib.ticker import ScalarFormatter
from scipy import ndimage
import numpy as np
import xarray as xr

def plot_resistance_surface(resistance_raster, aoi_utm):
    fig, ax = plt.subplots(figsize=(14, 12))
    
    # On prépare une copie pour l'affichage (remplacer inf par une valeur haute mais finie pour le plot)
    plot_data = resistance_raster.where(resistance_raster != np.inf, resistance_raster.max() * 1.2)
    
    im = plot_data.plot(
        ax=ax,
        robust=True, 
        cmap='RdYlGn_r', 
        add_labels=False,
        cbar_kwargs={'label': 'Coût de déplacement (friction)'}
    )

    aoi_utm.plot(ax=ax, facecolor="none", edgecolor='black', alpha=0.6, linewidth=2)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Surface de Résistance (Coût de friction)", fontsize=12)
    ax.set_axis_off()
    plt.tight_layout()
    plt.show()

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
    all_isolated_nodes = df_nodes[df_nodes.index.isin(isolated_nodes_list)]
    isolated_nodes_gdf = all_isolated_nodes[all_isolated_nodes.geometry.intersects(aoi_utm.unary_union)]
    
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
    
def plot_segment_metric(gdf_lcp: gpd.GeoDataFrame, df_nodes: gpd.GeoDataFrame, aoi_utm: gpd.GeoDataFrame, 
                        score_col='corridor_count', 
                        cmap_name='plasma', 
                        title="", 
                        cbar_label=""):
    """
    Génère une carte de chaleur vectorielle dynamique pour n'importe quelle métrique.
    L'épaisseur et la couleur s'adaptent automatiquement au maximum de la colonne choisie.
    """
    fig, ax = plt.subplots(figsize=(14, 12))
    aoi_utm.plot(ax=ax, color='#f8f9fa', edgecolor='#ced4da', zorder=1)

    # Réservoirs d'habitat 
    df_nodes.plot(ax=ax, color='#206c2c', alpha=0.6, zorder=2)

    # Préparation des données
    gdf_plot = gdf_lcp[gdf_lcp[score_col] > 0].sort_values(by=score_col, ascending=True)
    vmax_val = gdf_plot[score_col].max()
    ratios = gdf_plot[score_col] / vmax_val
    lw_min=1.5   
    lw_max=8.0   
    power=2
    gdf_plot['dynamic_lw'] = lw_min + (ratios**power) * (lw_max - lw_min)

    gdf_plot.plot(ax=ax, column=score_col, cmap=cmap_name, linewidth=gdf_plot['dynamic_lw'], alpha=0.8, zorder=3)
    
    cmap = plt.get_cmap(cmap_name)
    norm = mcolors.Normalize(vmin=0, vmax=vmax_val)

    # Barre de légende
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, shrink=0.5, pad=0.02)
    cbar.set_label(cbar_label, color='black', fontsize=12, labelpad=10)
    cbar.ax.yaxis.set_tick_params(color='black', labelcolor='black')

    aoi_utm.plot(ax=ax, facecolor="none", edgecolor='black', alpha=0.3, linewidth=1, zorder=4)
    plt.title(title, color='black', fontsize=18, pad=20)
    ax.set_axis_off()
    plt.tight_layout()
    plt.show()

def plot_dispersal_surface(
    disp_da: xr.DataArray,
    aoi_utm: gpd.GeoDataFrame,
    df_nodes: gpd.GeoDataFrame,
    threshold: float,
    gdf_lcp: gpd.GeoDataFrame = None, 
    cmap_name: str = 'RdYlGn_r',
    title: str = "Carte de dispersion",
) -> None:
    """
    Affiche la carte de dispersion (surface de coût continue) avec échelle
    de couleur plafonnée.

    Le coût brut est conservé (faible = favorable). Avec ``RdYlGn_r``, le faible
    coût (favorable) est vert et le coût élevé rouge. Les pixels au-delà de
    ``threshold`` sont rendus dans la couleur maximale (clamp visuel, pas de
    troncature des données). Les pixels infinis (inaccessibles) sont transparents.

    Parameters
    ----------
    disp_da : xr.DataArray
        Surface de coût de dispersion (friction x mètres), sortie de
        ``compute_dispersal_surface``. Peut contenir des ``inf``.
    aoi_utm : gpd.GeoDataFrame
        Limite de la zone d'étude (même CRS que ``disp_da``).
    df_nodes : gpd.GeoDataFrame
        Patchs sources (noyaux + espaces relais) à superposer.
    threshold : float
        Plafond de l'échelle de couleur (ex. ``2 * d0 * FRICTION_AVG_FAVORABLE``
        pour la limite "improbable" CEREMA, ou ``d0 * FRICTION_AVG_FAVORABLE``
        pour étaler le contraste sur la plage favorable).
    gdf_lcp : gpd.GeoDataFrame, optional
        Corridors LCP à superposer par-dessus la carte.
    cmap_name : str, default 'RdYlGn_r'
        Colormap. ``RdYlGn_r`` : vert = faible coût (favorable), rouge = élevé.
    title : str, default "Carte de dispersion"
        Titre de la figure.

    Returns
    -------
    None
        Affiche la figure via ``plt.show()``.
    """
    fig, ax = plt.subplots(figsize=(14, 12))

    # Copie d'affichage : inf (inaccessible) -> nan (transparent), input intact
    plot_data = disp_da.where(np.isfinite(disp_da))

    norm = mcolors.Normalize(vmin=0, vmax=threshold)

    plot_data.plot(
        ax=ax,
        cmap=cmap_name,
        norm=norm,
        add_labels=False,
        zorder=1,
        cbar_kwargs={
            'label': 'Coût de dispersion (friction × m)',
            'shrink': 0.5,
            'pad': 0.02,
            'extend': 'max',
        },
    )

    # Patchs sources (au-dessus du raster)
    df_nodes.to_crs(aoi_utm.crs).plot(
        ax=ax, facecolor='#206c2c', edgecolor='black', linewidth=0.6, alpha=0.7, zorder=2,
    )
    
    # --- AJOUT DES LCP ---
    if gdf_lcp is not None and not gdf_lcp.empty:
        gdf_lcp.to_crs(aoi_utm.crs).plot(
            ax=ax, 
            color='blue',    
            linewidth=1.5, 
            alpha=0.9, 
            zorder=3            
        )
        
    # Bordure AOI
    aoi_utm.plot(ax=ax, facecolor="none", edgecolor='black', alpha=0.6, linewidth=2, zorder=4)

    plt.title(title, color='black', fontsize=18, pad=20)
    ax.set_axis_off()
    plt.tight_layout()
    plt.show()
    
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