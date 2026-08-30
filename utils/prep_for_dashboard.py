"""Convert sp_pipeline.py per-(city, ecoprofil) outputs into the dashboard's
expected files under ``src/assets/data/<city_slug>/`` (AOI) and
``src/assets/data/<city_slug>/<ecoprofil>/`` (nodes, segments, stats, derived,
+ optional dispersal raster + ruptures points).

Expected input layout (``--pipeline-dir``):

    <pipeline-dir>/
      <City>/
        aoi_limits_<City>.geojson                 (per-city AOI)
        <ecoprofil>/
          nodes_<ecoprofil>_<City>.geojson
          corridor_segments_<ecoprofil>_<City>.geojson
          stats_<ecoprofil>_<City>.csv                (one header row + one data row)
          dispersal_<ecoprofil>_<City>.tif            (optional)
          ruptures_<ecoprofil>_<City>.geojson         (optional)
          isolated_nodes_<ecoprofil>_<City>.geojson   (optional)
          barriers_<ecoprofil>_<City>.geojson         (optional)
          ...intermediate files we ignore (friction, lcp, edges, etc.)

Produced layout (``--dashboard-dir/src/assets/data/<city_slug>/``):

    <city_slug>/
      aoi.geojson                                 (WGS84, written once per city)
      <ecoprofil>/
        nodes.geojson                             (WGS84, properties renamed, clipped to AOI)
        segments.geojson                          (WGS84, simplified, dpc normalized 0-100)
        stats.json                                (parsed from the stats CSV)
        derived.json                              (AOI-clipped metrics read from stats.json; recomputed only for legacy outputs)
        dispersal.png                             (optional: RGBA, RdYlGn_r-colormapped)
        dispersal.json                            (optional: WGS84 bounds sidecar)
        ruptures.geojson                          (optional: WGS84 points)
        barriers.geojson                          (optional: WGS84 line segments)

Usage
-----

Single pair::

    python prep_for_dashboard.py \\
        --city Perpignan \\
        --city-slug perpignan \\
        --ecoprofil ground_mammal \\
        --pipeline-dir /path/to/outputs_sp_pipeline \\
        --dashboard-dir ./urban-connectivity

Batch (all cities + all ecoprofils present in --pipeline-dir)::

    python prep_for_dashboard.py --all \\
        --pipeline-dir /path/to/outputs_sp_pipeline \\
        --dashboard-dir ./urban-connectivity
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

# Raw pipeline column to dashboard property name.
NODE_PROPS: dict[str, str] = {
    "node_id":       "id",     # graph node id (matches rupture/barrier node_1/node_2)
    "node_type":     "type",   # 'core' or 'islet'
    "total_area_ha": "area",   # ha
    "max_core_ha":   "core",   # ha (interior surface)
    "nbc_score":     "nbc",    # 0-100
}
SEGMENT_PROPS: dict[str, str] = {
    "corridor_count":   "cc",     # int
    "sum_dPC":          "dpc",    # raw, will be normalized 0-100 per file
    "max_pinch_point":  "pinch",  # 0-100
}
RUPTURE_PROPS: dict[str, str] = {
    "pn_id":   "id",       # rupture point id
    "wc_code": "wc_code",  # WorldCover landcover class at the rupture
    "node_1":  "node_1",   # adjacent node id (1)
    "node_2":  "node_2",   # adjacent node id (2)
}
# Barrier line properties to keep in the dashboard file. All sp_pipeline
# barrier features have ``status == "failed"`` and null real_dist /
# accumulated_cost / efficiency by construction, so we drop those.
# ``fail_reason`` drives the dashboard's per-line color (real barriers
# vs technical lookup failures).
BARRIER_PROPS: dict[str, str] = {
    "node_1":          "node_1",
    "node_2":          "node_2",
    "theoretical_dist": "dist",
    "fail_reason":     "reason",
    "obstacle":        "obstacle",    # comma-joined wc_codes the barrier crosses ('' if none)
    "n_ruptures":      "n_ruptures",  # number of rupture points on the barrier
}

SEGMENT_SIMPLIFY_TOLERANCE_M: float = 2.0
# Light Douglas-Peucker simplification of node (and isolated-node) polygons,
# purely for render performance. The analysis team smooths the polygons
# upstream, but smoothing oversamples the curves: raw nodes carry ~2.6M
# vertices for a city like Toulouse (~100 MB GeoJSON), which makes the
# Leaflet map crawl. DP only DROPS points from the existing smooth curve
# (never adds jaggedness, so it can't reintroduce pixel stair-steps) and
# guarantees the outline never moves more than this many metres. At 1.0 m
# the deviation is sub-pixel at every normal zoom -- the smoothed look is
# preserved -- while Toulouse drops to ~18 MB (≈ Perpignan, which is fluid).
# Lower toward 0.5 m for more edge fidelity at the cost of ~2x file size.
NODE_SIMPLIFY_TOLERANCE_M: float = 1.0
WGS84: str = "EPSG:4326"
COORD_DECIMALS: int = 5  # ~1 m precision at WGS84.

# AOI-clipped derived metrics. The pipeline (sp_pipeline.py) now emits these directly in
# stats_<ecoprofil>_<city>.csv, so prep reads them from stats.json (single source of truth) and
# only recomputes them as a fallback for outputs produced before that change.
DERIVED_KEYS: tuple[str, ...] = (
    "aoi_total_ha", "habitat_ha_in_aoi", "habitat_coverage_pct",
    "nodes_in_aoi", "cores_in_aoi", "islets_in_aoi",
)


def _round_coords(obj, decimals: int = COORD_DECIMALS):  # noqa: ANN001, ANN201
    """Walk a GeoJSON tree, rounding every float leaf to ``decimals`` places."""
    if isinstance(obj, list):
        return [_round_coords(x, decimals) for x in obj]
    if isinstance(obj, dict):
        return {k: _round_coords(v, decimals) for k, v in obj.items()}
    if isinstance(obj, float):
        return round(obj, decimals)
    return obj


def _write_geojson(gdf: gpd.GeoDataFrame, dst: Path) -> None:
    """Write a GeoDataFrame to GeoJSON with rounded coordinates."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    payload = json.loads(gdf.to_json())
    payload = _round_coords(payload)
    dst.write_text(json.dumps(payload, separators=(",", ":")))


