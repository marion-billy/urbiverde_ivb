"""
Single parameterized runner for the connectivity pipeline. FAST code (PC + segments).

Usage
-----
Baseline -> data/outputs/<City>/<ecoprofil>/...
    python3 utils/run_pipeline.py <City>

Scenario -> data/scenarios/<City>/<project-name-slug>/<ecoprofil>/...  (+ project.geojson, meta.json)
    python3 utils/run_pipeline.py <City> --project <history_dir_or_geojson>
where <history_dir> is a dashboard project folder holding project.geojson (+ meta.json).
The output folder name is the slug of the project's `project_name` (readable), and the
project id stays traceable in the copied meta.json.

Detached launch with a tidy timestamped log:
    cd /home/jovyan/work/team/marion/corridor_project
    setsid bash -c 'python3 utils/run_pipeline.py Nancy \
        > _sandbox/logs/Nancy_$(date +%Y%m%d_%H%M).log 2>&1' </dev/null &

Cities known in CITY_CONFIG: Perpignan, Toulouse, Nancy, Kourou, LRSY, PNR_Ardennes,
LaRochelle, SCOT_PaysYonVie.
"""
import argparse
import json
import os
import re
import shutil
import sys
import time
import unicodedata

os.umask(0)

PROJECT_ROOT = "/home/jovyan/work/team/marion/corridor_project"
ABC = "/home/jovyan/work/team/Hugo/a_b_c_functions"
for p in (os.path.join(PROJECT_ROOT, "utils"), os.path.join(PROJECT_ROOT, "libs"),
          ABC, os.path.join(ABC, "spatial_analysis"), os.path.join(ABC, "gee_with_python")):
    sys.path.insert(1, p)

import ee  # noqa: E402
import geopandas as gpd  # noqa: E402
import rioxarray  # noqa: E402, F401  (registers the .rio accessor + open_rasterio for the LC cache)

import landcover as lc  # noqa: E402
import sp_pipeline  # noqa: E402
import species_params as spp  # noqa: E402
from paths import CorridorPaths  # noqa: E402

# EarthEngine service-account auth. The key path is read from the $GEE_KEY_PATH environment
# variable (no path hard-coded here); the service-account email is read FROM the key file, so no
# credential value is hard-coded either. ee.Initialize(project=...) ADC is not configured in this
# environment, so a service-account key is still required: set GEE_KEY_PATH before running.
CREDENTIALS_PATH = os.environ["GEE_KEY_PATH"]

# AOI source per city: ("url", <geojson url>) | ("boundary", <name>) | ("bbox", (minx,miny,maxx,maxy))
CITY_CONFIG = {
    "Perpignan": ("url", "https://geo.api.gouv.fr/communes/66136?format=geojson&geometry=contour"),
    "Toulouse":  ("boundary", "Toulouse Métropole"),
    "Nancy":     ("url", "https://geo.api.gouv.fr/epcis?nom=Grand%20Nancy&format=geojson&geometry=contour"),
    "Kourou":    ("bbox", (-52.70, 5.10, -52.60, 5.20)),
    "LRSY":      ("url", "https://geo.api.gouv.fr/epcis?code=248500589&format=geojson&geometry=contour"),
    "PNR_Ardennes": ("boundary", "Parc naturel régional des Ardennes"),  # ~1183 km2
    "SCOT_PaysYonVie": ("boundary", "Pays Yon et Vie"),  # SCOT = CA La Roche + CC Vie&Boulogne, ~995 km2
    "LaRochelle": ("url", "https://geo.api.gouv.fr/epcis?code=241700434&format=geojson&geometry=contour"),  # CA de La Rochelle, ~331 km2
}


def slugify(name: str) -> str:
    """ASCII, lower-case, hyphen-separated slug of a project name."""
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "projet"


def load_aoi(city: str) -> gpd.GeoDataFrame:
    """Build the raw AOI GeoDataFrame for a known city."""
    kind, value = CITY_CONFIG[city]
    if kind == "url":
        return gpd.read_file(value)
    if kind == "boundary":
        from OSM.get_boundary import get_boundary
        return get_boundary(value)
    if kind == "bbox":
        from shapely.geometry import box
        return gpd.GeoDataFrame(geometry=[box(*value)], crs="EPSG:4326")
    raise ValueError(f"unknown AOI kind {kind!r}")


