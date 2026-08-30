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

def plot_resistance_surface(resistance_raster: xr.DataArray, aoi_utm: gpd.GeoDataFrame) -> None:
    """
    Plot the resistance (friction) surface with the AOI outline.

    Parameters
    ----------
    resistance_raster : xr.DataArray
        Cost surface (may contain ``inf``, replaced by a high finite value for display).
    aoi_utm : gpd.GeoDataFrame
        Study-area boundary.

    Returns
    -------
    None
        Displays the figure via ``plt.show()``.
    """
    fig, ax = plt.subplots(figsize=(14, 12))
    
    # Prepare a display copy (replace inf by a high but finite value for the plot)
    plot_data = resistance_raster.where(resistance_raster != np.inf, resistance_raster.max() * 1.2)
    
    im = plot_data.plot(
        ax=ax,
        robust=True, 
        cmap='RdYlGn_r', 
        add_labels=False,
        cbar_kwargs={'label': 'Movement cost (friction)'}
    )

    aoi_utm.plot(ax=ax, facecolor="none", edgecolor='black', alpha=0.6, linewidth=2)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Resistance surface (friction cost)", fontsize=12)
    ax.set_axis_off()
    plt.tight_layout()
    plt.show()

def plot_connectivity_ruptures(
    gdf_lcp: gpd.GeoDataFrame,
    aoi_utm: gpd.GeoDataFrame,
    df_nodes: gpd.GeoDataFrame,
) -> None:
    """
    Plot rupture zones (failed corridors) and isolated habitats.

    The success graph is rebuilt dynamically from the GeoDataFrame.

    Parameters
    ----------
    gdf_lcp : gpd.GeoDataFrame
        LCP corridors with a 'status' column ('success' / 'failed').
    aoi_utm : gpd.GeoDataFrame
        Study-area boundary.
    df_nodes : gpd.GeoDataFrame
        Habitat nodes.

    Returns
    -------
    None
        Displays the figure via ``plt.show()``.
    """
    # 1. Identify the removed corridors
    gdf_success = gdf_lcp[gdf_lcp['status'] == 'success']
    gdf_failed = gdf_lcp[gdf_lcp['status'] == 'failed']
    
    # 2. Identify isolated nodes
    G_success = nx.from_pandas_edgelist(gdf_success, 'node_1', 'node_2')
    G_success.add_nodes_from(df_nodes.index) # Garantit que tous les habitats sont inclus
    isolated_nodes_list = list(nx.isolates(G_success))
    all_isolated_nodes = df_nodes[df_nodes.index.isin(isolated_nodes_list)]
    isolated_nodes_gdf = all_isolated_nodes[all_isolated_nodes.geometry.intersects(aoi_utm.unary_union)]
    
    # 3. Build the map
    fig, ax = plt.subplots(figsize=(14, 12))
    aoi_utm.plot(ax=ax, color='#f8f9fa', edgecolor='#ced4da')
    
    # Functional corridors (success)
    if not gdf_success.empty:
        gdf_success.plot(ax=ax, color='#adb5bd', alpha=0.6, linewidth=1.4)
    # Rupture zones (failures)
    if not gdf_failed.empty:
        gdf_failed.plot(ax=ax, color='#ff0055', alpha=0.6, linewidth=1.8, linestyle='--')
    
    # All habitats (nodes)
    df_nodes.plot(ax=ax, color='#206c2c', markersize=10, alpha=0.6)
    # Outline of isolated habitats
    if not isolated_nodes_gdf.empty:
        isolated_nodes_gdf.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1.5, markersize=100)

    # 4. Legend
    handles = [
        mlines.Line2D([], [], color='#adb5bd', linewidth=2, label=f'Functional corridors ({len(gdf_success)})'),
        mlines.Line2D([], [], color='#ff0055', linewidth=2, linestyle='--', label=f'Rupture zones ({len(gdf_failed)})'),
        mlines.Line2D([], [], color='#206c2c', marker='o', linestyle='None', label=f'Habitat Patches ({len(df_nodes)})'),
        mlines.Line2D([], [], marker='o', markerfacecolor='none', markeredgecolor='black', linestyle='None', label=f'Isolated habitats ({len(isolated_nodes_gdf)})')
    ]

    aoi_utm.plot(ax=ax, facecolor="none", edgecolor='black', alpha=0.6, linewidth=2)
    plt.title("Diagnostic: rupture zones and isolated habitats", fontsize=16, color='black', pad=20)
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

    # Nodes (habitats)
    df_nodes.plot(ax=ax, color='#206c2c', alpha=0.6, zorder=1)

    handles = [mlines.Line2D([], [], color=c, linewidth=2.5, label=f"{l}") 
               for l, (c, w, z) in style_map.items()]
    handles.append(mpatches.Patch(color='#206c2c', label='Habitats'))

    aoi_utm.plot(ax=ax, facecolor="none", edgecolor='black', alpha=0.6, linewidth=2, zorder=6)
    plt.legend(handles=handles, loc='upper right', fontsize=12, frameon=True)
    plt.title(f"Connectivity diagnostic: corridor hierarchy", fontsize=16, color='black', pad=20)
    ax.set_axis_off()
    plt.tight_layout()
    plt.show()
    
def plot_segment_metric(gdf_lcp: gpd.GeoDataFrame, df_nodes: gpd.GeoDataFrame, aoi_utm: gpd.GeoDataFrame, 
                        score_col='corridor_count', 
                        cmap_name='plasma', 
                        title="", 
                        cbar_label=""):
    """
    Generate a dynamic vector heatmap for any metric.
    Line width and color adapt automatically to the maximum of the chosen column.
    """
    fig, ax = plt.subplots(figsize=(14, 12))
    aoi_utm.plot(ax=ax, color='#f8f9fa', edgecolor='#ced4da', zorder=1)

    # Habitat reservoirs 
    df_nodes.plot(ax=ax, color='#206c2c', alpha=0.6, zorder=2)

    # Prepare the data
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

    # Colorbar
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
    title: str = "Dispersion map",
) -> None:
    """
    Plot the dispersion map (continuous cost surface) with a capped color scale.

    Raw cost is preserved (low = favorable). With ``RdYlGn_r``, low cost (favorable)
    is green and high cost is red. Pixels above ``threshold`` are rendered in the
    maximum color (visual clamp, no data truncation). Infinite (unreachable) pixels
    are transparent.

    Parameters
    ----------
    disp_da : xr.DataArray
        Dispersion cost surface (friction x metres), output of
        ``compute_dispersal_surface``. May contain ``inf``.
    aoi_utm : gpd.GeoDataFrame
        Study-area boundary (same CRS as ``disp_da``).
    df_nodes : gpd.GeoDataFrame
        Source patches (cores + stepping stones) to overlay.
    threshold : float
        Color-scale cap (e.g. ``2 * d0 * FRICTION_AVG_FAVORABLE`` for the CEREMA
        "unlikely" limit, or ``d0 * FRICTION_AVG_FAVORABLE`` to spread contrast over
        the favorable range).
    gdf_lcp : gpd.GeoDataFrame, optional
        LCP corridors to overlay on top of the map.
    cmap_name : str, default 'RdYlGn_r'
        Colormap. ``RdYlGn_r``: green = low cost (favorable), red = high.
    title : str, default "Dispersion map"
        Figure title.

    Returns
    -------
    None
        Displays the figure via ``plt.show()``.
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
            'label': 'Dispersion cost (friction x m)',
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
    
