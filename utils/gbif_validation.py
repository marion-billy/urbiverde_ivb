"""GBIF occurrence validation for the connectivity pipeline (habitat-side external check).

Fetches, filters and spatially thins species occurrences (and a target-group background that
captures observation effort) per (city, ecoprofil), via the GBIF REST API. No auth, no extra
dependency (uses ``requests``, always available). This module only PRODUCES the cleaned occurrence
+ background layers; the use-vs-availability cross-test against the modelled cores/corridors
(selection ratios) is run downstream once the pipeline outputs exist.

Scope note: occurrences validate the HABITAT / presence side (are the guild's species where the
model puts habitat?), NOT the connectivity/flow itself. The target-group background + spatial
thinning neutralise the dominant GBIF sampling bias (records cluster where observers go).

Reference / representative species and the target-group class are read from ``species_params``.
"""
from __future__ import annotations

import time

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from shapely.geometry import Point

GBIF = "https://api.gbif.org/v1"
WGS84 = "EPSG:4326"


def _get(path: str, params: dict, tries: int = 5) -> dict:
    """GET a GBIF endpoint with backoff on rate-limit (429) / transient (503) errors."""
    for attempt in range(tries):
        r = requests.get(f"{GBIF}/{path}", params=params, timeout=60)
        if r.status_code in (429, 503):
            time.sleep(2 ** attempt)  # 1, 2, 4, 8, 16 s
            continue
        r.raise_for_status()
        return r.json()
    r.raise_for_status()
    return r.json()

# Guild -> GBIF class used as the target-group background (the sampling universe of the same
# observer community: mammals observed by the same people as the hedgehog, etc.).
TGB_CLASS: dict[str, str] = {
    "ground_mammal": "Mammalia",
    "arboreal_mammal": "Mammalia",
    "forest_edge_bird": "Aves",
    "ground_reptile": "Reptilia",
}


def taxon_key(name: str) -> int | None:
    """Resolve a scientific name to its GBIF usageKey (species-rank match), or None."""
    d = _get("species/match", {"name": name})
    return d.get("usageKey") if d.get("matchType") != "NONE" else None


def guild_species(ecoprofil: str, species_config: dict) -> list[tuple[str, str]]:
    """Return the (latin, french) representative species of an ecoprofil from species_params."""
    return list(species_config[ecoprofil].get("representative_species", []))


def fetch_occurrences(
    bbox: tuple[float, float, float, float],
    taxon_keys: list[int] | None = None,
    class_name: str | None = None,
    year_min: int = 2016,
    basis: str = "HUMAN_OBSERVATION",
    max_records: int = 40_000,
    page: int = 300,
) -> pd.DataFrame:
    """Fetch GBIF occurrences in a WGS84 bbox (minx, miny, maxx, maxy).

    Provide ``taxon_keys`` (focal species) OR ``class_name`` (target-group background). Applies the
    server-side filters shared by both so focal and background come from the SAME sampling universe.

    Returns a DataFrame with lon, lat, species, coordinateUncertaintyInMeters, year, basisOfRecord.
    """
    minx, miny, maxx, maxy = bbox
    base = {
        "decimalLongitude": f"{minx},{maxx}",
        "decimalLatitude": f"{miny},{maxy}",
        "hasCoordinate": "true",
        "hasGeospatialIssue": "false",
        "basisOfRecord": basis,
        "year": f"{year_min},2026",
        "limit": page,
    }
    keysets: list[dict] = []
    if taxon_keys:
        keysets = [{"taxonKey": k} for k in taxon_keys]  # one query per taxon (OR)
    elif class_name:
        ck = taxon_key(class_name)
        if ck is None:
            raise ValueError(f"class not resolved: {class_name}")
        keysets = [{"taxonKey": ck}]
    else:
        raise ValueError("give taxon_keys or class_name")

    rows: list[dict] = []
    for extra in keysets:
        offset = 0
        while offset < max_records:
            params = {**base, **extra, "offset": offset}
            d = _get("occurrence/search", params)
            for o in d.get("results", []):
                if o.get("decimalLatitude") is None or o.get("decimalLongitude") is None:
                    continue
                rows.append({
                    "lon": o["decimalLongitude"], "lat": o["decimalLatitude"],
                    "species": o.get("species"), "taxonKey": o.get("taxonKey"),
                    "uncertainty_m": o.get("coordinateUncertaintyInMeters"),
                    "year": o.get("year"), "basis": o.get("basisOfRecord"),
                })
            if d.get("endOfRecords") or not d.get("results"):
                break
            offset += page
            time.sleep(0.2)  # be polite to the API
    return pd.DataFrame(rows)


