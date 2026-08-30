"""Schematic of the normalised output tree (figure of section 3.5).

Clean file-explorer style tree: no boxes, thin elbow connectors, file names colour-coded by type
(green raster / blue vector / red csv), matching the pipeline palette.

Run: python3 make_output_tree.py
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT_DIR: str = os.path.dirname(os.path.abspath(__file__))

INK, LINE, GLOSS = "#1B2B28", "#9AA6A3", "#7A7A7A"
RAS, VEC, CSV, FOLD = "#2E7D32", "#2E6DA4", "#C62828", "#1B2B28"

# (depth, label, colour, bold, gloss)
NODES = [
    (0, "outputs/", FOLD, True, ""),
    (1, "<Ville>/", FOLD, True, ""),
    (2, "aoi_limits_<Ville>.geojson", GLOSS, False, ""),
    (2, "<profil écologique>/", FOLD, True, ""),
    (3, "landcover.tif", RAS, False, ""),
    (3, "binary_habitat.tif", RAS, False, ""),
    (3, "friction.tif", RAS, False, ""),
    (3, "dispersal.tif", RAS, False, ""),
    (3, "dispersal_bounded.tif", RAS, False, ""),
    (3, "nodes.geojson", VEC, False, ""),
    (3, "edges.geojson", VEC, False, ""),
    (3, "lcp.geojson", VEC, False, ""),
    (3, "failed_links.geojson", VEC, False, ""),
    (3, "rupture_points.geojson", VEC, False, ""),
    (3, "isolated_nodes.geojson", VEC, False, ""),
    (3, "corridor_segments.geojson", VEC, False, ""),
    (3, "stats.csv", CSV, False, ""),
]

X = [0.5, 1.5, 2.55, 3.75]   # x-start per depth
DY = 1.0
GLOSS_X = 8.2


def make_tree() -> None:
    """Draw and save the connector-tree schematic (no boxes)."""
    n = len(NODES)
    ys = [n - i for i in range(n)]  # top-down
    fig, ax = plt.subplots(figsize=(9.6, 0.62 * n))
    ax.set_xlim(0, 10.6)
    ax.set_ylim(0, n + 1)
    ax.axis("off")

    # connectors: link each node to its parent (last previous node of depth-1)
    for i, (d, *_ ) in enumerate(NODES):
        if d == 0:
            continue
        parent = next(j for j in range(i - 1, -1, -1) if NODES[j][0] == d - 1)
        tx = X[d - 1] + 0.12          # vertical trunk x (under the parent)
        ax.plot([tx, tx], [ys[parent] - 0.28, ys[i]], color=LINE, lw=1.1, zorder=1)
        ax.plot([tx, X[d] - 0.1], [ys[i], ys[i]], color=LINE, lw=1.1, zorder=1)

    for i, (d, label, color, bold, gloss) in enumerate(NODES):
        ax.text(X[d], ys[i], label, ha="left", va="center", fontsize=11.5 if bold else 10.3,
                fontweight="bold" if bold else "normal", color=color, zorder=3)
        if gloss:
            ax.text(GLOSS_X, ys[i], gloss, ha="left", va="center", fontsize=8.2,
                    style="italic", color=GLOSS, zorder=3)

    ax.text(0.5, 0.35, "Nommage : <artefact>_<profil écologique>_<Ville>.<extension>",
            ha="left", va="center", fontsize=8.6, style="italic", color=INK)

    out = os.path.join(OUT_DIR, "arborescence_sorties.png")
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("arborescence_sorties.png OK" if os.path.exists(out) else "MANQUANT")


if __name__ == "__main__":
    make_tree()
