"""Backfill the city-level aoi_limits_<city>.geojson at each output/scenario ROOT (once per city,
like the notebook / what run_pipeline now writes). Idempotent.

Usage: python3 _sandbox/backfill_aoi.py [baselines|scenarios]   (default: baselines)
"""
import glob
import os
import sys

PR = "/home/jovyan/work/team/marion/corridor_project"
ABC = "/home/jovyan/work/team/Hugo/a_b_c_functions"
sys.path.insert(0, f"{PR}/utils")  # run_pipeline.py now lives in utils/
for p in (f"{PR}/utils", ABC, f"{ABC}/spatial_analysis", f"{ABC}/gee_with_python"):
    sys.path.insert(1, p)

from run_pipeline import CITY_CONFIG, load_aoi  # noqa: E402

mode = sys.argv[1] if len(sys.argv) > 1 else "baselines"
_cache = {}
def aoi(city):
    if city not in _cache:
        _cache[city] = load_aoi(city)
    return _cache[city]

targets = []  # (root_dir, city)
if mode == "baselines":
    for cdir in sorted(glob.glob(f"{PR}/data/outputs/*/")):
        city = os.path.basename(cdir.rstrip("/"))
        if city in CITY_CONFIG:
            targets.append((cdir, city))
else:  # scenarios: data/scenarios/<City>/<slug>/
    for sdir in sorted(glob.glob(f"{PR}/data/scenarios/*/*/")):
        city = sdir.split("/data/scenarios/")[1].split("/")[0]
        targets.append((sdir, city))

for root, city in targets:
    out = os.path.join(root, f"aoi_limits_{city}.geojson")
    aoi(city).to_file(out, driver="GeoJSON")
    print("wrote", out.replace(PR + "/", ""))
print(f"done [{mode}]: {len(targets)} city roots ({len(_cache)} cities)")