def burn_polygon(lc_wc, polygon_path: str):
    """Burn a project polygon's class_code into a copy of the WorldCover land-cover."""
    from rasterio.features import rasterize
    change = gpd.read_file(polygon_path).to_crs(lc_wc.rio.crs)
    shapes = [(geom, int(code)) for geom, code in zip(change.geometry, change["class_code"])]
    burned = rasterize(shapes, out_shape=lc_wc.shape[-2:], transform=lc_wc.rio.transform(), fill=0, dtype="int16")
    lc_wc_mod = lc_wc.copy()
    m = burned != 0
    lc_wc_mod.values[..., m] = burned[m]
    print(f"Burned classes {sorted(set(change['class_code']))} into {int(m.sum())} pixels.", flush=True)
    return lc_wc_mod, int(m.sum())


def resolve_project(project_arg: str):
    """Return (polygon_path, meta_path_or_None, project_name) from a history dir or a .geojson."""
    if os.path.isdir(project_arg):
        poly = os.path.join(project_arg, "project.geojson")
        meta = os.path.join(project_arg, "meta.json")
        meta = meta if os.path.exists(meta) else None
    else:
        poly, meta = project_arg, None
    name = os.path.splitext(os.path.basename(poly))[0]
    gj = gpd.read_file(poly)
    if "project_name" in gj.columns and gj["project_name"].notna().any():
        name = str(gj["project_name"].dropna().iloc[0])
    return poly, meta, name


