"""
corridor_project - centralized output path management (PurePosixPath).

Mirrors the convention reference ``a_b_c_functions/ECCT/ECCT_Paths.py:ProjectPaths``:
pure paths (no I/O when building them) rooted under ``<project_root>/data/``, typed
accessors per output, and an ``init()`` that creates the directories.

Layout (variant B, data/ root rule)::

    <project_root>/data/outputs/<CITY>/<guild>/<artefact>_<guild>_<CITY>.<ext>

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

    def guild_dir(self, guild: str) -> PurePosixPath:
        """`data/outputs/<CITY>/<guild>`."""
        return self.city_dir / guild

    # -- per-guild artefacts ------------------------------------------------

    def _g(self, guild: str, prefix: str, ext: str) -> PurePosixPath:
        """Build `<guild_dir>/<prefix>_<guild>_<CITY>.<ext>`."""
        return self.guild_dir(guild) / f"{prefix}_{guild}_{self.city}.{ext}"

    def landcover_tif(self, guild: str) -> PurePosixPath:
        """Guild land-cover raster."""
        return self._g(guild, "landcover", "tif")

    def binary_habitat_tif(self, guild: str) -> PurePosixPath:
        """Binary habitat raster."""
        return self._g(guild, "binary_habitat", "tif")

    def friction_tif(self, guild: str) -> PurePosixPath:
        """Resistance / friction surface raster."""
        return self._g(guild, "friction", "tif")

    def dispersal_tif(self, guild: str) -> PurePosixPath:
        """Continuous dispersal-cost surface raster (clipped to the city AOI)."""
        return self._g(guild, "dispersal", "tif")

    def edges_geojson(self, guild: str) -> PurePosixPath:
        """Theoretical graph edges (GeoJSON)."""
        return self._g(guild, "edges", "geojson")

    def lcp_geojson(self, guild: str) -> PurePosixPath:
        """Least-cost-path corridors with metrics (GeoJSON)."""
        return self._g(guild, "lcp", "geojson")

    def barriers_geojson(self, guild: str) -> PurePosixPath:
        """Failed corridors (uncrossable barriers), GeoJSON."""
        return self._g(guild, "barriers", "geojson")

    def ruptures_geojson(self, guild: str) -> PurePosixPath:
        """Rupture points (failed corridors x OSM obstacles), GeoJSON."""
        return self._g(guild, "ruptures", "geojson")

    def segments_geojson(self, guild: str) -> PurePosixPath:
        """Aggregated urban-planning segments (GeoJSON)."""
        return self._g(guild, "segments_amenagement", "geojson")

    def nodes_geojson(self, guild: str) -> PurePosixPath:
        """Habitat nodes with node-betweenness (GeoJSON)."""
        return self._g(guild, "nodes", "geojson")

    def isolated_nodes_geojson(self, guild: str) -> PurePosixPath:
        """Distance-isolated nodes within the city AOI (GeoJSON)."""
        return self._g(guild, "isolated_nodes", "geojson")

    def stats_csv(self, guild: str) -> PurePosixPath:
        """Per-guild KPI statistics (CSV, one row)."""
        return self._g(guild, "stats", "csv")

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

    def init_guild(self, guild: str) -> PurePosixPath:
        """Create the guild output directory and return it (idempotent)."""
        from pathlib import Path

        gdir = self.guild_dir(guild)
        Path(gdir).mkdir(parents=True, exist_ok=True)
        return gdir