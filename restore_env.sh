#!/bin/bash
# restore_env.sh - reinstall the Python deps the corridor pipeline (and report build) need.
#
# Why: this container is ephemeral. On restart, everything outside /home/jovyan/work (NFS) is
# wiped, including pip-installed packages. The base conda image restores most of the geo stack
# (geopandas, rasterio, scikit-image, networkx, rioxarray, earthengine-api, xee, matplotlib,
# shapely, scipy), but NOT osmnx -- and run_pipeline.py imports it at module load (via
# landcover.py / OSM.get_boundary), so the pipeline dies immediately without this.
#
# Run this after any container restart, then relaunch a run:
#     bash restore_env.sh
#     python3 utils/run_pipeline.py <City>
#
# Distribution name vs import name that differ:  python-docx -> docx
# Installed one-by-one on purpose: pip aborts the whole batch if a single name fails to resolve.
# No version pins and NO forced geopandas upgrade: the base image already ships geopandas >=1.0
# (union_all / str()-on-export path the code relies on); re-pinning here risks a needless churn.

set -u
PIP="/opt/conda/bin/pip"
PY="/opt/conda/bin/python"

# Required for the pipeline to import + run:
PKGS_PIPELINE=(osmnx)
# Optional, only needed to build the internship report (papier/internship_report/build_*.py):
PKGS_REPORT=(python-docx xhtml2pdf)

echo "=== pipeline deps (required) ==="
for p in "${PKGS_PIPELINE[@]}"; do
    "$PIP" install --no-input "$p" >/dev/null 2>&1 && echo "  OK   $p" || echo "  FAIL $p"
done

echo "=== report-build deps (optional) ==="
for p in "${PKGS_REPORT[@]}"; do
    "$PIP" install --no-input "$p" >/dev/null 2>&1 && echo "  OK   $p" || echo "  FAIL $p (non-blocking: only needed to rebuild the report)"
done

echo "=== import check: full pipeline chain ==="
"$PY" - <<'PYEOF'
import sys
PR = "/home/jovyan/work/team/marion/corridor_project"
ABC = "/home/jovyan/work/team/Hugo/a_b_c_functions"
for p in (PR + "/utils", PR + "/libs", ABC, ABC + "/spatial_analysis", ABC + "/gee_with_python"):
    sys.path.insert(1, p)
missing = []
# The exact chain run_pipeline.py loads, plus the report-build imports (optional).
checks = [
    ("osmnx", True), ("landcover", True), ("sp_pipeline", True),
    ("species_params", True), ("routing", True), ("connectivity", True),
    ("docx", False), ("xhtml2pdf", False),
]
for mod, required in checks:
    try:
        __import__(mod)
    except Exception as e:
        missing.append((mod, required, type(e).__name__))
# get_boundary lives under a subpackage
try:
    from OSM.get_boundary import get_boundary  # noqa: F401
except Exception as e:
    missing.append(("OSM.get_boundary", True, type(e).__name__))

req_missing = [m for m, r, _ in missing if r]
print("  missing:", [f"{m}({t})" for m, r, t in missing] or "none")
print("  STATUS :", "PIPELINE ENV OK" if not req_missing else f"PIPELINE BROKEN -> {req_missing}")
PYEOF