def to_gdf(df: pd.DataFrame) -> gpd.GeoDataFrame:
    """Point GeoDataFrame (EPSG:4326) from a lon/lat occurrence DataFrame."""
    if df.empty:
        return gpd.GeoDataFrame(df, geometry=[], crs=WGS84)
    return gpd.GeoDataFrame(
        df, geometry=[Point(x, y) for x, y in zip(df["lon"], df["lat"])], crs=WGS84,
    )


def filter_occurrences(
    gdf: gpd.GeoDataFrame,
    aoi_wgs: gpd.GeoDataFrame | None = None,
    max_uncertainty_m: float = 100.0,
    drop_null_uncertainty: bool = True,
) -> gpd.GeoDataFrame:
    """Rigorous filtering: coordinate precision, clip to AOI, drop exact duplicates.

    ``max_uncertainty_m`` keeps only precise records (default 100 m, i.e. ~1 pixel). Municipality
    centroids and coarse records carry a large (or null) uncertainty and are dropped.
    """
    if gdf.empty:
        return gdf
    g = gdf.copy()
    unc = pd.to_numeric(g["uncertainty_m"], errors="coerce")
    keep = unc <= max_uncertainty_m
    keep = keep if drop_null_uncertainty else (keep | unc.isna())
    g = g[keep].copy()
    if aoi_wgs is not None and len(g):
        g = g[g.geometry.within(aoi_wgs.to_crs(WGS84).geometry.union_all())].copy()
    # exact-coordinate duplicates (same record re-uploaded / same spot repeatedly)
    g = g.drop_duplicates(subset=["lon", "lat", "taxonKey"]).reset_index(drop=True)
    return g