def _round_if_present(gdf: gpd.GeoDataFrame, col: str, ndigits: int) -> None:
    """Round a numeric column in-place if it exists.

    Coerces to numeric first: some upstream properties (e.g. ``nbc_score``
    for degree-0 nodes) come through as JSON ``null`` -> Python ``None``,
    which makes the column ``object`` dtype and ``Series.round`` raise
    ``TypeError: NoneType doesn't define __round__``. ``to_numeric`` turns
    those nulls into ``NaN`` (rendered as ``null`` in the output GeoJSON).
    """
    if col in gdf.columns:
        gdf[col] = pd.to_numeric(gdf[col], errors="coerce").round(ndigits)


def prep_aoi(src: Path, dst: Path) -> tuple[gpd.GeoDataFrame, float]:
    """Reproject AOI to WGS84, drop all properties, write to ``dst``.

    Returns
    -------
    aoi_wgs : gpd.GeoDataFrame
        Reprojected AOI (used downstream to clip nodes).
    aoi_area_ha : float
        Total AOI surface in hectares.
    """
    gdf = gpd.read_file(src)
    src_crs = gdf.crs
    if src_crs is None or src_crs.is_geographic:
        utm = gdf.estimate_utm_crs()
        aoi_area_ha = float(gdf.to_crs(utm).area.sum() / 10_000)
    else:
        aoi_area_ha = float(gdf.area.sum() / 10_000)

    gdf_wgs = gdf.to_crs(WGS84)[["geometry"]]
    _write_geojson(gdf_wgs, dst)
    return gdf_wgs, aoi_area_ha