def main() -> None:
    """Parse args, set up the city, optionally burn a project polygon, run every ecoprofil."""
    ap = argparse.ArgumentParser()
    ap.add_argument("city", choices=sorted(CITY_CONFIG))
    ap.add_argument("--project", help="dashboard history dir (project.geojson [+meta.json]) or a .geojson; scenario mode")
    ap.add_argument("--ecoprofil", choices=sorted(spp.SPECIES_CONFIG),
                    help="run only this ecoprofil (default: all). Useful for targeted re-tests.")
    ap.add_argument("--friction-scale", type=float, default=None,
                    help="sensitivity: multiply every friction value by this factor (NaN barriers kept).")
    ap.add_argument("--friction-class", type=int, default=None,
                    help="sensitivity: restrict --friction-scale to this single land-cover code "
                         "(e.g. 10 for tree cover); default applies it to every class.")
    ap.add_argument("--friction-contrast", type=float, default=None,
                    help="sensitivity: rescale the CONTRAST between classes around the habitat pivot 1: "
                         "friction' = 1 + (friction - 1) * k. k=0 flattens all contrasts, k=1 is the "
                         "reference, k>1 amplifies. Tests what drives the least-cost routing (the gaps "
                         "between frictions), not their absolute level.")
    ap.add_argument("--d0-scale", type=float, default=None,
                    help="sensitivity: multiply each ecoprofil dispersal distance d0 by this factor.")
    ap.add_argument("--out-tag", default=None,
                    help="sensitivity: write baseline-style outputs under _sandbox/sensitivity/<out-tag>/<City>/ "
                         "instead of data/outputs/ (keeps the reference run intact).")
    ap.add_argument("--lc-cache", action="store_true",
                    help="reuse a cached land cover per (city, buffer) instead of re-fetching Earth "
                         "Engine each run; builds the cache on first use. The land cover is identical "
                         "across a city's sensitivity/scenario runs, so this skips the slow, hang-prone "
                         "download. Falls back to a download if the cache is missing or unreadable.")
    ap.add_argument("--refresh-lc", action="store_true",
                    help="with --lc-cache, force a fresh Earth Engine download and rewrite the cache.")
    args = ap.parse_args()

    city = args.city
    t_all = time.perf_counter()

    # Edge buffer is pinned to the UNSCALED max d0 (captured before any sensitivity perturbation). The
    # buffer must always cover the longest reach (d0 x 3), so shrinking it with a reduced-d0 sweep would
    # under-correct the edge effect. Pinning it also keeps the land-cover query (buffered extent)
    # identical across all d0 variants, so they reuse the baseline's cached OSM/WorldCover instead of
    # issuing new Overpass queries, which hang on dense cities. The d0 used inside the model still
    # varies with the sweep; only the AOI extent is fixed.
    max_d0_ref = max(s["graph"]["d0"] for s in spp.SPECIES_CONFIG.values())

    # Sensitivity mode: perturb the (subjective) inputs in memory before any run. sp_pipeline reads
    # spp.SPECIES_CONFIG at call time, so rebinding it here propagates. Process-local (fresh process
    # per invocation): the reference config on disk is untouched.
    if args.friction_scale or args.d0_scale or args.friction_contrast is not None:
        import copy
        import math
        cfg = copy.deepcopy(spp.SPECIES_CONFIG)
        for v in cfg.values():
            if args.friction_scale:
                only = args.friction_class  # None -> all classes; else this single land-cover code
                v["friction"] = {c: (f if (isinstance(f, float) and math.isnan(f))
                                     else (f * args.friction_scale if (only is None or c == only) else f))
                                 for c, f in v["friction"].items()}
            if args.friction_contrast is not None:
                k = args.friction_contrast  # friction' = 1 + (friction - 1) * k, pivot on the habitat (1)
                v["friction"] = {c: (f if (isinstance(f, float) and math.isnan(f)) else 1.0 + (f - 1.0) * k)
                                 for c, f in v["friction"].items()}
            if args.d0_scale:
                v["graph"]["d0"] = v["graph"]["d0"] * args.d0_scale
        spp.SPECIES_CONFIG = cfg
        scope = f" (class {args.friction_class} only)" if args.friction_class is not None else ""
        print(f"SENSITIVITY: friction x{args.friction_scale}{scope}, contrast k={args.friction_contrast}, "
              f"d0 x{args.d0_scale}", flush=True)

    if args.project:
        poly, meta, name = resolve_project(args.project)
        slug = slugify(name)
        stage = os.path.join(PROJECT_ROOT, "data", "scenarios", city, slug)
        OUTPUT_DIR = os.path.join(stage, "data", "outputs", city)  # sp_pipeline reconstructs this layout
        mode = f"scenario '{name}' -> data/scenarios/{city}/{slug}"
    else:
        poly = meta = None
        stage = None
        if args.out_tag:
            # Mirror the scenario layout so sp_pipeline's parents[2] root-derivation lands on the
            # tag dir (it expects <root>/data/outputs/<city>); otherwise it writes to data/data/outputs.
            OUTPUT_DIR = os.path.join(PROJECT_ROOT, "_sandbox", "sensitivity", args.out_tag, city)
            mode = f"sensitivity[{args.out_tag}] -> {OUTPUT_DIR}"
        else:
            OUTPUT_DIR = str(CorridorPaths(city).city_dir)
            mode = f"baseline -> {OUTPUT_DIR}"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"=== {city} | {mode} | {time.ctime()} ===", flush=True)

    aoi_raw = load_aoi(city)
    # Baseline only: write the analysis AOI once at the city root (like the notebook), the
    # boundary overlay shared by every ecoprofil. Scenarios don't need it.
    if not args.project:
        aoi_raw.to_file(os.path.join(OUTPUT_DIR, f"aoi_limits_{city}.geojson"), driver="GeoJSON")
    max_d0 = max_d0_ref  # pinned buffer (see above): unscaled, so d0 sweeps reuse the cached land cover

    # Land-cover cache (opt-in via --lc-cache). WorldCover + OSM depend only on the city and the
    # buffered extent (2*max_d0), never on the ecoprofil or the friction/d0 perturbation, so they are
    # cached once per (city, buffer) and reloaded: sensitivity and scenario runs then skip Earth
    # Engine entirely (the download is the slow, hang-prone step). The key carries the buffer because
    # a d0 scaling changes the extent. --refresh-lc forces a rewrite; a cache-read error falls back to
    # a fresh download, so the cache is never a single point of failure.
    buf_m = int(round(2 * max_d0))
    lc_cache_dir = os.path.join(PROJECT_ROOT, "data", "lc_cache", f"{city}_{buf_m}")
    wc_cache = os.path.join(lc_cache_dir, "lc_wc.tif")
    osm_cache = os.path.join(lc_cache_dir, "lc_osm.parquet")

    # Earth Engine must be initialized for EVERY run, not only on a land-cover fetch: sp_pipeline still
    # calls ee.Geometry downstream (AOI handling), so a cache-hit run that skipped ee.Initialize died
    # with "client library not initialized" (silent-empty output, exit 0). Init is idempotent and cheap.
    with open(CREDENTIALS_PATH) as _kf:
        service_account = json.load(_kf)["client_email"]
    ee.Initialize(ee.ServiceAccountCredentials(service_account, CREDENTIALS_PATH))

    lc_wc = lc_osm = None
    if args.lc_cache and not args.refresh_lc and os.path.exists(wc_cache) and os.path.exists(osm_cache):
        try:
            lc_wc = rioxarray.open_rasterio(wc_cache).squeeze("band", drop=True).load()
            lc_osm = gpd.read_parquet(osm_cache)
            print(f"Land-cover from cache (Earth Engine skipped): {lc_cache_dir}", flush=True)
        except Exception as e:
            print(f"Land-cover cache unreadable ({e!r}); re-downloading.", flush=True)
            lc_wc = lc_osm = None
    if lc_wc is None:
        aoi_utm, aoi_ee, utm_epsg = lc.setup_aoi(aoi_raw)
        print(f"AOI area: {aoi_utm.area.sum() / 1e6:.1f} km2", flush=True)
        master_buffered_geom = gpd.GeoSeries(aoi_utm.buffer(2 * max_d0), crs=utm_epsg).to_crs(aoi_raw.crs)
        master_aoi_buffered = aoi_raw.copy()
        master_aoi_buffered.geometry = master_buffered_geom
        master_aoi_buffered = master_aoi_buffered.dissolve()
        master_aoib_utm, master_aoib_ee, master_utmb_epsg = lc.setup_aoi(master_aoi_buffered)
        lc_wc, lc_osm = lc.download_lc_data(master_aoib_ee, master_aoib_utm, master_aoi_buffered, master_utmb_epsg)
        print("Land-cover downloaded.", flush=True)
        if args.lc_cache:
            try:
                os.makedirs(lc_cache_dir, exist_ok=True)
                lc_wc.rio.to_raster(wc_cache)
                lc_osm.to_parquet(osm_cache)
                os.system(f"chmod -R a+rwX {lc_cache_dir} 2>/dev/null")
                print(f"Land-cover cached: {lc_cache_dir}", flush=True)
            except Exception as e:
                print(f"Land-cover cache write failed ({e!r}); continuing.", flush=True)

    if args.project:
        lc_wc, npix = burn_polygon(lc_wc, poly)
        if npix == 0:
            print("ABORT: 0 pixels modified (polygon outside the raster or empty).", flush=True)
            return
        # Make the burned scenario class win over EVERYTHING: on the project footprint, also erase the
        # OSM infrastructure. Otherwise generate_ecoprofil_landcover re-stamps roads/buildings (codes
        # 50-55/80) on top of the burned WorldCover, so a "vegetalized" avenue stays a road and only
        # its verges turn to habitat. Clipping OSM out of the footprint models the intended action
        # (vegetalize / pedestrianize: remove the road AND buildings, then set the veg class).
        if not lc_osm.empty:
            proj_osm = gpd.read_file(poly).to_crs(lc_osm.crs).union_all()
            lc_osm = lc_osm.copy()
            lc_osm["geometry"] = lc_osm.geometry.difference(proj_osm)
            lc_osm = lc_osm[lc_osm.geometry.notna() & ~lc_osm.geometry.is_empty].copy()
            print(f"OSM cleared on the project footprint ({len(lc_osm)} features kept).", flush=True)

    ecoprofils = [args.ecoprofil] if args.ecoprofil else list(spp.SPECIES_CONFIG.keys())
    for ecoprofil_key in ecoprofils:
        t0 = time.perf_counter()
        print(f"\n===== ECOPROFIL {ecoprofil_key} ({time.ctime()}) =====", flush=True)
        try:
            sp_pipeline.sp_pipeline(ecoprofil_key, aoi_raw, city, OUTPUT_DIR, lc_wc, lc_osm)
            print(f"  done {ecoprofil_key} in {(time.perf_counter() - t0) / 60:.1f} min", flush=True)
            from output_check import check_output_dir  # automated output check (report 2.6)
            _ok, _pb = check_output_dir(os.path.join(OUTPUT_DIR, ecoprofil_key))
            print(f"  contrôle sorties : {'conforme' if _ok else 'ANOMALIES -> ' + ' ; '.join(_pb)}", flush=True)
        except Exception as e:
            print(f"  ERROR {ecoprofil_key}: {e!r}", flush=True)

    # Scenario: flatten data/scenarios/<City>/<slug>/data/outputs/<City>/<ecoprofil> -> .../<slug>/<ecoprofil>
    # and drop the provenance files next to the ecoprofil folders. Overwrite any existing ecoprofil
    # folder (so re-running a scenario in place is clean), and skip copying project.geojson /
    # meta.json onto themselves (re-run with --project pointing at the scenario dir itself).
    if args.project:
        for entry in os.listdir(OUTPUT_DIR):
            dest = os.path.join(stage, entry)
            if os.path.isdir(dest):
                shutil.rmtree(dest)
            elif os.path.exists(dest):
                os.remove(dest)
            shutil.move(os.path.join(OUTPUT_DIR, entry), dest)
        shutil.rmtree(os.path.join(stage, "data"), ignore_errors=True)
        dest_poly = os.path.join(stage, "project.geojson")
        if os.path.abspath(poly) != os.path.abspath(dest_poly):
            shutil.copy(poly, dest_poly)
        if meta:
            dest_meta = os.path.join(stage, "meta.json")
            if os.path.abspath(meta) != os.path.abspath(dest_meta):
                shutil.copy(meta, dest_meta)
        final = stage
    else:
        final = OUTPUT_DIR

    print(f"\n=== {city} | {mode} | finished in {(time.perf_counter() - t_all) / 60:.1f} min ===", flush=True)
    print(f"Outputs: {final}", flush=True)


if __name__ == "__main__":
    main()
