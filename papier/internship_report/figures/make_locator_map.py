"""Locator map of the six study territories over an Esri satellite basemap (figure of section 3.1).

Metropolitan France panel (La Roche-sur-Yon, Nancy, Perpignan, Toulouse, La Rochelle) plus a French
Guiana inset for Kourou, where the territory outline is drawn so its shape is recognisable. City
positions come from the produced AOI limits (``data/outputs/<City>/aoi_limits_<City>.geojson``),
reprojected to Web Mercator so the satellite tiles align. Tiles fetched at render time (internet).

Run: python3 make_locator_map.py
"""

from __future__ import annotations

import os
import warnings

import matplotlib

matplotlib.use("Agg")
import contextily as ctx
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import box

import carto

warnings.filterwarnings("ignore")
os.environ.setdefault("PROJ_DATA", "/opt/conda/share/proj")

HERE: str = os.path.dirname(os.path.abspath(__file__))
OUTROOT: str = os.path.normpath(os.path.join(HERE, "..", "..", "..", "data", "outputs"))
WEBM: str = "EPSG:3857"
MFACE: str = "white"      # marker fill: neutral, legible on the satellite basemap
MEDGE: str = "#1B2B28"    # marker edge / spines: dark ink
INK: str = "#1B2B28"
LBL_BBOX = dict(boxstyle="round,pad=0.22", fc="white", ec="none", alpha=0.82)

MAINLAND: dict[str, tuple[int, int, str]] = {
    "La Roche-sur-Yon": (10, 6, "left"),
    "La Rochelle": (-8, -14, "right"),
    "Nancy": (9, 2, "left"),
    "Toulouse": (9, 5, "left"),
    "Perpignan": (-9, -2, "right"),
}
FOLDER: dict[str, str] = {
    "LRSY": "La Roche-sur-Yon", "LaRochelle": "La Rochelle", "Nancy": "Nancy",
    "Toulouse": "Toulouse", "Perpignan": "Perpignan",
}


def _aoi(folder: str) -> gpd.GeoDataFrame:
    """Load one AOI limits layer, reprojected to Web Mercator."""
    return gpd.read_file(f"{OUTROOT}/{folder}/aoi_limits_{folder}.geojson").to_crs(WEBM)


def _pin(ax, x, y, name, dx, dy, ha) -> None:
    """A neutral white marker plus a label on a semi-transparent white box (legible on satellite)."""
    ax.plot(x, y, marker="o", markersize=9, markerfacecolor=MFACE, markeredgecolor=MEDGE,
            markeredgewidth=1.4, zorder=4)
    ax.annotate(name, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center",
                fontsize=9.5, color=INK, zorder=5, bbox=LBL_BBOX)


def make_locator() -> None:
    """Draw the France panel with a French Guiana inset (outline drawn) and save the figure."""
    fig, ax = plt.subplots(figsize=(8.2, 8.6))

    for folder, name in FOLDER.items():
        c = _aoi(folder).union_all().centroid
        dx, dy, ha = MAINLAND[name]
        _pin(ax, c.x, c.y, name, dx, dy, ha)

    fr = gpd.GeoSeries([box(-5.4, 41.2, 8.4, 51.3)], crs="EPSG:4326").to_crs(WEBM).total_bounds
    ax.set_xlim(fr[0], fr[2])
    ax.set_ylim(fr[1], fr[3])
    ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery, zoom=7, attribution=False)
    ax.set_axis_off()
    xl, yl = ax.get_xlim(), ax.get_ylim()
    ax.set_position([0, 0, 1, 1])
    fig.set_size_inches(8.6, 8.6 * (yl[1] - yl[0]) / (xl[1] - xl[0]))
    carto.north(ax)  # pas de barre d'échelle : Web Mercator distord les distances à cette latitude
    carto.graticule(ax)

    # French Guiana inset: draw the territory outline so its whole shape is visible.
    gua = gpd.read_file(os.path.join(HERE, "basemap_guyane.geojson")).to_crs(WEBM)
    gb = gua.total_bounds
    mx, my = (gb[2] - gb[0]) * 0.06, (gb[3] - gb[1]) * 0.06
    xlim, ylim = (gb[0] - mx, gb[2] + mx), (gb[1] - my, gb[3] + my)
    aspect = (ylim[1] - ylim[0]) / (xlim[1] - xlim[0])
    iw = 0.28
    axk = fig.add_axes([0.71, 0.02, iw, iw * aspect])
    axk.set_xlim(*xlim)
    axk.set_ylim(*ylim)
    axk.set_aspect("equal")
    ctx.add_basemap(axk, source=ctx.providers.Esri.WorldImagery, attribution=False)
    gua.boundary.plot(ax=axk, color="white", linewidth=1.4, zorder=2)
    kc = _aoi("Kourou").union_all().centroid
    _pin(axk, kc.x, kc.y, "Kourou", 8, 2, "left")
    axk.set_xlim(*xlim)
    axk.set_ylim(*ylim)
    axk.set_xticks([])
    axk.set_yticks([])
    for s in axk.spines.values():
        s.set_edgecolor(MEDGE)

    out = os.path.join(HERE, "localisation_territoires_osm.png")
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print("Figure generee :", out, "OK" if os.path.exists(out) else "MANQUANT")


if __name__ == "__main__":
    make_locator()