def prep_nodes(
    src: Path,
    dst: Path,
    aoi_wgs: gpd.GeoDataFrame,
) -> dict[str, float | int]:
    """Reproject + rename + clip nodes to AOI, write to ``dst``, return derived stats."""
    gdf = gpd.read_file(src)
    utm = gdf.crs

    if NODE_SIMPLIFY_TOLERANCE_M > 0:
        gdf["geometry"] = gdf.geometry.simplify(
            NODE_SIMPLIFY_TOLERANCE_M, preserve_topology=True
        )
        gdf = gdf[~gdf.geometry.is_empty].copy()

    aoi_in_src = aoi_wgs.to_crs(utm).geometry.union_all()
    in_aoi = gdf[gdf.geometry.intersects(aoi_in_src)].copy()
    clipped_area_m2 = in_aoi.geometry.intersection(aoi_in_src).area

    in_aoi = in_aoi.rename(columns=NODE_PROPS)
    _round_if_present(in_aoi, "area", 2)
    _round_if_present(in_aoi, "core", 2)
    _round_if_present(in_aoi, "nbc", 2)
    keep = ["geometry"] + [c for c in NODE_PROPS.values() if c in in_aoi.columns]
    in_aoi = in_aoi[keep].reset_index(drop=True)
    # Prefer the upstream graph node id (so rupture/barrier node_1/node_2
    # resolve to these patches); fall back to a 1-based index for older
    # data that predates the node_id export.
    if "id" in in_aoi.columns:
        in_aoi["id"] = pd.to_numeric(in_aoi["id"], errors="coerce").astype("Int64")
    else:
        in_aoi["id"] = in_aoi.index + 1

    habitat_ha_in_aoi = round(float(clipped_area_m2.sum() / 10_000), 1)
    derived = {
        "habitat_ha_in_aoi": habitat_ha_in_aoi,
        "nodes_in_aoi": int(len(in_aoi)),
        "cores_in_aoi": (
            int((in_aoi["type"] == "core").sum()) if "type" in in_aoi.columns else 0
        ),
        "islets_in_aoi": (
            int((in_aoi["type"] == "islet").sum()) if "type" in in_aoi.columns else 0
        ),
    }
    _write_geojson(in_aoi.to_crs(WGS84), dst)
    return derived


def prep_segments(src: Path, dst: Path) -> None:
    """Reproject + simplify + rename + normalize segments, write to ``dst``."""
    gdf = gpd.read_file(src)
    gdf["geometry"] = gdf.geometry.simplify(
        SEGMENT_SIMPLIFY_TOLERANCE_M, preserve_topology=True
    )
    gdf = gdf[~gdf.geometry.is_empty].copy()
    gdf = gdf.rename(columns=SEGMENT_PROPS)
    if "dpc" in gdf.columns:
        # Coerce first: a null dpc would make the column object dtype and
        # break the max()/division below (same null-property issue as
        # _round_if_present).
        gdf["dpc"] = pd.to_numeric(gdf["dpc"], errors="coerce")
        max_dpc = float(gdf["dpc"].max())
        if max_dpc > 0:
            gdf["dpc"] = (gdf["dpc"] / max_dpc) * 100.0
    _round_if_present(gdf, "dpc", 2)
    _round_if_present(gdf, "pinch", 2)
    keep = ["geometry"] + [c for c in SEGMENT_PROPS.values() if c in gdf.columns]
    gdf = gdf[keep].reset_index(drop=True)
    gdf["id"] = gdf.index + 1
    _write_geojson(gdf.to_crs(WGS84), dst)


def prep_isolated_nodes(
    src: Path,
    dst: Path,
    aoi_wgs: gpd.GeoDataFrame,
) -> int:
    """Reproject + rename + clip isolated-node polygons to AOI, write to ``dst``.

    The upstream ``isolated_nodes_<ecoprofil>_<city>.geojson`` shares the
    ``nodes_*`` property schema (``node_type``, ``total_area_ha``,
    ``max_core_ha``) with an extra ``class`` field describing the
    isolation type. We rename to the same dashboard convention as
    ``prep_nodes`` so the existing tooltip/legend machinery can render
    these features.

    Returns
    -------
    int
        Count of isolated polygons written.
    """
    gdf = gpd.read_file(src)
    utm = gdf.crs

    if NODE_SIMPLIFY_TOLERANCE_M > 0:
        gdf["geometry"] = gdf.geometry.simplify(
            NODE_SIMPLIFY_TOLERANCE_M, preserve_topology=True
        )
        gdf = gdf[~gdf.geometry.is_empty].copy()

    aoi_in_src = aoi_wgs.to_crs(utm).geometry.union_all()
    in_aoi = gdf[gdf.geometry.intersects(aoi_in_src)].copy()

    in_aoi = in_aoi.rename(columns=NODE_PROPS)
    _round_if_present(in_aoi, "area", 2)
    _round_if_present(in_aoi, "core", 2)
    keep = ["geometry"] + [c for c in NODE_PROPS.values() if c in in_aoi.columns]
    in_aoi = in_aoi[keep].reset_index(drop=True)
    # Keep the upstream graph node id when present (so isolated patches carry
    # the same id space as ruptures/barriers); else fall back to a 1-based index.
    if "id" in in_aoi.columns:
        in_aoi["id"] = pd.to_numeric(in_aoi["id"], errors="coerce").astype("Int64")
    else:
        in_aoi["id"] = in_aoi.index + 1

    _write_geojson(in_aoi.to_crs(WGS84), dst)
    return int(len(in_aoi))


