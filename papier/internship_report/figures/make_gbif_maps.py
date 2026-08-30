"""Regenerate the GBIF occurrence maps of section 3.5 / annexe C, WITH the report's cartographic
conventions (satellite basemap, scale bar, north arrow, graticule, legend).

Why this file exists: the primitives live in ``utils/gbif_validation.py`` but nothing called them
(the original panels were made interactively and lost). This driver reuses the pure-geopandas
primitives (filter/thin) and fetches occurrences via the stdlib ``urllib`` (avoids the ~/.local
urllib3-future shadow that breaks ``requests`` in the normal env, which contextily needs).

Outputs (one panel per metropolitan territory):
  gbif_cartes_ground_mammal.png, gbif_cartes_arboreal_mammal.png,
  gbif_cartes_forest_edge_bird.png, gbif_cartes_ground_reptile.png,
  gbif_carte_Toulouse_fauvette.png  (Fig 14, single panel).

Run: python3 make_gbif_maps.py
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import matplotlib

matplotlib.use("Agg")
import contextily as ctx
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

import carto

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..", "..", "utils")))
from gbif_validation import filter_occurrences, spatial_thin, to_gdf  # noqa: E402
from species_params import SPECIES_CONFIG  # noqa: E402

OUTROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", "data", "outputs"))
GBIF = "https://api.gbif.org/v1"
WGS84 = "EPSG:4326"

CITIES = ["Perpignan", "Toulouse", "Nancy", "LRSY", "LaRochelle"]
CITY_LABEL = {"LRSY": "La Roche-sur-Yon", "LaRochelle": "La Rochelle"}
GUILD_FR = {"ground_mammal": "petit mammifère terrestre (hérisson)",
            "arboreal_mammal": "mammifère arboricole (écureuil)",
            "forest_edge_bird": "oiseau de lisière (fauvette)",
            "ground_reptile": "reptile terrestre (lézard)"}
CORE, ISLET, CORR, OCC = "#2E7D32", "#A5D6A7", "#F5A623", "#7E57C2"
_KEYCACHE: dict[str, int] = {}


_UA = {"User-Agent": "murmuration-corridor-report/1.0 (research@murmuration-sas.com)"}


def _get(path: str, params: dict, tries: int = 8) -> dict:
    """GET a GBIF endpoint via stdlib urllib, polite (User-Agent) with long backoff on 429/503."""
    url = f"{GBIF}/{path}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=_UA)
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 503, 502):
                time.sleep(min(45, 3 * 2 ** attempt))  # 3,6,12,24,45,45,45 s
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            time.sleep(min(45, 3 * 2 ** attempt))
    raise RuntimeError(f"GBIF unreachable after {tries} tries: {url}")


def taxon_key(name: str):
    if name not in _KEYCACHE:
        d = _get("species/match", {"name": name})
        _KEYCACHE[name] = d.get("usageKey") if d.get("matchType") != "NONE" else None
    return _KEYCACHE[name]


def fetch(bbox, taxon_keys, year_min=2016, page=300, max_records=6000):
    """Fetch HUMAN_OBSERVATION occurrences (WGS84 bbox) for the given taxon keys, via urllib."""
    minx, miny, maxx, maxy = bbox
    base = {"decimalLongitude": f"{minx},{maxx}", "decimalLatitude": f"{miny},{maxy}",
            "hasCoordinate": "true", "hasGeospatialIssue": "false",
            "basisOfRecord": "HUMAN_OBSERVATION", "year": f"{year_min},2026", "limit": page}
    rows = []
    for k in taxon_keys:
        offset = 0
        while offset < max_records:
            d = _get("occurrence/search", {**base, "taxonKey": k, "offset": offset})
            for o in d.get("results", []):
                if o.get("decimalLatitude") is None or o.get("decimalLongitude") is None:
                    continue
                rows.append({"lon": o["decimalLongitude"], "lat": o["decimalLatitude"],
                             "species": o.get("species"), "taxonKey": o.get("taxonKey"),
                             "uncertainty_m": o.get("coordinateUncertaintyInMeters"),
                             "year": o.get("year"), "basis": o.get("basisOfRecord")})
            if d.get("endOfRecords") or not d.get("results"):
                break
            offset += page
            time.sleep(0.35)  # polite pacing to avoid GBIF rate-limiting (429)
        time.sleep(0.5)
    import pandas as pd
    return pd.DataFrame(rows)


def load_layers(city: str, guild: str):
    aoi_p = f"{OUTROOT}/{city}/aoi_limits_{city}.geojson"
    nodes_p = f"{OUTROOT}/{city}/{guild}/nodes_{guild}_{city}.geojson"
    lcp_p = f"{OUTROOT}/{city}/{guild}/lcp_{guild}_{city}.geojson"
    if not (os.path.exists(aoi_p) and os.path.exists(nodes_p)):
        return None
    aoi = gpd.read_file(aoi_p)
    nodes = gpd.read_file(nodes_p)
    utm = nodes.crs
    aoi = aoi.to_crs(utm)
    cores = nodes[nodes.node_type == "core"]
    islets = nodes[nodes.node_type == "islet"]
    corr = gpd.read_file(lcp_p).to_crs(utm) if os.path.exists(lcp_p) else nodes.iloc[:0]
    return aoi, cores, islets, corr, utm


def get_occurrences(city: str, guild: str, aoi, utm):
    keys = [k for k in (taxon_key(lat) for lat, _ in SPECIES_CONFIG[guild]["representative_species"]) if k]
    bbox = tuple(aoi.to_crs(WGS84).total_bounds)
    df = fetch(bbox, keys)
    gdf = to_gdf(df)
    gdf = filter_occurrences(gdf, aoi_wgs=aoi.to_crs(WGS84))
    return spatial_thin(gdf, utm) if len(gdf) else gdf


def draw_panel(ax, city: str, guild: str, title: str) -> int:
    layers = load_layers(city, guild)
    if layers is None:
        ax.axis("off")
        return 0
    aoi, cores, islets, corr, utm = layers
    occ = get_occurrences(city, guild, aoi, utm)
    b = aoi.total_bounds
    ax.set_xlim(b[0], b[2])
    ax.set_ylim(b[1], b[3])
    ctx.add_basemap(ax, crs=utm, source=ctx.providers.Esri.WorldImagery, attribution=False, zorder=0)
    if len(corr):
        corr.plot(ax=ax, color=CORR, linewidth=0.7, alpha=0.85, zorder=2)
    if len(islets):
        islets.plot(ax=ax, facecolor=ISLET, edgecolor="none", alpha=0.7, zorder=3)
    if len(cores):
        cores.plot(ax=ax, facecolor=CORE, edgecolor="none", alpha=0.55, zorder=3)
    aoi.boundary.plot(ax=ax, color="white", linewidth=1.2, zorder=5)
    n = len(occ)
    if n:
        occ.plot(ax=ax, color=OCC, markersize=9, alpha=0.9, zorder=6)
    ax.set_xlim(b[0], b[2])
    ax.set_ylim(b[1], b[3])
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=11)  # effectifs exacts en annexe B (carte illustrative)
    carto.scalebar(ax)
    carto.north(ax)
    carto.graticule(ax)
    return n


def legend_handles():
    return [Patch(facecolor=CORE, label="Noyau de biodiversité"),
            Patch(facecolor=ISLET, label="Élément relais"),
            Line2D([], [], color=CORR, lw=2, label="Lien fonctionnel"),
            Line2D([], [], marker="o", color="none", markerfacecolor=OCC, markersize=8,
                   label="Occurrence GBIF")]


def make_guild(guild: str) -> None:
    out = os.path.join(HERE, f"gbif_cartes_{guild}.png")
    if os.path.exists(out):
        print(os.path.basename(out), "déjà présent, saute")
        return
    n = len(CITIES)
    fig, axes = plt.subplots(1, n, figsize=(4.6 * n, 5.2))
    for ax, city in zip(axes, CITIES):
        try:
            draw_panel(ax, city, guild, CITY_LABEL.get(city, city))
        except Exception as e:  # un panneau qui échoue ne doit pas tuer la planche entière
            ax.axis("off")
            ax.set_title(f"{CITY_LABEL.get(city, city)}\n(échec {type(e).__name__})", fontsize=9)
            print(f"  ÉCHEC {guild}/{city} : {type(e).__name__} {e}")
    _lg = axes[-1].legend(handles=legend_handles(), loc="lower right", fontsize=8, frameon=True)
    _lg.set_zorder(20)  # au-dessus des occurrences (zorder 6)
    art = "de l'" if guild == "forest_edge_bird" else "du "  # élision devant « oiseau »
    fig.suptitle(f"Occurrences GBIF {art}{GUILD_FR[guild]} sur le réseau modélisé", fontsize=13)
    out = os.path.join(HERE, f"gbif_cartes_{guild}.png")
    fig.savefig(out, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(os.path.basename(out), "OK")


def make_toulouse_fauvette() -> None:
    out = os.path.join(HERE, "gbif_carte_Toulouse_fauvette.png")
    if os.path.exists(out):
        print(os.path.basename(out), "déjà présent, saute")
        return
    fig, ax = plt.subplots(figsize=(7.2, 7.2))
    draw_panel(ax, "Toulouse", "forest_edge_bird", "Toulouse")
    _lg = ax.legend(handles=legend_handles(), loc="lower right", fontsize=8, frameon=True)
    _lg.set_zorder(20)  # au-dessus des occurrences (zorder 6)
    out = os.path.join(HERE, "gbif_carte_Toulouse_fauvette.png")
    fig.savefig(out, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(os.path.basename(out), "OK")


if __name__ == "__main__":
    for g in ["ground_mammal", "arboreal_mammal", "forest_edge_bird", "ground_reptile"]:
        make_guild(g)
    make_toulouse_fauvette()
    print("Cartes GBIF régénérées dans", HERE)