def spatial_thin(gdf: gpd.GeoDataFrame, utm_epsg: str, cell_m: float = 10.0) -> gpd.GeoDataFrame:
    """Keep at most one occurrence per ``cell_m`` grid cell (removes oversampling clusters).

    Thinning is per taxon so co-occurring species are not collapsed together.
    """
    if gdf.empty:
        return gdf
    g = gdf.to_crs(utm_epsg).copy()
    g["_cx"] = (g.geometry.x // cell_m).astype(int)
    g["_cy"] = (g.geometry.y // cell_m).astype(int)
    g = g.drop_duplicates(subset=["taxonKey", "_cx", "_cy"]).drop(columns=["_cx", "_cy"])
    return g.reset_index(drop=True)


# --------------------------------------------------------------------------------------------
# Cross-test: use-vs-availability selection ratios against the modelled cores / corridors.
# Availability is the target-group background distribution (controls for observation effort).
# --------------------------------------------------------------------------------------------

CLASSES = ("core", "stepping_stone", "corridor", "matrix")


def _classify(pts_utm: gpd.GeoDataFrame, core_u, islet_u, corr_u) -> np.ndarray:
    """Label each point core / stepping_stone / corridor / matrix.

    Priority core > stepping stone (islet) > corridor > matrix: a point inside a habitat patch is
    that patch's class even if it also falls in a corridor buffer. Stepping stones (islets) are
    habitat, not matrix, so they get their own class.
    """
    geom = pts_utm.geometry
    z = np.zeros(len(geom), bool)
    in_core = geom.within(core_u).to_numpy() if core_u is not None else z
    in_islet = geom.within(islet_u).to_numpy() if islet_u is not None else z
    in_corr = geom.within(corr_u).to_numpy() if corr_u is not None else z
    return np.where(in_core, "core",
                    np.where(in_islet & ~in_core, "stepping_stone",
                             np.where(in_corr & ~in_core & ~in_islet, "corridor", "matrix")))


def selection_ratios(
    focal_utm: gpd.GeoDataFrame,
    background_utm: gpd.GeoDataFrame,
    cores_utm: gpd.GeoDataFrame,
    islets_utm: gpd.GeoDataFrame,
    corridors_utm: gpd.GeoDataFrame,
    corridor_buffer_m: float = 25.0,
    n_boot: int = 1000,
    seed: int = 0,
) -> pd.DataFrame:
    """Selection ratio per class = (focal use) / (target-group availability), with bootstrap CI.

    Classes: core / stepping_stone / corridor / matrix. Ratio > 1 : the guild's species fall in that
    class MORE than the general observed biodiversity (signal beyond sampling effort). CI from
    resampling the focal point labels.
    """
    core_u = cores_utm.union_all() if len(cores_utm) else None
    islet_u = islets_utm.union_all() if len(islets_utm) else None
    corr_u = corridors_utm.buffer(corridor_buffer_m).union_all() if len(corridors_utm) else None
    fl = pd.Series(_classify(focal_utm, core_u, islet_u, corr_u))
    bl = pd.Series(_classify(background_utm, core_u, islet_u, corr_u))
    avail = bl.value_counts(normalize=True)
    rng = np.random.default_rng(seed)
    arr = fl.to_numpy()
    rows = []
    for c in CLASSES:
        u = float((fl == c).mean())
        a = float(avail.get(c, 0.0))
        ratio = u / a if a > 0 else np.nan
        boots = [((rng.choice(arr, size=len(arr), replace=True) == c).mean() / a) if a > 0 else np.nan
                 for _ in range(n_boot)]
        lo, hi = np.nanpercentile(boots, [2.5, 97.5]) if a > 0 else (np.nan, np.nan)
        rows.append({"class": c, "n_focal": int((fl == c).sum()), "use": round(u, 3),
                     "avail": round(a, 3), "ratio": round(ratio, 2),
                     "ci_lo": round(lo, 2), "ci_hi": round(hi, 2)})
    return pd.DataFrame(rows)


def distance_to_habitat(focal_utm, cores_utm, corridors_utm, aoi_utm, corridor_buffer_m=25.0,
                        seed=0):  # noqa: ANN001, ANN201
    """Distance of focal points vs uniform-random points to the nearest habitat (core+corridor)."""
    parts = []
    if len(cores_utm):
        parts.append(cores_utm.union_all())
    if len(corridors_utm):
        parts.append(corridors_utm.buffer(corridor_buffer_m).union_all())
    from shapely.ops import unary_union
    from shapely.geometry import Point
    hab = unary_union(parts) if parts else None
    aoi_u = aoi_utm.union_all()
    minx, miny, maxx, maxy = aoi_u.bounds
    rng = np.random.default_rng(seed)
    rnd = []
    while len(rnd) < len(focal_utm):
        p = Point(rng.uniform(minx, maxx), rng.uniform(miny, maxy))
        if aoi_u.contains(p):
            rnd.append(p)
    d_focal = focal_utm.geometry.apply(lambda g: g.distance(hab)) if hab is not None else None
    d_rand = gpd.GeoSeries(rnd, crs=aoi_utm.crs).apply(lambda g: g.distance(hab)) if hab is not None else None
    return d_focal, d_rand


def _plot_overlay(focal_wgs, cores, corridors, aoi, out_png, title):  # noqa: ANN001, ANN201
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 7))
    aoi.boundary.plot(ax=ax, color="black", linewidth=0.6)
    if len(corridors):
        corridors.to_crs(aoi.crs).plot(ax=ax, color="#F5A623", linewidth=0.6, alpha=0.7)
    if len(cores):
        cores.to_crs(aoi.crs).plot(ax=ax, color="#2E7D32", alpha=0.45)
    focal_wgs.to_crs(aoi.crs).plot(ax=ax, color="#7E57C2", markersize=7, alpha=0.8)
    ax.set_title(title, fontsize=10)
    ax.axis("off")
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_ratios(df, out_png, title):  # noqa: ANN001, ANN201
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(5.5, 4))
    x = range(len(df))
    ax.bar(x, df["ratio"], color=["#2E7D32", "#F5A623", "#9E9E9E"])
    ax.errorbar(x, df["ratio"], yerr=[df["ratio"] - df["ci_lo"], df["ci_hi"] - df["ratio"]],
                fmt="none", ecolor="black", capsize=4)
    ax.axhline(1.0, color="red", linestyle="--", linewidth=1, label="pas de préférence")
    ax.set_xticks(list(x))
    ax.set_xticklabels(["noyau", "corridor", "matrice"])
    ax.set_ylabel("ratio de sélection (use / dispo TGB)")
    ax.set_title(title, fontsize=10)
    ax.legend(fontsize=8)
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)