def prep_barriers(src: Path, dst: Path) -> int:
    """Reproject barrier lines to WGS84, keep all entries, write to ``dst``.

    Each barrier feature is a short LineString between two nodes that the
    sp_pipeline tried (and failed) to connect. ``fail_reason`` is kept so
    the dashboard's JS handler can color real obstacles
    (``uncrossable_barrier``) differently from technical lookup failures
    (``node_not_found``) -- see ``connectivity_layers.js::barrierLayer``.

    Returns
    -------
    int
        Count of barrier lines written.
    """
    gdf = gpd.read_file(src)
    gdf = gdf.rename(columns=BARRIER_PROPS)
    _round_if_present(gdf, "dist", 2)
    keep = ["geometry"] + [c for c in BARRIER_PROPS.values() if c in gdf.columns]
    gdf = gdf[keep].reset_index(drop=True)
    gdf["id"] = gdf.index + 1
    _write_geojson(gdf.to_crs(WGS84), dst)
    return int(len(gdf))


def prep_ruptures(src: Path, dst: Path) -> int:
    """Reproject ruptures (point features) to WGS84, write to ``dst``.

    Each rupture marks where a corridor is blocked by a barrier landcover
    class. Properties are minimal: ``id``, ``wc_code`` (WorldCover class),
    ``node_1`` and ``node_2`` (the patches the broken corridor would have
    connected).

    Returns
    -------
    int
        Count of rupture points written.
    """
    gdf = gpd.read_file(src)
    gdf = gdf.rename(columns=RUPTURE_PROPS)
    keep = ["geometry"] + [c for c in RUPTURE_PROPS.values() if c in gdf.columns]
    gdf = gdf[keep].reset_index(drop=True)
    _write_geojson(gdf.to_crs(WGS84), dst)
    return int(len(gdf))


