"""Generate result figures from the re-run outputs (data-dependent).

- mspa_example.png        (§3.4): cores vs stepping stones on a city sector.
- sorties_perpignan.png   (§4.1): full network (cores + corridors + failed_links) on a city.
- dispersion_comparee.png (§4.2): bounded dispersal surface, generalist vs reptile.

Run: python3 make_result_figures.py
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
import pandas as pd
import rasterio
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

import carto

warnings.filterwarnings("ignore")
os.environ.setdefault("PROJ_DATA", "/opt/conda/share/proj")

HERE = os.path.dirname(os.path.abspath(__file__))
OUTROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", "data", "outputs"))

CORE = "#2E7D32"
ISLET = "#A5D6A7"
CORR = "#F5A623"  # corridors in amber: visible over the satellite basemap
RED = "#C62828"
GREY = "#9E9E9E"


def layer(city: str, guild: str, name: str):
    p = f"{OUTROOT}/{city}/{guild}/{name}_{guild}_{city}.geojson"
    return gpd.read_file(p) if os.path.exists(p) else None


def aoi_boundary(ax, city: str, crs) -> None:
    """Draw the study-area (AOI) limit over the current axes, in the given CRS."""
    p = f"{OUTROOT}/{city}/aoi_limits_{city}.geojson"
    if os.path.exists(p):
        gpd.read_file(p).to_crs(crs).boundary.plot(ax=ax, color="white", linewidth=1.4, zorder=6)


def fig_mspa(city="Perpignan", guild="ground_mammal") -> None:
    nodes = layer(city, guild, "nodes")
    cores = nodes[nodes.node_type == "core"]
    islets = nodes[nodes.node_type == "islet"]
    minx, miny, maxx, maxy = nodes.total_bounds
    cx, cy = (minx + maxx) / 2 + 350, (miny + maxy) / 2 - 50  # shift SE, off the Têt banks and the low-res patch
    half = 620  # 1.24 km window (tighter, sharper satellite tiles)
    fig, ax = plt.subplots(figsize=(6.2, 6.2))
    ax.set_xlim(cx - half, cx + half)
    ax.set_ylim(cy - half, cy + half)
    ax.set_aspect("equal")
    ax.axis("off")
    ctx.add_basemap(ax, crs=cores.crs, source=ctx.providers.Esri.WorldImagery, attribution=False)
    islets.plot(ax=ax, facecolor=ISLET, edgecolor="none", alpha=0.85, zorder=3)
    cores.plot(ax=ax, facecolor=CORE, edgecolor="none", alpha=0.85, zorder=3)
    ax.set_xlim(cx - half, cx + half)
    ax.set_ylim(cy - half, cy + half)
    ax.legend(handles=[Patch(facecolor=CORE, label="Noyau de biodiversité"),
                       Patch(facecolor=ISLET, label="Élément relais")],
              loc="lower right", fontsize=8, frameon=True)
    carto.scalebar(ax)
    carto.north(ax)
    carto.graticule(ax)
    fig.savefig(os.path.join(HERE, "mspa_example.png"), dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("mspa_example.png OK")


def _network_panel(ax, city: str, guild: str, title: str, extent) -> None:
    """Draw one profile's full network (cores, islets, corridors, failed links) on a shared extent."""
    nodes = layer(city, guild, "nodes")
    lcp = layer(city, guild, "lcp")
    failed_links = layer(city, guild, "failed_links")
    crs = nodes.crs
    ax.set_xlim(extent[0], extent[2])
    ax.set_ylim(extent[1], extent[3])
    ctx.add_basemap(ax, crs=crs, source=ctx.providers.Esri.WorldImagery, attribution=False, zorder=0)
    nodes[nodes.node_type == "islet"].plot(ax=ax, facecolor=ISLET, edgecolor="none", zorder=3)
    nodes[nodes.node_type == "core"].plot(ax=ax, facecolor=CORE, edgecolor="none", zorder=3)
    if lcp is not None and len(lcp):
        lcp.plot(ax=ax, color=CORR, linewidth=0.9, alpha=0.85, zorder=4)
    if failed_links is not None and len(failed_links):
        failed_links.plot(ax=ax, color=RED, linewidth=1.8, zorder=5)
    aoi_boundary(ax, city, crs)
    ax.set_xlim(extent[0], extent[2])
    ax.set_ylim(extent[1], extent[3])
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=11)
    carto.scalebar(ax)
    carto.north(ax)
    carto.graticule(ax)


