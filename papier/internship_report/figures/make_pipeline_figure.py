"""Flowchart synoptic of the processing chain (figure of section 3.4), mermaid-like.

Top-down boxes linked by arrows, grouped into numbered method phases (left bands). Content matches the
delivered tool (WorldCover, Gabriel graph + least-cost, connectivity indicators). Outputs grouped by
theme (cores/relays, corridors/failed links/rupture points, dispersal/segments, indicators).

Run: python3 make_pipeline_figure.py
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

OUT_DIR: str = os.path.dirname(os.path.abspath(__file__))

IN_FC, IN_EC = "#F2E3C6", "#BE842A"
ST_FC, ST_EC = "#DDECEA", "#2E8B84"
OU_FC, OU_EC = "#DAE9DF", "#367752"
BAND, BAND_E = "#EFF5F3", "#C4D7D2"
GREEN_D, CREAM = "#123F3A", "#F4ECD8"
ARROW, INK = "#5E6E6B", "#1B2B28"


def box(ax, x, y, w, h, text, fc, ec, fs=9):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                                boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=ec, lw=1.3, zorder=3))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=INK, zorder=4, linespacing=1.2)
    return {"x": x, "y": y, "t": y + h / 2, "b": y - h / 2, "l": x - w / 2, "r": x + w / 2}


def arrow(ax, p, q):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=13, color=ARROW,
                                 lw=1.3, shrinkA=1, shrinkB=1, zorder=2))


def band(ax, yb, yt, num, title):
    ax.add_patch(FancyBboxPatch((0.25, yb), 11.9, yt - yb, boxstyle="round,pad=0.02,rounding_size=0.06",
                                fc=BAND, ec=BAND_E, lw=1.0, zorder=1))
    cy = (yb + yt) / 2
    if num:
        ax.add_patch(Circle((1.0, cy + 0.3), 0.33, fc=CREAM, ec=ST_EC, lw=1.2, zorder=3))
        ax.text(1.0, cy + 0.3, num, ha="center", va="center", fontsize=12, fontweight="bold", color=GREEN_D, zorder=4)
    ax.text(1.0, cy - 0.45 if num else cy, title, ha="center", va="center", fontsize=8, fontweight="bold",
            color=ST_EC, zorder=4, linespacing=1.05)


def make_pipeline() -> None:
    """Draw and save the mermaid-like grouped flowchart."""
    fig, ax = plt.subplots(figsize=(9.6, 12.2))
    ax.set_xlim(0, 12.4)
    ax.set_ylim(0, 15.2)
    ax.axis("off")

    band(ax, 13.35, 14.65, "", "Entrées")
    band(ax, 11.75, 12.95, "1", "Occupation\ndu sol")
    band(ax, 9.35, 11.15, "2", "Habitat et\nrésistance")
    band(ax, 7.15, 8.75, "3", "Graphe et\nconnectivité")
    band(ax, 5.35, 6.55, "4", "Moindre\ncoût")
    band(ax, 1.35, 4.75, "5", "Sorties")

    e1 = box(ax, 4.5, 14.0, 2.7, 0.9, "ESA WorldCover\n10 m", IN_FC, IN_EC, 8.5)
    e2 = box(ax, 7.5, 14.0, 2.7, 0.9, "OpenStreetMap\nroutes, rail, bâti, eau", IN_FC, IN_EC, 8.5)
    e3 = box(ax, 10.5, 14.0, 2.7, 0.9, "Paramètres du profil\nhabitat, d₀, frictions", IN_FC, IN_EC, 8.5)

    lc = box(ax, 7.3, 12.35, 5.0, 0.95, "Occupation du sol du profil\n(WorldCover + OSM, emprise tamponnée 2·d₀)", ST_FC, ST_EC)
    arrow(ax, (e1["x"], e1["b"]), (lc["x"] - 1.2, lc["t"]))
    arrow(ax, (e2["x"], e2["b"]), (lc["x"], lc["t"]))

    hab = box(ax, 5.6, 10.25, 4.6, 1.15, "Habitat binaire + MSPA\nnoyaux ≥ 1 ha, relais 0,1-1 ha", ST_FC, ST_EC)
    fric = box(ax, 10.1, 10.25, 2.9, 0.95, "Surface de friction", ST_FC, ST_EC)
    arrow(ax, (lc["x"] - 0.5, lc["b"]), (hab["x"], hab["t"]))
    arrow(ax, (lc["r"] - 0.3, lc["b"]), (fric["x"], fric["t"]))
    arrow(ax, (e3["x"], e3["b"]), (fric["x"], fric["t"]))

    gab = box(ax, 5.6, 7.95, 4.2, 0.95, "Graphe de Gabriel\nliens ≤ 2·d₀", ST_FC, ST_EC)
    pcth = box(ax, 8.75, 7.95, 1.5, 0.8, "PC\nthéorique", OU_FC, OU_EC, 8.5)
    arrow(ax, (hab["x"], hab["b"]), (gab["x"], gab["t"]))
    arrow(ax, (gab["r"], gab["y"]), (pcth["l"], pcth["y"]))

    lcp = box(ax, 7.3, 5.95, 4.8, 0.95, "Chemins de moindre coût\nbudget d₀ × 3", ST_FC, ST_EC)
    arrow(ax, (gab["x"], gab["b"]), (lcp["x"] - 1.3, lcp["t"]))
    arrow(ax, (fric["x"], fric["b"]), (lcp["r"] - 0.3, lcp["t"]))

    outs = [
        "Noyaux de\nbiodiversité,\néléments relais",
        "Corridors,\nliens en échec,\npoints de rupture",
        "Surface de dispersion,\nsegments\nde corridor",
        "Indicateurs : habitat\nconnecté, PC, sous-\nréseaux, tortuosité",
    ]
    ow, og, ox0 = 2.15, 0.2, 2.75
    obx = []
    for k, t in enumerate(outs):
        oxc = ox0 + ow / 2 + k * (ow + og)
        obx.append(box(ax, oxc, 2.85, ow, 2.35, t, OU_FC, OU_EC, 7.6))
    arrow(ax, (hab["l"] + 0.3, hab["b"]), (obx[0]["x"], obx[0]["t"]))  # cores/relays are outputs too
    arrow(ax, (lcp["x"] - 0.6, lcp["b"]), (obx[1]["x"], obx[1]["t"]))
    arrow(ax, (lcp["x"] + 0.2, lcp["b"]), (obx[2]["x"], obx[2]["t"]))
    arrow(ax, (lcp["x"] + 0.8, lcp["b"]), (obx[3]["x"], obx[3]["t"]))

    ax.text(7.3, 0.75, "Traitement répété pour les quatre profils écologiques.",
            ha="center", va="center", fontsize=9, style="italic", color=INK)

    out_path = os.path.join(OUT_DIR, "pipeline_chaine.png")
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("pipeline_chaine.png OK" if os.path.exists(out_path) else "MANQUANT")


if __name__ == "__main__":
    make_pipeline()