def _export_dispersal_raster(
    src: Path,
    dst_dir: Path,
    aoi_wgs: gpd.GeoDataFrame | None = None,
    blur_sigma: float = 1.5,
    upsample: int = 2,
) -> None:
    """Convert a dispersal GeoTIFF to dashboard-ready dispersal.png + dispersal.json.

    RdYlGn_r colormap (low cost = green, high cost = red),
    Gaussian-blurred + bilinearly upsampled to mask the source 10 m pixel
    grid. Barriers (np.inf) are overlaid as semi-opaque near-black after
    blurring so they stay crisp; NaN/NoData renders fully transparent.

    If ``aoi_wgs`` is provided, cells whose center is OUTSIDE the AOI
    polygon are forced to transparent. sp_pipeline.py sometimes outputs
    a dispersal raster that extends asymmetrically beyond the AOI (e.g.
    Nancy's run has ~600 m of east-side buffer vs ~280 m on the west),
    which makes the raster look misaligned with the AOI / nodes layers
    in the dashboard. Masking to the AOI fixes that without resizing
    the PNG (so the sidecar bounds + ImageOverlay positioning stay
    consistent across pairs).

    The sidecar JSON carries the WGS84 bounding box for Leaflet's
    ``dl.ImageOverlay`` as ``{"bounds": [[south, west], [north, east]]}``.
    """
    import matplotlib as mpl
    import numpy as np
    import rasterio
    from PIL import Image, ImageFilter
    from rasterio.features import geometry_mask
    from rasterio.warp import Resampling, calculate_default_transform, reproject

    dst_dir.mkdir(parents=True, exist_ok=True)

    # Reproject the raster from its native UTM CRS to EPSG:4326 BEFORE
    # exporting the PNG. Leaflet's ImageOverlay assumes the image is
    # axis-aligned in the target CRS; a UTM raster passed through with
    # only a bounding-box transform shows alignment drift wherever the
    # UTM grid isn't parallel to lat/lon. The drift is negligible near
    # the equator (Kourou) and small at mid-latitudes (Perpignan ~43N)
    # but visibly off at higher latitudes (Nancy ~49N). Reprojecting
    # makes the PNG pixels correspond directly to lat/lon cells, so
    # Leaflet's stretch-to-bounds is correct everywhere.
    #
    # ``calculate_default_transform`` returns a north-up target
    # transform regardless of the source's Y-scale sign, so we don't
    # need the manual ``arr[::-1]`` flip anymore.
    with rasterio.open(src) as raster:
        src_arr = raster.read(1)
        src_crs = raster.crs
        src_transform = raster.transform
        src_nodata = raster.nodata
        src_width, src_height = raster.width, raster.height
        b = raster.bounds

    src_west, src_east = min(b.left, b.right), max(b.left, b.right)
    src_south, src_north = min(b.top, b.bottom), max(b.top, b.bottom)
    dst_transform, dst_width, dst_height = calculate_default_transform(
        src_crs, WGS84, src_width, src_height,
        src_west, src_south, src_east, src_north,
    )
    arr = np.full((dst_height, dst_width), np.nan, dtype=np.float32)
    reproject(
        source=src_arr,
        destination=arr,
        src_transform=src_transform,
        src_crs=src_crs,
        dst_transform=dst_transform,
        dst_crs=WGS84,
        # Nearest preserves barrier (inf) cells exactly and matches the
        # source distribution faithfully -- the Gaussian blur below
        # provides smoothing, so we don't need bilinear here.
        resampling=Resampling.nearest,
        src_nodata=src_nodata,
        dst_nodata=np.nan,
    )

    # Bounds for the sidecar JSON come straight from the destination
    # transform; no further reprojection needed.
    west = dst_transform.c
    north = dst_transform.f
    east = west + dst_transform.a * dst_width
    south = north + dst_transform.e * dst_height

    barrier = np.isinf(arr)
    valid = np.isfinite(arr)
    # nodata in the reprojected array is NaN by construction, already
    # excluded by np.isfinite().

    # Mask cells outside the AOI. We now operate in EPSG:4326, so the
    # AOI doesn't need a CRS hop -- ``aoi_wgs`` is already WGS84.
    if aoi_wgs is not None:
        aoi_geom = aoi_wgs.geometry.union_all()
        outside = geometry_mask(
            [aoi_geom],
            out_shape=arr.shape,
            transform=dst_transform,
            invert=False,  # True outside the geometry
        )
        valid &= ~outside
        barrier &= ~outside

    transparent = ~valid & ~barrier  # NaN/nodata/outside-AOI, excluding inf barriers

    # Normalise the dispersal field into [0, 1] using a percentile stretch
    # + gamma correction. Raw min-max produces near-all-green maps because
    # the cumulative-cost distribution is heavily right-skewed: median is
    # at or near 0 (cells inside source habitat) and the high tail
    # stretches to 5e3 - 5e4 depending on ecoprofil. min-max would compress
    # the bulk of pixels into the green end.
    #
    # - vmin/vmax pinned at the 1st and 99th percentiles of valid cells
    #   so a handful of extreme outliers don't dominate the scale.
    # - Gamma 0.5 (square-root) brightens the colormap: a normalised
    #   value of 0.25 maps to colormap position 0.5 (mid-yellow), making
    #   moderate-cost pixels read as yellow instead of pale green.
    if valid.any():
        valid_vals = arr[valid]
        vmin = float(np.percentile(valid_vals, 1))
        vmax = float(np.percentile(valid_vals, 99))
    else:
        vmin, vmax = 0.0, 1.0
    span = max(vmax - vmin, 1e-9)
    norm = np.clip((arr - vmin) / span, 0.0, 1.0)
    gamma = 0.5
    norm = np.power(norm, gamma)
    norm_masked = np.where(valid, norm, 0.0)
    weight = valid.astype(np.float32)

    if blur_sigma > 0:
        v_u8 = (norm_masked * 255).astype(np.uint8)
        w_u8 = (weight * 255).astype(np.uint8)
        v_img = Image.fromarray(v_u8, mode="L").filter(
            ImageFilter.GaussianBlur(radius=blur_sigma)
        )
        w_img = Image.fromarray(w_u8, mode="L").filter(
            ImageFilter.GaussianBlur(radius=blur_sigma)
        )
        v_blur = np.asarray(v_img, dtype=np.float32) / 255.0
        w_blur = np.asarray(w_img, dtype=np.float32) / 255.0
        smoothed = np.divide(
            v_blur, w_blur,
            out=np.zeros_like(v_blur),
            where=w_blur > 1e-3,
        )
    else:
        smoothed = norm_masked

    if upsample > 1:
        h, w = smoothed.shape
        new_size = (w * upsample, h * upsample)
        smoothed_img = Image.fromarray(
            (np.clip(smoothed, 0.0, 1.0) * 255).astype(np.uint8), mode="L"
        ).resize(new_size, Image.Resampling.BILINEAR)
        smoothed = np.asarray(smoothed_img, dtype=np.float32) / 255.0
        barrier = np.asarray(
            Image.fromarray(barrier.astype(np.uint8) * 255, mode="L")
            .resize(new_size, Image.Resampling.NEAREST)
        ) > 127
        transparent = np.asarray(
            Image.fromarray(transparent.astype(np.uint8) * 255, mode="L")
            .resize(new_size, Image.Resampling.NEAREST)
        ) > 127

    cmap = mpl.colormaps["RdYlGn_r"]
    rgba = (cmap(np.clip(smoothed, 0.0, 1.0)) * 255).astype(np.uint8)
    rgba[barrier] = [26, 26, 26, 210]     # barriers: crisp, semi-opaque near-black
    rgba[transparent] = [0, 0, 0, 0]      # NaN/nodata: fully transparent

    Image.fromarray(rgba, mode="RGBA").save(
        dst_dir / "dispersal.png", optimize=True,
    )
    (dst_dir / "dispersal.json").write_text(
        json.dumps({"bounds": [[south, west], [north, east]]}, indent=2)
    )


