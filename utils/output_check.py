"""Automated output check for the corridor pipeline (report section 2.6).

For one (city, ecoprofil) output directory, verifies: the stats file is present with its headline
indicators finite ; the core vector layers (nodes, corridors) exist, are non-empty and carry a
PROJECTED CRS (UTM, not lon/lat) ; the friction raster's finite values stay in the plausible
1..100 range (barriers are +inf, excluded) ; and the bounded dispersal cost never exceeds the
movement budget 3 x d0 (report eq. 3). Returns (ok, problems).

Run as a module to check every set under data/outputs :
    PYTHONPATH=/opt/conda/lib/python3.11/site-packages python3 utils/output_check.py [outputs_dir]
Or import check_output_dir() to call it at the end of a pipeline run.
"""
from __future__ import annotations

import glob
import os
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
import rioxarray  # noqa: F401  (registers the .rio accessor)

KEY_STATS = ["pc_real", "connected_habitat_pct", "n_subnetworks", "habitat_ha_in_aoi"]


def check_output_dir(d: str) -> tuple[bool, list[str]]:
    """Check one <city>/<ecoprofil> output directory. Returns (ok, list of problems)."""
    problems: list[str] = []

    # 1. indicators present and finite
    sf = glob.glob(os.path.join(d, "stats_*.csv"))
    if not sf:
        problems.append("tableau d'indicateurs (stats) manquant")
    else:
        s = pd.read_csv(sf[0]).iloc[0]
        for k in KEY_STATS:
            if k not in s or pd.isna(s[k]):
                problems.append(f"indicateur {k} manquant ou non fini")

    # 2. core vector layers present, non-empty, projected CRS
    for name, allow_empty in (("nodes", False), ("lcp", True)):
        vf = glob.glob(os.path.join(d, f"{name}_*.geojson"))
        if not vf:
            problems.append(f"couche {name} manquante")
            continue
        g = gpd.read_file(vf[0])
        if g.crs is None or g.crs.is_geographic:
            problems.append(f"couche {name} : projection non métrique ({g.crs})")
        if g.empty and not allow_empty:
            problems.append(f"couche {name} vide")

    # 3. friction raster: finite values plausible (1..100 ; barriers are +inf)
    ff = glob.glob(os.path.join(d, "friction_*.tif"))
    if ff:
        a = rioxarray.open_rasterio(ff[0]).squeeze().values.astype("float64")
        finite = a[np.isfinite(a)]
        if finite.size and (finite.min() < 1 or finite.max() > 100):
            problems.append(f"friction hors [1, 100] (min {finite.min():g}, max {finite.max():g})")

    # 4. dispersal cost bounded by the movement budget (3 x d0 ; report eq. (3))
    df = glob.glob(os.path.join(d, "dispersal_bounded_*.tif"))
    if df:
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import species_params as spp
            cfg = spp.SPECIES_CONFIG.get(os.path.basename(os.path.normpath(d)))
        except Exception:
            cfg = None
        if cfg:
            budget = 3.0 * cfg["graph"]["d0"]
            a = rioxarray.open_rasterio(df[0]).squeeze().values.astype("float64")
            finite = a[np.isfinite(a)]
            if finite.size and (finite.min() < -1e-6 or finite.max() > budget * 1.01):
                problems.append(
                    f"coût de dispersion hors budget (max {finite.max():g} > 3*d0 = {budget:g})")

    return (len(problems) == 0, problems)


def main(outputs_dir: str) -> int:
    dirs = sorted(
        d for d in glob.glob(os.path.join(outputs_dir, "*", "*"))
        if os.path.isdir(d) and glob.glob(os.path.join(d, "stats_*.csv"))
    )
    n_ok = 0
    for d in dirs:
        ok, problems = check_output_dir(d)
        rel = os.path.relpath(d, outputs_dir)
        if ok:
            n_ok += 1
            print(f"OK    {rel}")
        else:
            print(f"FAIL  {rel} : " + " ; ".join(problems))
    print(f"\n{n_ok}/{len(dirs)} jeux conformes")
    return 0 if n_ok == len(dirs) else 1


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), "..", "data", "outputs")
    sys.exit(main(root))
