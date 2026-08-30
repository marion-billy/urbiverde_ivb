"""Cartographic furniture for the report maps: a metric scale bar and a north arrow drawn in the
current axes. Manual (no matplotlib_scalebar dependency). Call AFTER the final set_xlim/set_ylim
(and after contextily add_basemap, which can reset the limits).

For a non-metric axis (lat/lon locator, or Web Mercator whose distances are latitude-distorted) use
north() only: a metric scale bar there would be misleading.
"""
from __future__ import annotations

import math

import matplotlib.patheffects as pe
from matplotlib.patches import Polygon


def north(ax, loc=(0.865, 0.80, 0.11, 0.17)) -> None:
    """QGIS-style north arrow: a two-tone dart pointing up (left half hollow, right half filled) with
    an 'N' below. Drawn in a corner inset so the shape is preserved whatever the map's aspect ratio;
    white halo for legibility on a satellite basemap. `loc` = (x0, y0, w, h) in axes fraction."""
    axn = ax.inset_axes(loc, zorder=13)
    axn.set_xlim(0, 1)
    axn.set_ylim(0, 1)
    axn.set_aspect("equal")
    axn.axis("off")
    axn.patch.set_alpha(0)
    halo = [pe.withStroke(linewidth=2.6, foreground="white")]
    apex, notch = (0.5, 0.97), (0.5, 0.44)
    axn.add_patch(Polygon([apex, (0.19, 0.22), notch], closed=True, facecolor="white",
                          edgecolor="black", lw=1.2, joinstyle="miter", path_effects=halo, zorder=13))
    axn.add_patch(Polygon([apex, (0.81, 0.22), notch], closed=True, facecolor="black",
                          edgecolor="black", lw=1.2, joinstyle="miter", path_effects=halo, zorder=13))
    axn.text(0.5, 0.15, "N", ha="center", va="top", fontsize=12, fontweight="bold",
             color="black", path_effects=halo, zorder=13)


def graticule(ax, n: int = 4, color: str = "white", alpha: float = 0.35) -> None:
    """Overlay a light semi-transparent coordinate grid (graticule) at nice round intervals.

    Works with axis('off') maps (draws artist lines, independent of ticks/frame). White + dotted so
    it reads over a satellite basemap without dominating it.
    """
    (x0, x1), (y0, y1) = ax.get_xlim(), ax.get_ylim()
    span = abs(x1 - x0)
    if span <= 0:
        return
    raw = span / n
    p = 10 ** math.floor(math.log10(raw))
    f = raw / p
    step = (1 if f < 1.5 else 2 if f < 3.5 else 5) * p
    lo, hi = min(x0, x1), max(x0, x1)
    x = math.ceil(lo / step) * step
    while x < hi:
        ax.axvline(x, color=color, lw=0.5, ls=(0, (1, 3)), alpha=alpha, zorder=8)
        x += step
    lo, hi = min(y0, y1), max(y0, y1)
    y = math.ceil(lo / step) * step
    while y < hi:
        ax.axhline(y, color=color, lw=0.5, ls=(0, (1, 3)), alpha=alpha, zorder=8)
        y += step


def scalebar(ax) -> None:
    """Draw a metric scale bar (nice round length ~1/4 of the x-extent) at the lower left.

    Assumes the axis x-units are metres (projected CRS such as UTM). White halo so it reads over a
    dark satellite basemap.
    """
    from matplotlib.patches import Rectangle
    (x0, x1), (y0, y1) = ax.get_xlim(), ax.get_ylim()
    span = abs(x1 - x0)
    yspan = abs(y1 - y0)
    if span <= 0:
        return
    raw = span / 4.0
    p = 10 ** math.floor(math.log10(raw))
    f = raw / p
    L = (1 if f < 1.5 else 2 if f < 3.5 else 5) * p
    segments = 4
    seg = L / segments
    xb = min(x0, x1) + span * 0.05
    yb = min(y0, y1) + yspan * 0.075
    h = yspan * 0.013
    unit = "km" if L >= 1000 else "m"
    div = 1000.0 if L >= 1000 else 1.0
    pad = span * 0.012
    # panneau blanc de fond (lisibilité sur satellite)
    ax.add_patch(Rectangle((xb - pad, yb - h * 1.1), L + 2 * pad, h * 4.6, facecolor="white",
                           edgecolor="none", alpha=0.72, zorder=9))
    # segments alternés noir / blanc, style QGIS
    for i in range(segments):
        ax.add_patch(Rectangle((xb + i * seg, yb), seg, h,
                               facecolor=("black" if i % 2 == 0 else "white"),
                               edgecolor="black", lw=0.7, zorder=11))
    # étiquettes : 0, moitié, longueur totale + unité
    for frac in (0.0, 0.5, 1.0):
        val = L * frac / div
        txt = f"{val:g} {unit}" if frac == 1.0 else f"{val:g}"
        ax.text(xb + L * frac, yb + h * 1.6, txt, ha="center", va="bottom", fontsize=7,
                fontweight="bold", color="black", zorder=12)