def prep_stats(src: Path, dst: Path) -> dict:
    """Convert the upstream single-row stats CSV to the dashboard's stats.json.

    sp_pipeline now emits ``stats_<ecoprofil>_<city>.csv`` (one header row of
    metric names + exactly one data row of values) instead of a JSON object.
    We parse that single row into a flat ``{metric: value}`` mapping and write
    it as ``stats.json`` -- the dashboard's ``data_access.load_stats`` still
    reads JSON. ``to_json(orient="records")`` is used (rather than a row
    Series) so per-column dtypes survive: integer counts stay ints, ratios
    and tortuosity stay floats, matching the previous passthrough JSON.

    Returns
    -------
    dict
        The parsed stats (also written to ``dst``).
    """
    df = pd.read_csv(src)
    if df.empty:
        raise ValueError(f"stats CSV has no data row: {src}")
    if len(df) > 1:
        print(f"    Warning: stats CSV has {len(df)} rows, using the first.")
    stats = json.loads(df.head(1).to_json(orient="records", double_precision=15))[0]
    dst.write_text(json.dumps(stats, indent=2))
    return stats


def prep_one_pair(
    city_name: str,
    city_slug: str,
    ecoprofil: str,
    pipeline_dir: Path,
    dashboard_dir: Path,
    overwrite_aoi: bool = False,
) -> None:
    """Prepare one (city, ecoprofil) bundle end-to-end.

    Resolves input paths against the new nested layout::

        <pipeline-dir>/<city_name>/aoi_limits_<city_name>.geojson
        <pipeline-dir>/<city_name>/<ecoprofil>/<file>_<ecoprofil>_<city_name>.<ext>
    """
    city_in = pipeline_dir / city_name
    ecoprofil_in = city_in / ecoprofil

    src_aoi      = city_in / f"aoi_limits_{city_name}.geojson"
    src_nodes    = ecoprofil_in / f"nodes_{ecoprofil}_{city_name}.geojson"
    src_segments = ecoprofil_in / f"corridor_segments_{ecoprofil}_{city_name}.geojson"
    src_stats    = ecoprofil_in / f"stats_{ecoprofil}_{city_name}.csv"

    for label, p in [
        ("AOI", src_aoi), ("nodes", src_nodes),
        ("segments", src_segments), ("stats", src_stats),
    ]:
        if not p.exists():
            raise FileNotFoundError(f"{label} file missing: {p}")

    city_dir = dashboard_dir / "src" / "assets" / "data" / city_slug
    ecoprofil_dir = city_dir / ecoprofil
    ecoprofil_dir.mkdir(parents=True, exist_ok=True)
    aoi_dst = city_dir / "aoi.geojson"

    if aoi_dst.exists() and not overwrite_aoi:
        print(f"  AOI already exists at {aoi_dst}, reusing.")
        aoi_wgs = gpd.read_file(aoi_dst)
        utm = aoi_wgs.estimate_utm_crs()
        aoi_area_ha = float(aoi_wgs.to_crs(utm).area.sum() / 10_000)
    else:
        print(f"  Writing AOI to {aoi_dst}...")
        aoi_wgs, aoi_area_ha = prep_aoi(src_aoi, aoi_dst)

    print(f"  Preparing nodes (clipping to AOI)...")
    node_derived = prep_nodes(src_nodes, ecoprofil_dir / "nodes.geojson", aoi_wgs)

    print(f"  Preparing segments (simplifying, normalizing dpc 0-100)...")
    prep_segments(src_segments, ecoprofil_dir / "segments.geojson")

    # Dispersal raster (optional): replaces the prior friction overlay in
    # the dashboard. Same colour-map and overlay machinery, different
    # ecological semantic (probability of dispersal vs movement cost).
    src_dispersal = ecoprofil_in / f"dispersal_{ecoprofil}_{city_name}.tif"
    if src_dispersal.exists():
        print(f"  Preparing dispersal raster (color-mapping, masking to AOI)...")
        _export_dispersal_raster(src_dispersal, ecoprofil_dir, aoi_wgs=aoi_wgs)
    else:
        print(f"  No dispersal raster at {src_dispersal.name}, skipping (optional).")

    # Isolated nodes (optional): subset of habitat patches that have no
    # connection to any other patch (graph degree 0). Rendered with a
    # diagonal-hatch overlay on top of the regular node fill so the user
    # can spot them at a glance.
    src_isolated = ecoprofil_in / f"isolated_nodes_{ecoprofil}_{city_name}.geojson"
    if src_isolated.exists():
        print(f"  Preparing isolated nodes (clipping to AOI)...")
        n_isolated = prep_isolated_nodes(
            src_isolated, ecoprofil_dir / "isolated.geojson", aoi_wgs,
        )
        print(f"    -> {n_isolated} isolated patches")
    else:
        print(f"  No isolated-nodes file at {src_isolated.name}, skipping (optional).")

    # Rupture points layer removed: the rupture info now lives on the barriers
    # (obstacle / n_ruptures), so no standalone ruptures layer is prepared. The
    # `prep_ruptures` helper is kept for backward compatibility but no longer called.

    # Barrier lines (optional): failed connection attempts between
    # adjacent nodes. Used by the dashboard's Overview map to flag where
    # the pipeline couldn't draw a corridor (real obstacles vs technical
    # lookup failures, colored differently by fail_reason).
    src_barriers = ecoprofil_in / f"barriers_{ecoprofil}_{city_name}.geojson"
    if src_barriers.exists():
        print(f"  Preparing barriers (reprojecting to WGS84)...")
        n_barriers = prep_barriers(src_barriers, ecoprofil_dir / "barriers.geojson")
        print(f"    -> {n_barriers} barrier lines")
    else:
        print(f"  No barriers file at {src_barriers.name}, skipping (optional).")

    print(f"  Converting stats CSV -> stats.json...")
    stats = prep_stats(src_stats, ecoprofil_dir / "stats.json")

    # Derived AOI-clipped metrics now come straight from the pipeline stats (single source of
    # truth, computed on full-fidelity geometry upstream). Recompute only for legacy outputs
    # that predate sp_pipeline emitting them.
    if all(stats.get(k) is not None for k in DERIVED_KEYS):
        derived = {k: stats[k] for k in DERIVED_KEYS}
    else:
        print("    stats.json carries no derived metrics (pre-change output); recomputing locally.")
        derived = {
            "aoi_total_ha":          round(aoi_area_ha, 1),
            "habitat_ha_in_aoi":     node_derived["habitat_ha_in_aoi"],
            "habitat_coverage_pct":  (
                round(node_derived["habitat_ha_in_aoi"] / aoi_area_ha * 100, 1)
                if aoi_area_ha > 0 else 0.0
            ),
            "nodes_in_aoi":          node_derived["nodes_in_aoi"],
            "cores_in_aoi":          node_derived["cores_in_aoi"],
            "islets_in_aoi":         node_derived["islets_in_aoi"],
        }
    (ecoprofil_dir / "derived.json").write_text(json.dumps(derived, indent=2))
    print(f"  derived.json: {derived}")
    print(f"  Done. Output at {ecoprofil_dir}")


