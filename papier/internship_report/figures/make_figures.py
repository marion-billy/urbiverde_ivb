"""Generate the schematic (data-independent) figures for the internship report.

These three figures do not depend on the pipeline outputs and can be produced at any time:
- gabriel_criterion.png : Gabriel graph edge criterion (diametral circle).
- reseau_ecologique.png : conceptual ecological network (cores, relays, corridors, rupture).
- methodes_binaire_gradient.png : binary connectivity vs gradient (least-cost) approaches.

Run: python3 make_figures.py
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, PathPatch, Rectangle
from matplotlib.path import Path

OUT_DIR: str = os.path.dirname(os.path.abspath(__file__))

CORE: str = "#2E7D32"
RELAY: str = "#81C784"
MATRIX: str = "#EEF1F0"
ROAD: str = "#9E9E9E"
WATER: str = "#4FA3D1"
RED: str = "#C62828"
CORR: str = "#F5A623"  # corridors/links in amber, consistent with the result figures

plt.rcParams.update(
    {
        "font.size": 11,
        "axes.titlesize": 12,
        "figure.dpi": 160,
        "savefig.bbox": "tight",
    }
)


def _blob(ax, xy: tuple[float, float], r: float, color: str, label: str | None = None) -> None:
    """Draw a filled habitat patch as a circle, with an optional centered label."""
    ax.add_patch(Circle(xy, r, facecolor=color, edgecolor="white", linewidth=1.5, zorder=3))
    if label:
        ax.annotate(label, xy, ha="center", va="center", color="white", fontsize=9, zorder=4)


def fig_gabriel() -> None:
    """Gabriel graph criterion: an edge exists iff no patch lies in the diametral circle."""
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.6))
    a = np.array([1.2, 2.2])
    b = np.array([4.8, 2.2])
    mid = (a + b) / 2
    radius = np.linalg.norm(b - a) / 2

    cases = [
        ("Lien valide : aucune tache dans le cercle", np.array([3.0, 4.4]), True),
        ("Lien rompu : une tache s'intercale", np.array([3.0, 2.9]), False),
    ]
    for ax, (title, c_xy, valid) in zip(axes, cases):
        ax.add_patch(Circle(mid, radius, facecolor="none", edgecolor=ROAD, linewidth=1.2, linestyle="--", zorder=2))
        if valid:
            ax.plot([a[0], b[0]], [a[1], b[1]], color=CORR, linewidth=3, zorder=2.5)
            ax.annotate("", xy=(b[0], a[1] - 0.5), xytext=(a[0], a[1] - 0.5),
                        arrowprops=dict(arrowstyle="<->", color=ROAD, lw=1.2))
            ax.annotate("diamètre ≤ 2 d₀", (mid[0], a[1] - 0.72), ha="center", va="top",
                        fontsize=8.5, color=ROAD)
        _blob(ax, a, 0.42, CORE, "A")
        _blob(ax, b, 0.42, CORE, "B")
        _blob(ax, c_xy, 0.42, RELAY, "C")
        ax.set_title(title, fontsize=11, fontweight="normal", color="#1B2B28", pad=14)
        ax.set_xlim(0, 6)
        ax.set_ylim(0, 5.2)
        ax.set_aspect("equal")
        ax.axis("off")
    fig.savefig(os.path.join(OUT_DIR, "gabriel_criterion.png"))
    plt.close(fig)


def fig_reseau() -> None:
    """Conceptual ecological network: cores, relays, corridors, a road and a rupture point."""
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    ax.add_patch(plt.Rectangle((0, 0), 10, 6, facecolor=MATRIX, edgecolor="none", zorder=0))

    # road crossing
    ax.add_patch(plt.Rectangle((0, 2.7), 10, 0.5, facecolor=ROAD, edgecolor="none", zorder=1))
    ax.annotate("Infrastructure fragmentante", (9.8, 2.95), ha="right", va="center", fontsize=8.5, color="white", zorder=2)

    cores = {"A": (1.6, 4.6), "B": (8.2, 4.4), "C": (5.0, 1.2)}
    for name, xy in cores.items():
        _blob(ax, xy, 0.7, CORE, name)
    relays = [(4.3, 4.8), (6.4, 3.9)]
    for xy in relays:
        _blob(ax, xy, 0.32, RELAY)

    # corridors (green links)
    links = [
        (cores["A"], relays[0]),
        (relays[0], relays[1]),
        (relays[1], cores["B"]),
        (cores["A"], cores["C"]),
    ]
    for p, q in links:
        ax.plot([p[0], q[0]], [p[1], q[1]], color=CORR, linewidth=2.4, zorder=2, solid_capstyle="round")

    # rupture point where a corridor crosses the road (A -> C)
    ax.plot(3.25, 2.95, marker="X", markersize=15, color=RED, zorder=5)
    ax.annotate("Point de rupture", (3.25, 2.95), xytext=(0.4, 1.6), fontsize=9, color=RED,
                arrowprops=dict(arrowstyle="-", color=RED, lw=1))

    # legend handles
    handles = [
        plt.Line2D([], [], marker="o", color="none", markerfacecolor=CORE, markeredgecolor="none", markersize=14, label="Noyau de biodiversité"),
        plt.Line2D([], [], marker="o", color="none", markerfacecolor=RELAY, markeredgecolor="none", markersize=9, label="Élément relais"),
        plt.Line2D([], [], color=CORR, lw=2.4, label="Corridor"),
        plt.Line2D([], [], marker="X", color="none", markerfacecolor=RED, markeredgecolor="none", markersize=11, label="Point de rupture"),
    ]
    ax.legend(handles=handles, loc="lower right", frameon=True, fontsize=8.5)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(os.path.join(OUT_DIR, "reseau_ecologique.png"))
    plt.close(fig)


def fig_binaire_gradient() -> None:
    """Binary connectivity (mesh) vs gradient (friction surface + least-cost path)."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8))

    # Panel A: effective mesh size, after Kirk et al. (2023, Fig. 1). Habitats are buffered then
    # fragmented by roads into connected components; connectivity is binary (same component or not),
    # and the patch areas feed the effective-mesh-size index.
    axb = axes[0]
    BLUE, GREENc, ORANGE, YELLOW = "#4F86C6", "#3DA35D", "#E08A3C", "#E6C84F"
    # roads (a cross) fragmenting the landscape into components
    axb.add_patch(Rectangle((0, 3.85), 10, 0.3, facecolor=ROAD, edgecolor="none", zorder=2))
    axb.add_patch(Rectangle((4.85, 0), 0.3, 8, facecolor=ROAD, edgecolor="none", zorder=2))
    # buffer halos that merge the two blue patches into a single connected component
    for xy, r in [((2.1, 6.0), 1.5), ((3.5, 5.05), 1.15)]:
        axb.add_patch(Circle(xy, r, facecolor="#CFE0F2", edgecolor="none", zorder=1))
    # BLUE component: two patches connected by buffering (areas 30 + 15)
    _blob(axb, (2.1, 6.0), 0.92, BLUE, "30")
    _blob(axb, (3.5, 5.05), 0.58, BLUE, "15")
    # other components, each isolated by the roads
    _blob(axb, (7.6, 6.0), 1.12, GREENc, "40")
    _blob(axb, (2.3, 1.9), 0.62, ORANGE, "10")
    _blob(axb, (7.5, 1.9), 0.45, YELLOW)
    axb.text(7.5, 1.9, "5", ha="center", va="center", color="#5A4A00", fontsize=8, zorder=4)
    axb.set_title("Approche binaire (taille de maille)", fontsize=11)
    axb.text(5.0, -0.9, "habitats tamponnés puis fragmentés par les routes en composantes connexes ;\n"
             "connecté = même composante (oui / non). Schéma d'après Kirk et al. (2023).",
             ha="center", va="top", fontsize=7.5, color="#444444")
    axb.set_xlim(0, 10)
    axb.set_ylim(-2.0, 8.2)
    axb.set_aspect("equal")
    axb.axis("off")

    # Panel B: gradient friction surface + least-cost path
    axg = axes[1]
    nx, ny = 100, 80
    yy, xx = np.mgrid[0:ny, 0:nx]
    friction = 2 + 1.5 * np.sin(xx / 14.0) + 1.5 * np.cos(yy / 12.0)
    friction += 0.6 * (xx / nx) * 3
    # a high-friction barrier band (a road) with a small gap
    friction[:, 52:56] = 9.0
    friction[34:44, 52:56] = 2.5  # gap (passage)
    im = axg.imshow(friction, origin="lower", cmap="YlOrRd", extent=(0, 10, 0, 8), aspect="auto")
    # least-cost path: from left blob, dip to the gap, then to right blob (hand drawn for illustration)
    verts = [(1.2, 5.6), (3.5, 5.2), (5.0, 4.0), (5.4, 3.9), (7.0, 3.0), (8.6, 2.6)]
    codes = [Path.MOVETO] + [Path.CURVE3, Path.CURVE3] * 2 + [Path.LINETO]
    # simpler: plot a smooth line through the gap
    px = [1.2, 3.2, 4.8, 5.4, 6.6, 8.6]
    py = [5.6, 5.0, 4.2, 3.9, 3.1, 2.6]
    axg.plot(px, py, color="#1A237E", linewidth=2.6, zorder=4)
    _blob(axg, (1.2, 5.6), 0.5, CORE)
    _blob(axg, (8.6, 2.6), 0.5, CORE)
    axg.set_title("Approche par gradient (graphe, moindre coût)", fontsize=11)
    axg.set_xlim(0, 10)
    axg.set_ylim(0, 8)
    axg.axis("off")
    cb = fig.colorbar(im, ax=axg, fraction=0.046, pad=0.04)
    cb.set_label("friction (résistance)")
    fig.savefig(os.path.join(OUT_DIR, "methodes_binaire_gradient.png"))
    plt.close(fig)


if __name__ == "__main__":
    fig_gabriel()
    fig_reseau()
    print("Figures generees dans", OUT_DIR)
    for f in ("gabriel_criterion.png", "reseau_ecologique.png"):
        p = os.path.join(OUT_DIR, f)
        print(f"  {f}: {'OK' if os.path.exists(p) else 'MANQUANT'}")
