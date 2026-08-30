"""
WIP — alternative corridor-segment builder (polygon/polygonize approach), extracted
from nancy_prod.ipynb on 2026-06-12. This is the in-progress attempt at the still-
UNRESOLVED segment-smoothing / zigzag issue. NOT used by the canonical pipeline
(sp_pipeline uses connectivity.create_urban_planning_segments). Kept here for later work.
"""

# connectivity.py — add `polygonize` to the existing shapely.ops import:
from shapely.ops import nearest_points, unary_union, linemerge, polygonize
from shapely.ops import polygonize, unary_union

def build_corridor_segments(
    gdf_lcp: gpd.GeoDataFrame,
    df_nodes: gpd.GeoDataFrame,
    buffer_width: float = 8.0,
    min_area_m2: float = 50.0,
    round_rules: dict[str, int] | None = None,
) -> gpd.GeoDataFrame:
    """
    Fuse overlapping corridors into areal management segments.

    Replaces the line-union approach (``create_urban_planning_segments`` +
    ``weld_segments``). Geometric union of raster LCP staircases shatters
    coincident corridors into unmergeable pixel-edges; instead each corridor is
    buffered into a ribbon, the ribbons are planar-overlaid, and every resulting
    face is labelled by how many corridors cover it (``corridor_count``) plus
    aggregated metrics. Faces with identical (rounded) attributes are dissolved.

    Parameters
    ----------
    gdf_lcp : geopandas.GeoDataFrame
        Successful LCP corridors; must contain ``dPC_val``, ``ebc_score``,
        ``pinch_point_score`` and a (Multi)LineString geometry.
    df_nodes : geopandas.GeoDataFrame
        Habitat patches; their union is erased so only inter-patch (matrix)
        portions of corridors remain.
    buffer_width : float, default 8.0
        Ribbon half-width (m). Must exceed ~half the raster pixel size so that
        one-pixel-offset duplicates of the same corridor fuse, but stay below
        half the spacing of genuinely distinct corridors (the tuning knob).
    min_area_m2 : float, default 50.0
        Drop overlay slivers below this area.
    round_rules : dict of {str: int}, optional
        Decimals per metric used to group faces for dissolving. Defaults to
        ``{'sum_dPC': 12, 'max_ebc': 3, 'max_pinch_point': 2}``.

    Returns
    -------
    geopandas.GeoDataFrame
        Areal segments (Polygon) with ``corridor_count``, ``sum_dPC``,
        ``max_ebc``, ``max_pinch_point``, ``segment_id``.
    """
    if round_rules is None:
        round_rules = {"sum_dPC": 12, "max_ebc": 3, "max_pinch_point": 2}
    crs = gdf_lcp.crs
    empty_cols = ["corridor_count", "sum_dPC", "max_ebc", "max_pinch_point", "segment_id", "geometry"]

    # 1. Erase in-habitat portions; keep inter-patch matrix segments.
    habitats = df_nodes.geometry.union_all()
    clipped = gdf_lcp.copy()
    clipped["geometry"] = clipped.geometry.difference(habitats)
    clipped = clipped[~clipped.geometry.is_empty & clipped.geometry.notna()].copy()
    if clipped.empty:
        return gpd.GeoDataFrame(columns=empty_cols, geometry="geometry", crs=crs)

    # 2. Buffer each corridor into a ribbon carrying its metrics.
    ribbons = clipped[["dPC_val", "ebc_score", "pinch_point_score"]].copy()
    ribbons["geometry"] = clipped.geometry.buffer(buffer_width)
    ribbons = gpd.GeoDataFrame(ribbons, geometry="geometry", crs=crs).reset_index(drop=True)

    # 3. Planar overlay: polygonize the union of ribbon boundaries into faces.
    faces = gpd.GeoDataFrame(geometry=list(polygonize(unary_union(ribbons.geometry.boundary))), crs=crs)
    if faces.empty:
        return gpd.GeoDataFrame(columns=empty_cols, geometry="geometry", crs=crs)
    faces["face_id"] = range(len(faces))

    # 4. Count covering ribbons per face + aggregate metrics (vectorised sjoin).
    pts = faces.copy()
    pts["geometry"] = faces.geometry.representative_point()
    cov = gpd.sjoin(pts, ribbons, predicate="within", how="inner")
    agg = cov.groupby("face_id").agg(
        corridor_count=("dPC_val", "size"),
        sum_dPC=("dPC_val", "sum"),
        max_ebc=("ebc_score", "max"),
        max_pinch_point=("pinch_point_score", "max"),
    ).reset_index()
    faces = faces.merge(agg, on="face_id", how="inner")   # drops gap faces (0 ribbons)

    # 5. Dissolve faces sharing identical (rounded) attributes.
    for col, nd in round_rules.items():
        faces[col] = faces[col].round(nd)
    dissolve_cols = ["corridor_count"] + list(round_rules.keys())
    seg = faces[dissolve_cols + ["geometry"]].dissolve(by=dissolve_cols).reset_index()
    seg = seg.explode(index_parts=False).reset_index(drop=True)

    # 6. Drop slivers, finalise.
    seg = seg[seg.geometry.area >= min_area_m2].copy()
    seg["segment_id"] = range(len(seg))
    return seg

# ---- cell break ----

gdf_urbanplan_segments = build_corridor_segments(gdf_lcp_city, df_nodes, buffer_width=1.0)
gdf_urbanplan_segments = safe_smooth(gdf_urbanplan_segments)          # POLYGON smoother (same as df_nodes)
gdf_urbanplan_segments["geometry"] = gdf_urbanplan_segments.geometry.buffer(0)
# gdf_urbanplan_segments.to_file(paths.segments(guild_key), driver="GeoJSON")

# ---- cell break ----

gw = conn.weld_segments(sm)        # == gdf_urbanplan_segments in sp_pipeline (3694 rows)