def fig_sorties(city="Perpignan") -> None:
    """Two contrasted profiles side by side on the same city and extent: the connected network of the
    ground mammal vs the fragmented network of the reptile."""
    ref = layer(city, "ground_mammal", "nodes")
    extent = gpd.read_file(f"{OUTROOT}/{city}/aoi_limits_{city}.geojson").to_crs(ref.crs).total_bounds
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(13, 6.8))
    _network_panel(axL, city, "ground_mammal", "Petit mammifère terrestre (réseau connexe)", extent)
    _network_panel(axR, city, "ground_reptile", "Reptile terrestre (réseau morcelé)", extent)
    handles = [Patch(facecolor=CORE, label="Noyau de biodiversité"),
               Patch(facecolor=ISLET, label="Élément relais"),
               Line2D([], [], color=CORR, lw=1.5, label="Lien fonctionnel"),
               Line2D([], [], color=RED, lw=2, label="Lien en échec")]
    axR.legend(handles=handles, loc="lower right", fontsize=8, frameon=True)
    fig.savefig(os.path.join(HERE, "sorties_perpignan.png"), dpi=160, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print("sorties_perpignan.png OK (2 panneaux)")


def _disp(ax, city, guild, title):
    p = f"{OUTROOT}/{city}/{guild}/dispersal_bounded_{guild}_{city}.tif"
    with rasterio.open(p) as r:
        a = r.read(1).astype("float64")
        b = r.bounds
        crs = r.crs
    a[~np.isfinite(a)] = np.nan
    mx = np.nanmax(a)
    if mx and mx > 0:
        a = a / mx  # fraction of the guild's own dispersal budget (0 = core, 1 = reach limit)
    ax.set_xlim(b.left, b.right)
    ax.set_ylim(b.bottom, b.top)
    ctx.add_basemap(ax, crs=crs, source=ctx.providers.Esri.WorldImagery, attribution=False, zorder=0)
    cmap = plt.cm.RdYlGn_r.copy()  # vert = atteint facilement, rouge = limite de portée
    cmap.set_bad(alpha=0)  # no-data transparent, so the satellite basemap shows through
    im = ax.imshow(a, origin="upper", extent=(b.left, b.right, b.bottom, b.top),
                   cmap=cmap, vmin=0, vmax=1, alpha=0.75, zorder=2)
    ax.set_xlim(b.left, b.right)
    ax.set_ylim(b.bottom, b.top)
    aoi_boundary(ax, city, crs)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=10)
    carto.scalebar(ax)
    carto.north(ax)
    carto.graticule(ax)
    return im


