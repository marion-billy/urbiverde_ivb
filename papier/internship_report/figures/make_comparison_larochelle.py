"""Side-by-side comparisons on La Rochelle (figures of section 5.3.2).

For a given ecological profile and commune, the left panel shows this work (bounded dispersal surface
+ least-cost corridors, satellite basemap, AOI outline) zoomed on that commune; the right panel shows
the matching Cerema Sud-Ouest sub-network map (an extracted figure). Two comparisons are produced:
- arborée/arbustive vs the forest-edge bird, on the L'Houmeau commune (Cerema fig. 30);
- herbacée vs the open-ground reptile, on the Salles-sur-Mer commune (Cerema fig. 32).

Run: python3 make_comparison_larochelle.py
"""

from __future__ import annotations

import os
import warnings

import matplotlib

matplotlib.use("Agg")
import contextily as ctx
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

import carto

warnings.filterwarnings("ignore")
os.environ.setdefault("PROJ_DATA", "/opt/conda/share/proj")

HERE: str = os.path.dirname(os.path.abspath(__file__))
OUTROOT: str = os.path.normpath(os.path.join(HERE, "..", "..", "..", "data", "outputs"))
CITY: str = "LaRochelle"
CORR: str = "#F5A623"  # corridors in amber, consistent across the report
CORE: str = "#2E7D32"  # biodiversity cores (dark green)
ISLET: str = "#A5D6A7"  # stepping-stone islets (light green)


def _scalebar(ax) -> None:
    """An adaptive scale bar (bottom-right), like the Cerema panel: a round length ~1/5 of the view."""
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    w = x1 - x0
    nice = [100, 200, 250, 500, 1000, 2000, 2500, 5000]
    L = min(nice, key=lambda v: abs(v - w * 0.2))
    bx = x1 - w * 0.06 - L
    by = y0 + (y1 - y0) * 0.09
    h = (y1 - y0) * 0.012
    ax.add_patch(Rectangle((bx, by), L / 2, h, fc="black", ec="black", lw=0.5, zorder=8))
    ax.add_patch(Rectangle((bx + L / 2, by), L / 2, h, fc="white", ec="black", lw=0.5, zorder=8))
    st = [pe.withStroke(linewidth=2.4, foreground="black")]
    lab = f"{L / 1000:g} km" if L >= 1000 else f"{L:g} m"
    ax.text(bx, by + h * 2.0, "0", ha="center", va="bottom", fontsize=7, color="white",
            zorder=8, path_effects=st)
    ax.text(bx + L, by + h * 2.0, lab, ha="center", va="bottom", fontsize=7, color="white",
            zorder=8, path_effects=st)


def _legend_box(fig, ax, imh) -> None:
    """White legend box (bottom-left): dispersal colour ramp + corridor, à la Cerema."""
    ax.add_patch(Rectangle((0.02, 0.02), 0.44, 0.34, transform=ax.transAxes,
                 fc="white", ec="#8A8A8A", lw=0.8, alpha=0.93, zorder=7))
    ax.text(0.05, 0.325, "Légende", transform=ax.transAxes, fontsize=8, fontweight="bold",
            va="top", color="#1B2B28", zorder=8)
    cax = inset_axes(ax, width="4%", height="20%", loc="lower left",
                     bbox_to_anchor=(0.06, 0.06, 1, 1), bbox_transform=ax.transAxes, borderpad=0)
    cb = fig.colorbar(imh, cax=cax, orientation="vertical")
    cb.outline.set_edgecolor("#555555")
    cb.set_ticks([0, 1])
    cb.set_ticklabels(["0", "limite"])
    cb.ax.tick_params(labelsize=6.5, length=0, colors="#1B2B28")
    ax.text(0.14, 0.255, "Coût de\ndispersion\ncumulé", transform=ax.transAxes, fontsize=6.8,
            va="top", color="#1B2B28", zorder=8, linespacing=1.25)
    ax.plot([0.27, 0.33], [0.085, 0.085], transform=ax.transAxes, color=CORR, lw=2.4, zorder=8,
            solid_capstyle="round")
    ax.text(0.35, 0.085, "Corridor", transform=ax.transAxes, fontsize=7, va="center",
            color="#1B2B28", zorder=8)


