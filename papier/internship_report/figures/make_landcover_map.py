"""Land-cover map of Toulouse for section 3.2: ESA WorldCover (official symbology) with the
OpenStreetMap infrastructure burned in (codes 51-55).

Reads the produced guild land-cover raster (same base layer for every guild; the ground_mammal
extent is the largest) and renders each class with the official WorldCover colour, plus dedicated
colours for the OSM-added codes.

Run: python3 make_landcover_map.py
"""

from __future__ import annotations

import os
import warnings

import matplotlib

matplotlib.use("Agg")
import geopandas as gpd
import numpy as np
import rasterio
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

import carto

warnings.filterwarnings("ignore")
os.environ.setdefault("PROJ_DATA", "/opt/conda/share/proj")

HERE: str = os.path.dirname(os.path.abspath(__file__))
OUTROOT: str = os.path.normpath(os.path.join(HERE, "..", "..", "..", "data", "outputs"))
RASTER: str = f"{OUTROOT}/Toulouse/ground_mammal/landcover_ground_mammal_Toulouse.tif"
STEP: int = 2  # downsample factor for the figure

# code -> (colour, label). 10-95 are the official ESA WorldCover colours; 51-55 are the OSM codes.
LC: dict[int, tuple[str, str]] = {
    10: ("#006400", "Arbres"),
    20: ("#ffbb22", "Arbustes"),
    30: ("#ffff4c", "Prairies"),
    40: ("#f096ff", "Cultures"),
    50: ("#fa0000", "Bâti (WorldCover)"),
    60: ("#b4b4b4", "Sols nus"),
    80: ("#0064c8", "Eau"),
    90: ("#0096a0", "Zones humides"),
    95: ("#00cf75", "Mangroves"),
    51: ("#404040", "Bâtiments (OSM)"),
    52: ("#000000", "Autoroutes, grands axes"),
    53: ("#808080", "Routes secondaires"),
    54: ("#c9a66b", "Chemins"),
    55: ("#7b3fa0", "Voies ferrées"),
}
MIN_PIXELS: int = 500  # a class must exceed this (after downsample) to appear in the legend


def _hex_to_rgb(h: str) -> tuple[float, float, float]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def make_landcover() -> None:
    """Render the Toulouse land-cover raster with WorldCover + OSM symbology."""
    with rasterio.open(RASTER) as src:
        arr = src.read(1)[::STEP, ::STEP]
        bnds = src.bounds
        crs = src.crs

    rgb = np.ones((*arr.shape, 3), dtype=float)  # white background for nodata / unmapped
    for code, (hexc, _) in LC.items():
        rgb[arr == code] = _hex_to_rgb(hexc)

    codes, counts = np.unique(arr, return_counts=True)
    present = {int(c): int(n) for c, n in zip(codes, counts)}

    fig, ax = plt.subplots(figsize=(7.6, 7.0))
    ax.imshow(rgb, extent=(bnds.left, bnds.right, bnds.bottom, bnds.top), origin="upper")
    aoi_p = f"{OUTROOT}/Toulouse/aoi_limits_Toulouse.geojson"
    if os.path.exists(aoi_p):
        gpd.read_file(aoi_p).to_crs(crs).boundary.plot(ax=ax, color="white", linewidth=1.6, zorder=5)
    ax.set_aspect("equal")
    ax.set_axis_off()

    handles = [Patch(facecolor=LC[c][0], edgecolor="#888888", linewidth=0.3, label=f"{c} - {LC[c][1]}")
               for c in LC if present.get(c, 0) >= MIN_PIXELS or c == 20]
    ax.legend(handles=handles, loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=8.5,
              frameon=False, title="Occupation du sol", title_fontsize=9)
    carto.scalebar(ax)
    carto.north(ax)
    carto.graticule(ax, color="#333333")

    out = os.path.join(HERE, "landcover_toulouse.png")
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("Figure generee :", out, "OK" if os.path.exists(out) else "MANQUANT")


if __name__ == "__main__":
    make_landcover()