def fig_dispersion(city="Perpignan") -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.4))
    _disp(axes[0], city, "ground_mammal", "Mammifère terrestre (le mieux connecté)")
    im = _disp(axes[1], city, "ground_reptile", "Reptile terrestre (le plus fragmenté)")
    cb = fig.colorbar(im, ax=axes, fraction=0.025, pad=0.02)
    cb.set_label("Part du budget de dispersion atteinte\n(0 = noyau, 1 = limite de portée)", fontsize=9)
    fig.savefig(os.path.join(HERE, "dispersion_comparee.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("dispersion_comparee.png OK")


CITY_LABEL = {"LaRochelle": "La Rochelle", "LRSY": "La Roche-sur-Yon"}


def fig_territoires(guild="ground_mammal", cities=("Perpignan", "Nancy", "LaRochelle")) -> None:
    # Same square window for every panel: the territories are shown at the same size and scale,
    # so only the habitat structure (cores + relays) is compared. No corridors, no failed links, no KPI.
    data = {}
    for city in cities:
        nodes = layer(city, guild, "nodes")
        b = gpd.read_file(f"{OUTROOT}/{city}/aoi_limits_{city}.geojson").to_crs(nodes.crs).total_bounds
        data[city] = (nodes, (b[0] + b[2]) / 2, (b[1] + b[3]) / 2, max(b[2] - b[0], b[3] - b[1]))
    half = max(v[3] for v in data.values()) / 2 * 1.06
    fig, axes = plt.subplots(1, len(cities), figsize=(5.0 * len(cities), 5.4))
    for ax, city in zip(axes, cities):
        nodes, cx, cy, _ = data[city]
        ax.set_xlim(cx - half, cx + half)  # fix the common window BEFORE fetching the basemap
        ax.set_ylim(cy - half, cy + half)
        ctx.add_basemap(ax, crs=nodes.crs, source=ctx.providers.Esri.WorldImagery, attribution=False, zorder=0)
        nodes[nodes.node_type == "islet"].plot(ax=ax, facecolor=ISLET, edgecolor="none")
        nodes[nodes.node_type == "core"].plot(ax=ax, facecolor=CORE, edgecolor="none")
        aoi_boundary(ax, city, nodes.crs)
        ax.set_xlim(cx - half, cx + half)
        ax.set_ylim(cy - half, cy + half)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(CITY_LABEL.get(city, city), fontsize=11)
        carto.scalebar(ax)
        carto.north(ax)
        carto.graticule(ax)
    axes[-1].legend(handles=[Patch(facecolor=CORE, label="Noyau de biodiversité"),
                             Patch(facecolor=ISLET, label="Élément relais")],
                    loc="lower right", fontsize=8, frameon=True)
    fig.savefig(os.path.join(HERE, "territoires_comparees.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("territoires_comparees.png OK")


def fig_localisation() -> None:
    biome = {"Perpignan": "méditerranéen", "Nancy": "continental", "LRSY": "atlantique",
             "LaRochelle": "atlantique (réf. Cerema)", "Toulouse": "contrôle visuel",
             "Kourou": "équatorial"}
    cent = {}
    for c in biome:
        a = gpd.read_file(f"{OUTROOT}/{c}/aoi_limits_{c}.geojson")
        g = a.geometry.union_all().centroid
        cent[c] = (g.x, g.y)
    frp = os.path.join(HERE, "basemap_france.geojson")
    gup = os.path.join(HERE, "basemap_guyane.geojson")
    fr = gpd.read_file(frp) if os.path.exists(frp) else None
    gu = gpd.read_file(gup) if os.path.exists(gup) else None
    fig, (axm, axg) = plt.subplots(1, 2, figsize=(11, 5.6), gridspec_kw={"width_ratios": [2.1, 1]})
    if fr is not None:
        fr.plot(ax=axm, facecolor="#EAF1E7", edgecolor="#9DB8A4", linewidth=0.7, zorder=0)
    off = {"LRSY": (0.25, 0.4), "LaRochelle": (0.25, -0.6)}  # avoid overlap of the two Atlantic sites
    for c in ["Perpignan", "Nancy", "LRSY", "LaRochelle", "Toulouse"]:
        x, y = cent[c]
        axm.plot(x, y, "o", color=CORE, markersize=10, zorder=3)
        dx, dy = off.get(c, (0.15, 0.15))
        axm.annotate(f"{CITY_LABEL.get(c, c)}\n({biome[c]})", (x, y), xytext=(x + dx, y + dy), fontsize=9)
    if fr is not None:
        b = fr.total_bounds
        axm.set_xlim(b[0] - 0.5, b[2] + 0.5)
        axm.set_ylim(b[1] - 0.5, b[3] + 0.5)
    else:
        axm.set_xlim(-5.5, 9.5)
        axm.set_ylim(41, 51.5)
    axm.set_title("France métropolitaine")
    axm.set_xlabel("longitude (°)")
    axm.set_ylabel("latitude (°)")
    axm.grid(True, linestyle=":", alpha=0.5)
    axm.set_aspect("equal", adjustable="box")
    if gu is not None:
        gu.plot(ax=axg, facecolor="#EAF1E7", edgecolor="#9DB8A4", linewidth=0.7, zorder=0)
    x, y = cent["Kourou"]
    axg.plot(x, y, "o", color=CORE, markersize=10, zorder=3)
    axg.annotate(f"Kourou\n({biome['Kourou']})", (x, y), xytext=(x + 0.1, y + 0.1), fontsize=9)
    if gu is not None:
        b = gu.total_bounds
        axg.set_xlim(b[0] - 0.3, b[2] + 0.3)
        axg.set_ylim(b[1] - 0.3, b[3] + 0.3)
    else:
        axg.set_xlim(-54.8, -51.5)
        axg.set_ylim(2, 6)
    axg.set_title("Guyane")
    axg.set_xlabel("longitude (°)")
    axg.grid(True, linestyle=":", alpha=0.5)
    axg.set_aspect("equal", adjustable="box")
    fig.suptitle("Localisation des territoires d'étude et leurs contextes bioclimatiques", fontsize=12)
    fig.savefig(os.path.join(HERE, "localisation_territoires.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("localisation_territoires.png OK")


def fig_scenario_local(city="Toulouse", guild="ground_mammal",
                       scen_name="vegetalisation-allees-jj-ramblas-2") -> None:
    """Local effect of one vegetalization project, from the scenario outputs (project.geojson footprint).

    The project footprint is read directly from ``project.geojson`` (the authoritative emprise), not from a
    landcover diff. Vegetalizing it turns the area into a new biodiversity core, which the least-cost step
    then plugs into the network through several corridors (7 here, versus 1 reaching the site before).
    """
    scen_dir = os.path.normpath(os.path.join(OUTROOT, "..", "scenarios", city, scen_name))
    base = f"{OUTROOT}/{city}/{guild}"
    ns = gpd.read_file(f"{scen_dir}/{guild}/nodes_{guild}_{city}.geojson")
    nb = gpd.read_file(f"{base}/nodes_{guild}_{city}.geojson")
    proj = gpd.read_file(f"{scen_dir}/project.geojson").to_crs(ns.crs)
    lcp_s = gpd.read_file(f"{scen_dir}/{guild}/lcp_{guild}_{city}.geojson").to_crs(ns.crs)
    lcp_b = gpd.read_file(f"{base}/lcp_{guild}_{city}.geojson").to_crs(ns.crs)
    proj_geom = proj.union_all()

    bc = np.array([(g.x, g.y) for g in nb.geometry.centroid])
    is_new = ns.geometry.apply(
        lambda g: float(np.hypot(bc[:, 0] - g.centroid.x, bc[:, 1] - g.centroid.y).min()) > 20.0
    )
    created = ns[is_new]  # the node(s) the project adds: here one new core over the footprint
    conn = lcp_s[lcp_s.intersects(created.union_all().buffer(15))] if len(created) else lcp_s.iloc[:0]

    # a single square window, shared by both panels: footprint + the corridors the project unlocks
    focus = gpd.GeoSeries(list(conn.geometry) + [proj_geom], crs=ns.crs).total_bounds
    cx, cy = (focus[0] + focus[2]) / 2, (focus[1] + focus[3]) / 2
    half = max((focus[2] - focus[0]) / 2, (focus[3] - focus[1]) / 2) * 0.95
    half = max(half, 330.0)
    win = (cx - half, cx + half, cy - half, cy + half)

    handles = [Patch(facecolor=CORE, label="Noyau de biodiversité"),
               Patch(facecolor=ISLET, label="Élément relais"),
               Line2D([], [], color=CORR, lw=2.0, label="Lien fonctionnel"),
               Line2D([], [], color="#1B5E20", lw=1.8, linestyle=(0, (4, 2)),
                      label="Emprise du projet")]
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 6.7), constrained_layout=True)
    for ax, (nodes, lcp, title, add_core) in zip(
        axes, [(nb, lcp_b, "Avant le projet", False), (ns, lcp_s, "Après le projet", True)]
    ):
        lcp.cx[win[0]:win[1], win[2]:win[3]].plot(ax=ax, color=CORR, linewidth=1.1, zorder=2)
        sub = nodes.cx[win[0]:win[1], win[2]:win[3]]
        if add_core:
            sub = sub[~sub.index.isin(created.index)]
        sub[sub.node_type == "islet"].plot(ax=ax, facecolor=ISLET, edgecolor="white", linewidth=0.3, zorder=3)
        sub[sub.node_type == "core"].plot(ax=ax, facecolor=CORE, edgecolor="white", linewidth=0.3, zorder=3)
        if add_core:
            created.plot(ax=ax, facecolor=CORE, edgecolor="white", linewidth=0.4, zorder=4)
        proj.boundary.plot(ax=ax, color="#1B5E20", linewidth=1.8, linestyle=(0, (4, 2)), zorder=5)
        ax.set_xlim(win[0], win[1])
        ax.set_ylim(win[2], win[3])
        ctx.add_basemap(ax, crs=ns.crs, source=ctx.providers.Esri.WorldImagery, attribution=False, zorder=0)
        ax.set_xlim(win[0], win[1])
        ax.set_ylim(win[2], win[3])
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(title, fontsize=11)
        ax.legend(handles=handles, loc="lower right", fontsize=8, frameon=True)
        carto.scalebar(ax)
        carto.north(ax)
        carto.graticule(ax)

    fig.suptitle("Scénario de végétalisation (Toulouse) : effet local sur le réseau", fontsize=12.5)
    fig.savefig(os.path.join(HERE, "scenario_local.png"), dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("scenario_local.png OK")


if __name__ == "__main__":
    fig_mspa()
    fig_sorties()
    fig_dispersion()
    fig_territoires()
    fig_localisation()
    fig_scenario_local()
    print("Figures résultats générées dans", HERE)