def make_one(guild: str, insee: str, cerema_png: str, left_title: str, right_title: str,
             out_name: str, zoom_pad: float = 1.12, off_x: float = 0.0, off_y: float = 0.0) -> None:
    """Draw one this-work vs Cerema comparison, zoomed on the given commune."""
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(13, 6.7))

    # Left: our bounded dispersal surface + corridors.
    with rasterio.open(f"{OUTROOT}/{CITY}/{guild}/dispersal_bounded_{guild}_{CITY}.tif") as r:
        a = r.read(1).astype("float64")
        b = r.bounds
        crs = r.crs
    a[~np.isfinite(a)] = np.nan
    mx = np.nanmax(a)
    if mx and mx > 0:
        a = a / mx
    try:  # zoom on the same commune as the Cerema map
        hz = gpd.read_file(
            f"https://geo.api.gouv.fr/communes/{insee}?format=geojson&geometry=contour"
        ).to_crs(crs).total_bounds
        cx, cy = (hz[0] + hz[2]) / 2, (hz[1] + hz[3]) / 2
        half = max(hz[2] - hz[0], hz[3] - hz[1]) / 2 * zoom_pad  # square extent, tight on the commune
        cx += off_x * half
        cy += off_y * half
        xlim, ylim = (cx - half, cx + half), (cy - half, cy + half)
    except Exception:
        xlim, ylim = (b.left, b.right), (b.bottom, b.top)
    ax0.set_xlim(*xlim)
    ax0.set_ylim(*ylim)
    ctx.add_basemap(ax0, crs=crs, source=ctx.providers.Esri.WorldImagery, attribution=False, zorder=0)
    cmap = plt.cm.RdYlGn_r.copy()
    cmap.set_bad(alpha=0)
    imh = ax0.imshow(a, origin="upper", extent=(b.left, b.right, b.bottom, b.top), cmap=cmap, vmin=0,
                     vmax=1, alpha=0.75, zorder=2)
    nodes_p = f"{OUTROOT}/{CITY}/{guild}/nodes_{guild}_{CITY}.geojson"
    if os.path.exists(nodes_p):
        nd = gpd.read_file(nodes_p)
        nd[nd.node_type == "islet"].plot(ax=ax0, facecolor=ISLET, edgecolor="white", linewidth=0.2, alpha=0.9, zorder=3)
        nd[nd.node_type == "core"].plot(ax=ax0, facecolor=CORE, edgecolor="white", linewidth=0.2, alpha=0.9, zorder=3)
    lcp = gpd.read_file(f"{OUTROOT}/{CITY}/{guild}/lcp_{guild}_{CITY}.geojson")
    if lcp is not None and len(lcp):
        lcp.plot(ax=ax0, color=CORR, linewidth=1.2, zorder=4)
    aoi = f"{OUTROOT}/{CITY}/aoi_limits_{CITY}.geojson"
    if os.path.exists(aoi):
        gpd.read_file(aoi).to_crs(crs).boundary.plot(ax=ax0, color="white", linewidth=1.3, zorder=5)
    ax0.set_xlim(*xlim)
    ax0.set_ylim(*ylim)
    ax0.set_aspect("equal")
    ax0.axis("off")
    ax0.set_title(left_title, fontsize=10.5)
    # legend: cores, islets and least-cost links (same convention as the other report figures)
    _lg = ax0.legend(handles=[Patch(facecolor=CORE, label="Noyau de biodiversité"),
                              Patch(facecolor=ISLET, label="Élément relais"),
                              Line2D([], [], color=CORR, lw=2.4, label="Lien fonctionnel")],
                     loc="lower left", fontsize=7.5, frameon=True)
    _lg.set_zorder(20)
    carto.scalebar(ax0)
    carto.north(ax0)
    carto.graticule(ax0)

    # Right: the Cerema map.
    ax1.imshow(plt.imread(os.path.join(HERE, cerema_png)))
    ax1.axis("off")
    ax1.set_title(right_title, fontsize=10.5)

    out = os.path.join(HERE, out_name)
    fig.savefig(out, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(out_name, "OK" if os.path.exists(out) else "MANQUANT")


def make_comparison() -> None:
    """Produce both La Rochelle comparisons (arborée/L'Houmeau and herbacée/Salles-sur-Mer)."""
    make_one("forest_edge_bird", "17190", "cerema_fig30_arboree.png",
             "Chaîne développée :oiseau de lisière, secteur de L'Houmeau",
             "Cerema Sud-Ouest : sous-trame arborée/arbustive",
             "comparaison_larochelle.png")
    make_one("ground_reptile", "17420", "cerema_fig32_herbacee.png",
             "Chaîne développée :reptile des milieux ouverts, secteur de Salles-sur-Mer",
             "Cerema Sud-Ouest : sous-trame herbacée",
             "comparaison_salles.png", zoom_pad=0.56, off_x=-0.22, off_y=-0.12)


if __name__ == "__main__":
    make_comparison()
