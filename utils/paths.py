"""
corridor_project - centralized output path management (PurePosixPath).

Mirrors the convention reference ``a_b_c_functions/ECCT/ECCT_Paths.py:ProjectPaths``:
pure paths (no I/O when building them) rooted under ``<project_root>/data/``, typed
accessors per output, and an ``init()`` that creates the directories.

Layout (variant B, data/ root rule)::

    <project_root>/data/outputs/<CITY>/<ecoprofil>/<artefact>_<ecoprofil>_<CITY>.<ext>

The stack is posix-only (Linux + NFS + Jupyter), so ``PurePosixPath`` is the right
abstraction: it composes paths without touching the disk; directory creation goes
through ``pathlib.Path`` inside ``init()``.
"""

from pathlib import PurePosixPath
from typing import Union

DEFAULT_PROJECT_ROOT = "/home/jovyan/work/team/marion/corridor_project"


class CorridorPaths:
    """
    Typed accessors for one city's connectivity outputs.

    Parameters
    ----------
    city : str
        Study-area name, used both as a sub-directory and as a filename suffix
        (e.g. ``"Nancy"``).
    project_root : Union[str, PurePosixPath], default DEFAULT_PROJECT_ROOT
        Project root. The data tree is rooted at ``<project_root>/data``.
    """

    def __init__(
        self,
        city: str,
        project_root: Union[str, PurePosixPath] = DEFAULT_PROJECT_ROOT,
    ) -> None:
        self.city = city
        self.project_root = PurePosixPath(project_root)

    # -- base dirs ----------------------------------------------------------

    @property
    def data(self) -> PurePosixPath:
        """`<project_root>/data`."""
        return self.project_root / "data"

    @property
    def outputs(self) -> PurePosixPath:
        """`data/outputs`."""
        return self.data / "outputs"

    @property
    def cache(self) -> PurePosixPath:
        """`data/cache` (excluded from the deliverable)."""
        return self.data / "cache"

    @property
    def aoi(self) -> PurePosixPath:
        """`data/aoi` (convention slot for AOI outlines)."""
        return self.data / "aoi"

    @property
    def city_dir(self) -> PurePosixPath:
        """`data/outputs/<CITY>` (the legacy ``OUTPUT_DIR``)."""
        return self.outputs / self.city

    def ecoprofil_dir(self, ecoprofil: str) -> PurePosixPath:
        """`data/outputs/<CITY>/<ecoprofil>`."""
        return self.city_dir / ecoprofil

    # -- per-ecoprofil artefacts ------------------------------------------------

    def _g(self, ecoprofil: str, prefix: str, ext: str) -> PurePosixPath:
        """Build `<ecoprofil_dir>/<prefix>_<ecoprofil>_<CITY>.<ext>`."""
        return self.ecoprofil_dir(ecoprofil) / f"{prefix}_{ecoprofil}_{self.city}.{ext}"

    def landcover_tif(self, ecoprofil: str) -> PurePosixPath:
        """Ecoprofil land-cover raster."""
        return self._g(ecoprofil, "landcover", "tif")

    def binary_habitat_tif(self, ecoprofil: str) -> PurePosixPath:
        """Binary habitat raster."""
        return self._g(ecoprofil, "binary_habitat", "tif")

    def friction_tif(self, ecoprofil: str) -> PurePosixPath:
        """Resistance / friction surface raster."""
        return self._g(ecoprofil, "friction", "tif")

    def dispersal_tif(self, ecoprofil: str) -> PurePosixPath:
        """Continuous (unbounded) dispersal-cost surface raster (clipped to the city AOI)."""
        return self._g(ecoprofil, "dispersal", "tif")

    def dispersal_bounded_tif(self, ecoprofil: str) -> PurePosixPath:
        """Dispersal-cost surface cut at the dispersal budget `d0 * FRICTION_AVG_FAVORABLE`
        (CEREMA-like reach; pixels beyond the budget are NaN)."""
        return self._g(ecoprofil, "dispersal_bounded", "tif")

    def edges_geojson(self, ecoprofil: str) -> PurePosixPath:
        """Theoretical graph edges (GeoJSON)."""
        return self._g(ecoprofil, "edges", "geojson")

    def lcp_geojson(self, ecoprofil: str) -> PurePosixPath:
        """Least-cost-path corridors with metrics (GeoJSON)."""
        return self._g(ecoprofil, "lcp", "geojson")

    def failed_links_geojson(self, ecoprofil: str) -> PurePosixPath:
        """Failed links (out_of_reach + blocked + node_not_found), GeoJSON."""
        return self._g(ecoprofil, "failed_links", "geojson")

    def rupture_points_geojson(self, ecoprofil: str) -> PurePosixPath:
        """Rupture points (blocked links x OSM obstacles), GeoJSON."""
        return self._g(ecoprofil, "rupture_points", "geojson")

    def segments_geojson(self, ecoprofil: str) -> PurePosixPath:
        """Corridor segments: corridor portions outside habitat patches, aggregated by overlap (GeoJSON)."""
        return self._g(ecoprofil, "corridor_segments", "geojson")

    def nodes_geojson(self, ecoprofil: str) -> PurePosixPath:
        """Habitat nodes with node-betweenness (GeoJSON)."""
        return self._g(ecoprofil, "nodes", "geojson")

    def isolated_nodes_geojson(self, ecoprofil: str) -> PurePosixPath:
        """Distance-isolated nodes within the city AOI (GeoJSON)."""
        return self._g(ecoprofil, "isolated_nodes", "geojson")

    def stats_csv(self, ecoprofil: str) -> PurePosixPath:
        """Per-ecoprofil KPI statistics (CSV, one row)."""
        return self._g(ecoprofil, "stats", "csv")

    # -- city-level artefacts ----------------------------------------------

    def aoi_limits(self) -> PurePosixPath:
        """Archived AOI outline for the city (written by the notebook)."""
        return self.city_dir / f"aoi_limits_{self.city}.geojson"

    # -- directory creation -------------------------------------------------

    def init(self) -> None:
        """Create the base output directories for the city (idempotent)."""
        from pathlib import Path

        for d in (self.outputs, self.aoi, self.city_dir):
            Path(d).mkdir(parents=True, exist_ok=True)

    def init_ecoprofil(self, ecoprofil: str) -> PurePosixPath:
        """Create the ecoprofil output directory and return it (idempotent)."""
        from pathlib import Path

        gdir = self.ecoprofil_dir(ecoprofil)
        Path(gdir).mkdir(parents=True, exist_ok=True)
        return gdir