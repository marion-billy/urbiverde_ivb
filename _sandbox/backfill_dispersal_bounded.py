"""Backfill dispersal_bounded_<guild>_<city>.tif from the existing (unbounded) dispersal_*.tif,
masked at the dispersal budget d0 * FRICTION_AVG_FAVORABLE. Idempotent. No MCP re-run."""
import glob, os, sys
PR = "/home/jovyan/work/team/marion/corridor_project"
ABC = "/home/jovyan/work/team/Hugo/a_b_c_functions"
for p in (f"{PR}/utils", ABC, f"{ABC}/spatial_analysis"): sys.path.insert(1, p)
import rioxarray  # noqa
import species_params as spp
FAV = spp.FRICTION_AVG_FAVORABLE
D0 = {g: c["graph"]["d0"] for g, c in spp.SPECIES_CONFIG.items()}
n = 0
roots = glob.glob(f"{PR}/data/outputs/*/*/") + glob.glob(f"{PR}/data/scenarios/*/*/*/")
for gdir in roots:
    g = os.path.basename(gdir.rstrip("/"))
    if g not in D0: continue
    srcs = [t for t in glob.glob(gdir + "dispersal_*.tif") if "dispersal_bounded" not in os.path.basename(t)]
    if not srcs: continue
    src = srcs[0]
    da = rioxarray.open_rasterio(src)
    bounded = da.where(da <= D0[g] * FAV)
    out = os.path.join(gdir, os.path.basename(src).replace("dispersal_", "dispersal_bounded_", 1))
    bounded.rio.to_raster(out)
    n += 1
print(f"wrote {n} dispersal_bounded rasters")
