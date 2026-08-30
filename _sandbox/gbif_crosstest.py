"""GBIF use-vs-availability cross-test, per-city and pooled, over the 5 temperate cities.

Outputs (in _sandbox/gbif_validation/):
  coverage.csv            : n focal + n target-group per (ecoprofil, city) -> where are the data?
  ratios_per_city.csv     : selection ratio + CI per (ecoprofil, city, class) where n_focal >= MIN_N
  ratios_pooled.csv       : selection ratio + CI per (ecoprofil, class), pooled over cities
Occurrences are cached (WGS84 geojson) so re-runs do not re-hit the API.
"""
import os
import sys

sys.path.insert(1, "utils")
import geopandas as gpd
import numpy as np
import pandas as pd
import species_params as spp
import gbif_validation as gv

CITIES = ["Perpignan", "Toulouse", "Nancy", "LRSY", "LaRochelle"]
GUILDS = list(spp.SPECIES_CONFIG.keys())
CORR_BUF = 25.0
MIN_N = 30          # below this, a per-city ratio is not reported (CI meaningless)
OUT = "_sandbox/gbif_validation"
CACHE = f"{OUT}/cache"
os.makedirs(CACHE, exist_ok=True)

gkeys = {g: [k for k in (gv.taxon_key(s[0]) for s in gv.guild_species(g, spp.SPECIES_CONFIG)) if k]
         for g in GUILDS}


def cached(guild, city, kind, bb, aoi, utm, keys):
    """Fetch (or load cached) filtered+thinned occurrences, returned in the city UTM."""
    path = f"{CACHE}/{guild}_{city}_{kind}.geojson"
    if os.path.exists(path):
        g = gpd.read_file(path)
        return g.to_crs(utm) if len(g) else g
    if kind == "focal":
        raw = gv.fetch_occurrences(bb, taxon_keys=keys, max_records=8000)
    else:
        raw = gv.fetch_occurrences(bb, class_name=gv.TGB_CLASS[guild], max_records=8000)
    g = gv.spatial_thin(gv.filter_occurrences(gv.to_gdf(raw), aoi_wgs=aoi), utm)
    (g.to_crs("EPSG:4326") if len(g) else gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")).to_file(path, driver="GeoJSON")
    return g


def ratios_from_labels(fl, bl, n_boot=1000, seed=0):
    avail = pd.Series(bl).value_counts(normalize=True) if len(bl) else pd.Series(dtype=float)
    rng = np.random.default_rng(seed)
    out = {}
    for cl in gv.CLASSES:
        a = float(avail.get(cl, 0.0))
        u = float((fl == cl).mean()) if len(fl) else np.nan
        ratio = u / a if a > 0 else np.nan
        boots = [((rng.choice(fl, len(fl)) == cl).mean() / a) for _ in range(n_boot)] if (a > 0 and len(fl)) else []
        lo, hi = (np.percentile(boots, [2.5, 97.5]) if boots else (np.nan, np.nan))
        out[cl] = (int((fl == cl).sum()), round(u, 3), round(a, 3), round(ratio, 2), round(lo, 2), round(hi, 2))
    return out


cov, per_city, pooled_rows = [], [], []
for g in GUILDS:
    fl_pool, bl_pool = [], []
    for c in CITIES:
        try:
            nodes = gpd.read_file(f"data/outputs/{c}/{g}/nodes_{g}_{c}.geojson")
        except Exception:
            cov.append({"guild": g, "city": c, "n_focal": 0, "n_tgb": 0})
            continue
        aoi = gpd.read_file(f"data/outputs/{c}/aoi_limits_{c}.geojson").to_crs("EPSG:4326")
        utm = aoi.estimate_utm_crs().to_epsg()
        bb = tuple(aoi.total_bounds)
        cores = nodes[nodes.node_type == "core"].to_crs(utm)
        islets = nodes[nodes.node_type == "islet"].to_crs(utm)
        try:
            lcp = gpd.read_file(f"data/outputs/{c}/{g}/lcp_{g}_{c}.geojson").to_crs(utm)
        except Exception:
            lcp = cores.iloc[0:0]
        focal = cached(g, c, "focal", bb, aoi, utm, gkeys[g])
        bg = cached(g, c, "tgb", bb, aoi, utm, gkeys[g])
        core_u = cores.union_all() if len(cores) else None
        islet_u = islets.union_all() if len(islets) else None
        corr_u = lcp.buffer(CORR_BUF).union_all() if len(lcp) else None
        fl = gv._classify(focal, core_u, islet_u, corr_u) if len(focal) else np.array([])
        bl = gv._classify(bg, core_u, islet_u, corr_u) if len(bg) else np.array([])
        cov.append({"guild": g, "city": c, "n_focal": len(fl), "n_tgb": len(bl)})
        print(f"  {g}/{c}: focal={len(fl)} tgb={len(bl)}", flush=True)
        if len(fl):
            fl_pool.append(fl)
        if len(bl):
            bl_pool.append(bl)
        if len(fl) >= MIN_N and len(bl) >= MIN_N:
            r = ratios_from_labels(fl, bl)
            for cl, v in r.items():
                per_city.append({"guild": g, "city": c, "class": cl, "n_c": v[0],
                                 "use": v[1], "avail": v[2], "ratio": v[3], "ci_lo": v[4], "ci_hi": v[5]})
    fl = np.concatenate(fl_pool) if fl_pool else np.array([])
    bl = np.concatenate(bl_pool) if bl_pool else np.array([])
    r = ratios_from_labels(fl, bl)
    for cl, v in r.items():
        pooled_rows.append({"guild": g, "class": cl, "n_focal_tot": int(len(fl)), "n_c": v[0],
                            "use": v[1], "avail": v[2], "ratio": v[3], "ci_lo": v[4], "ci_hi": v[5]})

pd.DataFrame(cov).to_csv(f"{OUT}/coverage.csv", index=False)
pd.DataFrame(per_city).to_csv(f"{OUT}/ratios_per_city.csv", index=False)
pd.DataFrame(pooled_rows).to_csv(f"{OUT}/ratios_pooled.csv", index=False)

print("\n=== COUVERTURE (n occurrences par profil x ville) ===")
print(pd.DataFrame(cov).pivot(index="city", columns="guild", values="n_focal").to_string())
print("\n=== RATIOS POOLES ===")
print(pd.DataFrame(pooled_rows).to_string(index=False))
print(f"\n=== RATIOS PAR VILLE (n_focal >= {MIN_N}) : {len(per_city)//3} couples (profil,ville) ===")
print(pd.DataFrame(per_city).to_string(index=False))
print("\nOK -> coverage.csv / ratios_per_city.csv / ratios_pooled.csv")