def discover_pairs(pipeline_dir: Path) -> list[tuple[str, str]]:
    """Walk ``pipeline_dir`` and return every ``(City, ecoprofil)`` pair found.

    A pair is considered valid when both the per-city AOI and the per-ecoprofil
    nodes file exist. Ignores hidden / dotfile folders (e.g. ``.ipynb_checkpoints``).
    """
    pairs: list[tuple[str, str]] = []
    for city_dir in sorted(p for p in pipeline_dir.iterdir() if p.is_dir()):
        city = city_dir.name
        if city.startswith("."):
            continue
        aoi = city_dir / f"aoi_limits_{city}.geojson"
        if not aoi.exists():
            continue
        for ecoprofil_dir in sorted(p for p in city_dir.iterdir() if p.is_dir()):
            ecoprofil = ecoprofil_dir.name
            if ecoprofil.startswith("."):
                continue
            if (ecoprofil_dir / f"nodes_{ecoprofil}_{city}.geojson").exists():
                pairs.append((city, ecoprofil))
    return pairs


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--all", action="store_true",
                    help="Prep every (city, ecoprofil) pair discovered in --pipeline-dir.")
    ap.add_argument("--city",
                    help="City name as used in pipeline filenames (e.g. 'Perpignan'). "
                         "Required unless --all is set.")
    ap.add_argument("--city-slug",
                    help="Lowercase URL-safe slug used as the dashboard data folder "
                         "(e.g. 'perpignan'). Defaults to --city lowercased.")
    ap.add_argument("--ecoprofil",
                    help="Ecoprofil key (e.g. 'ground_mammal'). Required unless --all is set.")
    _here = Path(__file__).resolve().parent
    ap.add_argument("--pipeline-dir", type=Path, default=_here / "data",
                    help="Directory containing the raw pipeline outputs.")
    ap.add_argument("--dashboard-dir", type=Path, default=_here,
                    help="urban-connectivity project root.")
    ap.add_argument("--overwrite-aoi", action="store_true",
                    help="Rewrite the city-level AOI file even if it already exists.")
    args = ap.parse_args()

    if args.all:
        pairs = discover_pairs(args.pipeline_dir)
        if not pairs:
            print(f"No (city, ecoprofil) pairs discovered under {args.pipeline_dir}.")
            return
        print(f"Discovered {len(pairs)} (city, ecoprofil) pairs:")
        for city, ecoprofil in pairs:
            print(f"  - {city} / {ecoprofil}")
        for city, ecoprofil in pairs:
            print(f"\n=== {city} / {ecoprofil} ===")
            prep_one_pair(
                city_name=city,
                city_slug=city.lower(),
                ecoprofil=ecoprofil,
                pipeline_dir=args.pipeline_dir,
                dashboard_dir=args.dashboard_dir,
                overwrite_aoi=args.overwrite_aoi,
            )
        return

    if not (args.city and args.ecoprofil):
        ap.error("--city and --ecoprofil are required (or pass --all).")

    print(f"Preparing {args.city} / {args.ecoprofil} ...")
    prep_one_pair(
        city_name=args.city,
        city_slug=args.city_slug or args.city.lower(),
        ecoprofil=args.ecoprofil,
        pipeline_dir=args.pipeline_dir,
        dashboard_dir=args.dashboard_dir,
        overwrite_aoi=args.overwrite_aoi,
    )


if __name__ == "__main__":
    main()
