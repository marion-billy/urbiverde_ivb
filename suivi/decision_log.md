# decision_log.md : corridor_project

> Append-only project decision log. Instantiated by retrofit on 2026-06-09.
> Traces technical decisions. Convention contract: `A_Structure_convention/CLAUDE.md`.

---

## Retroactive scoping (Phase 0, reconstructed)

- **Owner**: Marion. Deliverable accountability is human (see CLAUDE.md hard rules).
- **Goal**: map urban ecological connectivity (Trame Verte et Bleue, brand "TVB.urban")
  from global satellite observation, per functional guild, and derive corridors usable
  for urban planning.
- **Project type**: exploratory leaning toward scoped (multi-city). **Convention variant: B
  (indicator)**: spatialized indicators (PC, dPC, EBC, pinch points, tortuosity) + per-entity
  dashboard layers.
- **Study areas (5)**: Toulouse, Nancy, Perpignan, Kourou (French Guiana), LRSY
  (La Roche-sur-Yon). One orchestration notebook per city (`<city>_prod.ipynb`).
- **Guilds (5, active)**: ground_mammal, arboreal_mammal, forest_edge_bird, ground_reptile,
  herbaceous_insect. Functional-guild approach (not focal-species, not CEREMA sub-trame).
- **Inputs**: ESA WorldCover v200 (10 m, via Earth Engine) + OSM (OSMnx: roads, rail,
  buildings, water). CosIA (IGN) was a validation-reference side track (since removed).
- **Target CRS**: local UTM per AOI (`get_utm_epsg`), metric, for all distance/raster work.

## Key technical decisions (embedded in code, reconstructed)

- **Habitat morphology**: fast MSPA by binary erosion (`scipy.ndimage`), cores >= 1 ha core
  area, small-core stepping stones >= 0.1 ha. `[Certain]`
- **Graph model**: Gabriel graph on edge-to-edge distances, `max_dist = 2*d0`. Chosen over
  KNN/RNG (both kept commented in `utils/connectivity.py`) for alternative-path retention. `[Certain]`
- **Link probability**: `exp(-d/d0)`, cost `-log(prob)` for Dijkstra. `[Certain]`
- **LCP**: `skimage.MCP_Geometric` over a friction surface; barriers encoded `np.nan -> np.inf`;
  cost threshold `d0 * FRICTION_AVG_FAVORABLE` (=3) recategorizes too-costly links as failed. `[Certain]`
- **Frictions**: calibrated on CEREMA La Rochelle 2025 (pp.96-98), distances Tab.8 p44.
  Habitat forced to friction 1. Chimera guilds (no CEREMA ref) disabled. `[Certain]`
- **Known limits** (documented in `utils/species_params.py` docstring): rail aggregated with
  motorways (code 52), water (80) treated as barrier for terrestrial guilds, no sub-class
  granularity, field validation not implemented. `[Certain]`

## Open points to verify (flagged, not yet resolved)

- **PC > 1** on some city/guild configs (Nancy 5.9, Perpignan 10.2 for ground_mammal): the
  normalization `pc_sum / total_area_km2**2` can exceed 1 when summed patch area is large
  relative to the strict AOI. To confirm against scoping definition of the AOI. `[Assumption]`
- **AOI handling**: `aoi_limits_<city>.geojson` is currently written inside
  `data/outputs/<city>/`, not in the convention `data/aoi/` slot (would need a code change in
  the notebooks). Left as-is; `data/aoi/` reserved for later. `[Certain]`
- **`safe_smooth` duplication**: `utils/routing.py:178` defines a local `safe_smooth` while
  `utils/sp_pipeline.py` imports the canonical one from
  `a_b_c_functions/spatial_analysis/utils_polygon_smoothing`. Shadowing to resolve. `[Certain]`

---

## 2026-06-09 : convention retrofit + non-destructive cleanup

Branched the convention onto the project (variant B) and cleaned the layout. **No file
deleted** (engineer instruction: keep old trials). All flagged dead material moved to
`_sandbox/deprecated/`.

**Moves applied** (validated by engineer, item by item):
- `results_connectivity/` -> `data/outputs/` (data/ root rule).
- `cache/` (5.2 GB) -> `data/cache/` (excluded from deliverable).
- `modules/` -> `utils/` (project-specific functions imported by the notebooks).
- `config/species_params.py` -> `utils/`; rest of `config/` (old versions + caches) ->
  `_sandbox/deprecated/config_old/`.
- `old/` (7 obsolete notebooks) -> `_sandbox/deprecated/old_notebooks/`.
- `results_connectivity/<city>/old_chimeras/` (x5) -> `_sandbox/deprecated/old_chimeras_<city>/`.
- `nancy_prod_clean.ipynb`, `nancy_prod_clean (1).ipynb`, `toimplement.ipynb` ->
  `_sandbox/deprecated/`.

**Done earlier by the engineer** (reported): deleted `app/` (desynced Dash prototype) and
`data/cosia/` (unused validation reference).

**Path patches** (so the pipeline still runs after the moves):
- `utils/sp_pipeline.py`: `sys.path` to `config/` and `modules/` -> `utils/`.
- 5 active notebooks (`kourou/lrsy/nancy/perpignan/tlse_prod.ipynb`): `OUTPUT_DIR`
  `.../results_connectivity/{CITY}` -> `.../data/outputs/{CITY}`; `sys.path` `modules/` and
  `config/` -> `utils/`. Verified: no stale `results_connectivity` / `modules/` / `config/`
  ref remains in the active notebooks.

**Not touched**: `my_custom_libs/` (6.2 GB vendored env, needed for `geoai`); commented-out
dead functions inside `utils/*.py` (kept as trials per engineer instruction).

**Verification**: `python -c import species_params` resolves from `utils/` (5 guilds listed);
`suivi/data_tree.json` regenerated on the clean tree.

## 2026-06-09 : centralized output paths (CorridorPaths)

Replaced the hardcoded output f-strings in `utils/sp_pipeline.py` with a typed path
manager `utils/paths.py:CorridorPaths`, modeled on the convention reference
`a_b_c_functions/ECCT/ECCT_Paths.py:ProjectPaths` (**`PurePosixPath`**, pure path building +
`init()` for directory creation; the stack is posix-only).

- 12 per-guild artefact accessors (`landcover_tif`, `binary_habitat_tif`, `friction_tif`,
  `dispersal_tif`, `edges_json`, `lcp_json`, `barriers_json`, `ruptures_json`, `segments_json`,
  `nodes_geojson`, `isolated_nodes_geojson`, `stats_json`) + `aoi_limits()` + `init_guild()`.
- `sp_pipeline()` builds `CorridorPaths(CITY, project_root=PurePosixPath(OUTPUT_DIR).parents[2])`,
  so the **5 notebooks stay unchanged** (still pass the legacy `OUTPUT_DIR = <root>/data/outputs/{CITY}`).
- Verified: every accessor is byte-identical to the previous f-string path (outputs land in
  the same place); `py_compile` OK.

**Scope**: only the data/output side. The `sys.path.insert` import hacks (a_b_c_functions,
`my_custom_libs`) are a packaging concern, intentionally left untouched (not solved by a path
manager). The `my_custom_libs` absolute path remains the main hardcoded-path offender.

Note: the `Hardcoded paths` table in `suivi/audit_report.md` is dominated by false positives
from vendored deps under `my_custom_libs/` (third-party test fixtures); only the `utils/*.py`
`sys.path` lines and the `my_custom_libs` absolute path are real.

## 2026-06-09 : notebooks on CorridorPaths + drop .json outputs

- **Notebooks use CorridorPaths**: the 5 active notebooks now set
  `from paths import CorridorPaths; OUTPUT_DIR = str(CorridorPaths(CITY).city_dir)` instead of a
  hardcoded `OUTPUT_DIR = f"/home/jovyan/.../data/outputs/{CITY}"`. Verified the `utils/`
  `sys.path` insert precedes the `OUTPUT_DIR` line in every notebook (import resolves).
  `sp_pipeline()` still derives the root from the passed `OUTPUT_DIR`, so it stays compatible.
- **No more `.json` outputs**: geometry layers now `.geojson` (edges, lcp, barriers, ruptures,
  segments), KPI stats now `.csv` (`pd.DataFrame([stats]).to_csv(..., index=False)` via the new
  `paths.stats_csv()`). Accessors renamed accordingly (`*_geojson`, `stats_csv`). Dropped the
  unused `import json` / `json.dump` from `sp_pipeline.py`, added `import pandas as pd`.
  Rationale: `.json` was a misnomer (the GeoJSON layers were written with driver='GeoJSON' but a
  `.json` suffix); tabular KPIs belong in CSV.
- **Backward note**: pre-existing `.json` results already on disk in `data/outputs/` are left in
  place (not deleted); a re-run writes the new `.geojson`/`.csv` next to them.
- Verified: `py_compile` OK; accessors produce the expected `.geojson`/`.csv` names; no `.json`
  write or `json.*` ref remains in `sp_pipeline.py`.

## 2026-06-09 : drop geoai / my_custom_libs (6.6 GB -> 60 KB)

`my_custom_libs/` (6.6 GB, on NFS) existed only to provide `geoai.smooth_vector`, which is a
thin wrapper around the `smoothify` package (`smoothify(geom=..., smooth_iterations=3,
preserve_area=True, ...)`, same defaults). geoai's PyTorch/CUDA/Lightning stack was 100% unused.

- **`utils/routing.py`**: `import geoai` -> `from smoothify import smoothify`; the 2 active
  `geoai.smooth_vector(X, **kwargs)` -> `smoothify(geom=X, **kwargs)` (behaviorally identical).
  Removed the dead, shadowed `from utils_polygon_smoothing import safe_smooth` import (the module
  defines its own `safe_smooth`), which also pulled geoai. `custom_dir` now points to `./libs`.
- **`utils/sp_pipeline.py`**: dropped `from utils_polygon_smoothing import safe_smooth` (geoai-
  dependent canonical, in a_b_c_functions); node smoothing now uses `rout.safe_smooth`
  (smoothify-based, index-preserving -> safer for the node-ID mapping). a_b_c_functions itself is
  NOT modified (engineer instruction), only no longer imported.
- **5 notebooks**: `custom_dir` `my_custom_libs` -> `libs`; commented `%pip` line slimmed to
  `smoothify --no-deps`; the stray `import geoai` cell in `perpignan_prod.ipynb` commented out.
- **Dependency**: `smoothify==0.2.3` installed into `./libs` (60 KB) via
  `pip install -r requirements.txt --no-deps --target=libs` (its deps geopandas/scipy/shapely/
  numpy/joblib are already in the base env). `libs/` is on NFS so it survives the ephemeral
  container. `requirements.txt` pins it.
- **Deleted `my_custom_libs/`** (engineer-authorized, nothing imports it anymore). Verified: no
  active geoai / my_custom_libs import in `utils/*.py` or the notebooks; `smoothify` smooths
  polygons and lines from `./libs` in a standalone test.
- **Residual**: ~10 `my_custom_libs/.nfs*` ghost files held open by a long-running Jupyter
  kernel (NFS silly-rename). They clear when that kernel is restarted or on container reboot;
  then `rm -rf my_custom_libs` removes the empty shell. ~6.5 of 6.6 GB already reclaimed.

This also resolves the `safe_smooth` shadowing flagged earlier (sp_pipeline no longer pulls the
canonical geoai-based one; routing uses its own).

## 2026-06-09 : convention pass on utils/*.py (docstrings, types, English)

Applied the code conventions to the **active code** of every `utils/*.py`. Originals backed up
to `_sandbox/_convention_backup_20260609/`.

- **Language (hard rule)**: translated all French docstrings/comments/strings in active code to
  English. `species_params.py` is the exception (engineer choice "not the science"): its French
  scientific prose / guild descriptions are kept; only em-dashes removed and the 2 helper
  functions typed/documented.
- **Em-dash (hard rule)**: removed all 10 (species_params) -> hyphen; 0 remain anywhere.
- **Docstrings / typing**: numpy docstrings + type hints added (landcover fully; routing,
  sp_pipeline, vizu_ind, paths done; connectivity: English docstrings + missing signatures typed).
- **Unicode**: normalized math/punctuation in code (x, ->, ^2, *) to ASCII.
- **Verification**: every file `py_compile` OK and **AST-identical** to the backup once
  docstrings/annotations/string-literals are ignored (logic provably unchanged). The ✓ emoji in
  `sp_pipeline` progress print is kept (convention encourages emoji in progress prints).

Remaining (minor, not done):
- Large **commented-out dead blocks** (connectivity ~600 lines, routing/vizu tails) kept in
  French (dead trials, consistent with the keep-trials rule; not active code).
- (resolved) connectivity Google-style docstrings -> all converted to numpy.

## 2026-06-09 : airports / stadiums no longer counted as habitat (landcover.py)

Problem: WorldCover maps the grass of airfields and stadium/sports pitches as grassland
(code 30), so open-ground guilds (`ground_reptile`, `herbaceous_insect`, `ground_mammal`)
treated secured runways and mowed pitches as habitat.

Fix in `utils/landcover.py:download_lc_data`:
- OSM query extended with `aeroway` (`aerodrome, runway, taxiway, apron, helipad`) and
  `leisure` (`stadium, pitch, track, sports_centre`). Polygons only (line runways skipped:
  the `aerodrome` polygon already covers the grass infield, which is the actual false positive).
- These polygons are burned as **code 50 (built-up)**, painted at lowest priority
  (`custom_order = [50, 80, 51, 52, 53, 55, 54]`) so water/buildings/roads inside still win.
- `generate_guild_landcover` gains one `xr.where(da_osm_raster == 50, 50, ...)`.

Why 50 and not 60 (bare soil): **60 is in `habitat_codes`** for `ground_reptile` and
`herbaceous_insect`, so 60 would NOT remove the false positive for those guilds. 50 is
non-habitat for every guild and already has a friction entry in all 5 friction dicts, so no
change to `species_params.py`. `leisure=park/garden/golf_course` deliberately excluded (often
genuine habitat). Affects new runs only; py_compile OK. Validated end-to-end on Toulouse-Blagnac
(1 aerodrome + 47 aeroway polygons -> code 50 -> non-habitat; runway-centre pixel checked).

## 2026-06-09 : fix node-ID desync from node smoothing (node_not_found / false isolated)

Symptom (nancy run): ~28 corridors failing as `node_not_found`, unstable/offset node IDs, and
stepping stones with no barrier and habitat right next door appearing isolated.

Cause: node smoothing changed the node set/index. `df_nodes.index` is the key for the graph
(`G`/`gdf_edges`), `patch_masks` in `compute_lcp_network`, and node betweenness. The old
`safe_smooth` could drop rows (silent `continue`) and the canonical a_b_c_functions version did
`pd.concat(ignore_index=True)` (renumber). Any drop/renumber desynced the IDs -> corridors to a
shifted/missing node failed as `node_not_found`, and their endpoints looked isolated.

Fix (in `utils/routing.py:safe_smooth`, so callers stay one line): rewritten to be index-stable
by construction. It starts from `gdf.copy()`, smooths each geometry, and only **overwrites the
geometry** where smoothing succeeds (unusable/failed geometries keep their raw geometry); no row
is ever dropped or renumbered. `buffer(0)` is folded in, so `sp_pipeline` is now just
`df_nodes = rout.safe_smooth(df_nodes)`. Unit-tested: non-contiguous index + an empty geometry
-> output index identical to input, every row kept. Re-run the pipeline; `node_not_found` from
smoothing should disappear (`uncrossable_barrier` / `cost_threshold_exceeded` are legit and stay).

## 2026-06-10 : node smoothing 12h -> ~10s (batched smoothify)

`safe_smooth` called `smoothify` once per node (2218x). Each call respawns a joblib/loky worker
pool for a single geometry -> ~19 s/node, ~12 h ETA, and "A worker stopped ... memory leak"
warnings. `smoothify` itself is fast even on 8k-vertex polygons (~0.06 s); the cost was the
per-call pool churn, not geometry complexity.

Rewrote `safe_smooth` to do ONE batched `smoothify(merge_collection=False)` call on all smoothable
geometries (vectorized sanitation first: make_valid, keep polygonal types). `merge_collection=False`
keeps one output per input so the node set/index stays intact; results are written back by index,
failures keep raw geometry, final `buffer(0)`. Benchmarked: 300 nodes (incl. big complex ones)
in 1.3 s -> ~10 s for 2218 nodes, index preserved, all valid/non-empty.

Note on the persistent "29 node_not_found": that output was a stale notebook cell cache (identical
to-the-second timings across "reruns"); the slow smoothing meant no fresh LCP had actually
completed. With the batched smoothing + index-stable nodes + the patch_masks filled-polygon
fallback, a clean restart + Run All should show node_not_found ~0.

Notebook migration (2026-06-09): the 5 `<city>_prod.ipynb` still smoothed nodes inline via the
geoai-dependent canonical `from utils_polygon_smoothing import safe_smooth` (4 notebooks) or an
inline `fast_safe_smooth` using `geoai.smooth_vector` (perpignan), both of which now raise
`ModuleNotFoundError: geoai` after the my_custom_libs removal. All 5 redirected to
`df_nodes = rout.safe_smooth(df_nodes)` (index-stable, geoai-free). The unused `%pip install
ipyvuetify leafmap --target=libs` line (deleted Dash app) was commented out. perpignan keeps a
now-dead inline `fast_safe_smooth` def whose `geoai.smooth_vector` line never executes (function
no longer called); inline defs in notebooks remain a convention gap to clean up later.

## 2026-06-10 : ROOT CAUSE of the persistent `node_not_found` (was NOT a node/index issue)

Correction of the two notes above (stale-cache / index-desync hypotheses): both were wrong. The
30 `node_not_found` survived a confirmed kernel restart, a forced `importlib.reload(routing)`, and
a fresh cell-24 run, on a fully consistent state. In-function instrumentation proved it:

    [DBG] patch_masks=2218 | nodes_df=2218 | nodes missing from patch_masks=0
    [DBG] corridors failing 'u in pm and v in pm' = 0      <- ZERO membership failures
    ... yet value_counts -> node_not_found 30

So `node_not_found` did NOT come from a missing node / unaligned index / stale patch_masks. Every
failing corridor entered the `try` block (both endpoints in `patch_masks`) but exited with the
DEFAULT `fail_reason='node_not_found'` left untouched. The only branch that leaves the default
intact is the success path when `len(path_coords) < 2`: for two adjacent/overlapping patches, the
cheapest MCP end pixel is already a start pixel, so `mcp.traceback` returns a single pixel, no
pixel-path `LineString` can be built, and the code fell through without updating `fail_reason`.
The label `node_not_found` was a misnomer that misdirected the whole investigation.

Fix (`utils/routing.py:compute_lcp_network`): added the missing `else` to the `len(path_coords)
>= 2` test. When the LCP collapses to a single pixel, the patches are genuinely connected (cost
~ 0), so the corridor is marked `success` using the theoretical anchor-to-anchor segment from the
Gabriel graph as geometry (`path_geom = row['geometry']`), with `real_dist`/`accumulated_cost`
filled. The `'node_not_found'` default now only survives for a truly missing node (defensive
guard, not reached on real data here).

Result (nancy, ground_mammal): 4619 -> 4649 success, `node_not_found` 30 -> 0; `uncrossable_barrier`
110 and `cost_threshold_exceeded` 8 unchanged (legitimate ecological outcomes).

Open choice [Assumption], to confirm with Marion: these 30 near-adjacent corridors are labelled
`success` with the straight anchor segment. Alternative would be a distinct tag (e.g.
`status='success', fail_reason='adjacent_patches'`) or a centroid-to-centroid geometry, if the
deliverable needs to single them out. Current choice keeps them as ordinary successful corridors.

## 2026-06-10 : rupture points exclude buildings (51) AND water (80)

`extract_rupture_points` (`utils/connectivity.py`) builds its barrier list from the friction dict
(codes whose friction is NaN = uncrossable). Buildings (51) were already excluded; added water (80)
the same way:

    if isinstance(v, float) and np.isnan(v) and str(k) not in ('51', '80')

Rationale: a rupture point flags a "black spot" to fix with a wildlife-crossing structure. That
makes sense for crossable-by-engineering infrastructure (roads, rail), not for a watercourse or a
building footprint. The corridor network itself is unchanged: water still acts as an
`uncrossable_barrier` in the LCP; only the `ruptures_*.geojson` layer no longer emits points where
a failed corridor meets water. [Assumption] to confirm with Marion: if she instead wants to flag
water crossings (e.g. to site a fauna passage), this exclusion must be reverted for code 80.

## 2026-06-10 : cleanup of my_custom_libs and libs

Removed `my_custom_libs/` (was 100 MB: orjson, pyogrio, pyogrio.libs, regex, rpds). Verified zero
imports across `utils/*.py` and the 5 notebooks (only stale comments + an old
`.ipynb_checkpoints/routing-checkpoint.py` reference). Base env provides pyogrio + rpds + geopandas,
so geopandas I/O is unaffected; orjson/regex/fiona are absent from base but unused by current code.
The directory could not be fully deleted while the Jupyter kernel held `.nfs*` ghost files; they
clear on kernel restart, after which `rm -rf my_custom_libs` finishes the job. No runtime breakage.

Trimmed `libs/` from 47 MB to ~196 KB: kept `smoothify` + `smoothify-0.2.3.dist-info` (the only
package not in base env, imported by `routing.py:20`). Removed PIL, _duckdb-stubs, box, pexpect,
pyproj, socks.py: all duplicated the base env and, via `sys.path.insert(0, libs)` in routing.py,
were shadowing the conda versions. smoothify remains the sole reason `libs/` is on the path.

## 2026-06-10 : pinch points (current-flow) disabled (perf), implementation preserved

`sp_pipeline` hung (interrupted by KeyboardInterrupt) inside
`conn.calculate_pinch_points_network` -> `nx.edge_current_flow_betweenness_centrality(solver='lu')`.
That current-flow metric (Circuitscape-equivalent) builds/inverts the graph Laplacian and solves
one system per node: ~O(N^2) memory, ~O(N^3) time. On the giant connected component of a large
city (Toulouse, thousands of nodes) it runs for tens of minutes to hours per guild, x5 guilds x
several cities. The solver was already the efficient one ('lu'); the cost is the number of solves,
not the solver.

Marion does not need the pinch-point attribute for now and did not want the work deleted. Decision:
DISABLE the computation at a single point. `calculate_pinch_points_network` now short-circuits with
an early return that adds a NaN `pinch_point_score` column (kept so downstream writers/viz do not
break), and the full original implementation is preserved verbatim below the early return
(unreachable while disabled). Re-enable by deleting the early-return block.

Single-point design rationale: every caller is covered at once (sp_pipeline + the inline cells in
the 5 *_prod notebooks) without editing the large .ipynb files. To apply in a running kernel:
`importlib.reload(connectivity)` before re-running. The lcp_*.geojson still carries a
`pinch_point_score` column, now all-NaN.

## 2026-06-10 : flux/flow corridor metrics disabled (not needed), implementations preserved

Marion does not need the flux/flow corridor characterisation for now. Same pattern as the pinch
points: disable at the function level (single point, covers sp_pipeline + the inline cells of all
5 *_prod notebooks without editing the large .ipynb), early return, full implementation preserved
verbatim below the return.

Disabled in utils/connectivity.py:
- `calculate_edge_dpc` -> returns NaN 'dPC_val' / 'dPC_relative' (dPC = flux). Note: dPC is the
  standard connectivity-importance metric, not a minor attribute; disabled per request, trivially
  re-enabled.
- `calculate_edge_betweenness` -> returns NaN 'ebc_score' (edge betweenness = flow of paths).
- `classify_corridors` -> returns None 'category' (it derives from dPC_relative + ebc_score, both
  now disabled, so the classes would be meaningless otherwise).
- `calculate_pinch_points_network` -> already disabled (current-flow, perf), NaN 'pinch_point_score'.

These were not perf problems (edge_dpc is cheap per-row arithmetic; edge_betweenness is Brandes
O(VE), fast at this scale) except pinch (the real O(N^3) hang). lcp_*.geojson still carries the
columns dPC_val, dPC_relative, ebc_score, category, pinch_point_score, now all NaN/None. sp_pipeline
references none of them downstream (stats KPIs unaffected). To apply in a running kernel:
`importlib.reload(connectivity)`. Re-enable any metric by deleting its early-return block (for
`classify_corridors`, also re-enable dPC + edge betweenness first).

## 2026-06-10 : node network-role (NBC) disabled too

Same request/pattern: `calculate_node_betweenness` (node betweenness centrality, the patches'
"network role" / ecological-hub score) disabled. Early return sets NaN 'nbc_score' but KEEPS the
AOI spatial clip (sjoin) so nodes_*.geojson stays city-only, identical node set, just without the
score. Full implementation preserved below the return. nx.betweenness_centrality is Brandes O(VE)
(fast at this scale); disabled because the attribute is not needed, not for perf. Reload
connectivity to apply.

## 2026-06-11 : spurious isolated nodes -> build_gabriel_graph ran on invalid raw geometries

Many "isolated nodes" in the outputs were not ecological: nodes with a valid neighbour a few
metres away, no barrier, no intervening node, yet degree 0. Step-by-step trace on a Perpignan
orphan (id 265, core): its 7-11 m neighbours (261, 1255, 1268) produced Gabriel candidate edges
that NO node pruned ("the edge should exist") yet were absent from the graph.

Root cause: `build_gabriel_graph` is called BEFORE node smoothing (deliberately, smoothing is slow),
so it operates on the raw MSPA polygons, which are frequently self-intersecting / invalid. Shapely
`geom.distance()` / `nearest_points()` on an invalid polygon return wrong values WITHOUT raising, so
the edge-to-edge distance falls outside [0.1, max_dist] (or the anchor fails) and the candidate edge
is silently never created. Proof: rebuilding the graph on the already-smoothed (valid) df_nodes gave
`build_gabriel_graph -> node 265 degree = 3 (neighbours 261, 1255, 1268)` exactly as expected.

Fix: added a validity guard at the top of `build_gabriel_graph` -> `make_valid()` on the invalid
geometries only (cheap, far cheaper than smoothing, so the build-before-smoothing order is kept;
index preserved so node IDs stay aligned). This was NOT the Gabriel pruning / polygon-vs-point
hypotheses explored earlier (both wrong); it was invalid input geometry.

Impact: this reconnects the spuriously-isolated nodes, so the graph topology changes (more edges)
-> dPC, corridors, isolated-node counts all change. Every city's graph was built on raw geometries,
so all cities must be re-run to benefit. Reload connectivity (`importlib.reload(connectivity)`)
before re-running.

## 2026-06-11 : safe_smooth_lines batched (segment smoothing was the new bottleneck)

`safe_smooth_lines` (urban-planning segment smoothing, used in sp_pipeline and the segment
regeneration) called `smoothify` once PER branch inside a per-row loop. On Toulouse/ground_mammal
that is 27,926 segments at ~2 it/s -> ~4 h for ONE guild (the regen_segments.py run was on track for
~40 h). Same joblib/loky worker-pool churn we already fixed in `safe_smooth` for nodes.

Rewrote it as a 3-pass batched version: (1) explode rows into cleaned simple-line branches,
remembering (row, slot) ownership; (2) ONE `smoothify(merge_collection=False)` call over all
branches, then `anchor_endpoints` each; (3) reassemble per row (LineString or MultiLineString),
attributes preserved. Branches degraded by cleanup are kept raw; a failed batch falls back to the
cleaned branches. Same output contract; orders-of-magnitude faster. Reload routing to apply.

## 2026-06-11 : sp_pipeline chmod outputs (world rw) + inherits the function-level fixes

Added at the end of each guild in `sp_pipeline`: `chmod -R a+rwX <guild_dir>` (+ keep city_dir /
outputs traversable). The kernel runs as root, so outputs were `root:644` and teammates hit
Permission denied; this makes them world rw, per the convention. No other sp_pipeline change was
needed for the perf fixes: `safe_smooth_lines` (batched) and `build_gabriel_graph` (make_valid) are
fixed at the function level, and sp_pipeline calls them, so it inherits both via a module reload.

## 2026-06-11 : dashboard node-id linkage (rupture/barrier tooltips vs patch ids)

Two unrelated id spaces broke the dashboard: pipeline graph ids (df_nodes.index, span the buffered
AOI, carried by LCP/rupture/barrier node_1/node_2) vs a fresh 1..N re-index assigned in prep, because
GeoJSON export drops the pandas index. So rupture "Between patches X<->Y" never matched "Patch #N".

Fix (Marion's diagnosis):
- Edit 1 (sp_pipeline.py): right after node smoothing, `df_nodes['node_id'] = df_nodes.index`,
  materializing the graph id as a column BEFORE the isolated-nodes subset and the nodes export, so
  both nodes_*.geojson and isolated_nodes_*.geojson carry it (survives the betweenness sjoin/clip).
- Edit 2 (utils/prep_for_dashboard.py): NODE_PROPS maps node_id->id; prep_nodes and
  prep_isolated_nodes prefer that id (Int64) and only fall back to index+1 for pre-node_id data.
  RUPTURE/BARRIER_PROPS already keep node_1/node_2 (graph ids), so they now line up.

Requires re-running pipeline (regenerates nodes/isolated with node_id) then prep. Known limitation:
rupture/barrier endpoints outside the city AOI reference graph ids with no drawn patch (corridors
cross the boundary); inherent, not fixed here.

## 2026-06-11 : ruptures de-aggregated + barriers enriched with obstacle / n_ruptures

Goal: link barriers (failed corridors) to the obstacle that blocks them. The blocker was the rupture
aggregation: `extract_rupture_points` clustered crossings and kept only `node_1=('node_1','first')`
per cluster, destroying the corridor<->rupture link, so barriers could not be matched without loss.

- De-aggregated `extract_rupture_points`: removed the clustering + 'first' aggregation. Now returns
  ONE rupture point per (failed corridor x obstacle) crossing, each keeping its exact node_1/node_2
  and wc_code (pn_id = row index). Consequence: more rupture points than before (no merged
  "black spots"); cluster_tolerance is now unused (kept in the signature for compatibility).
- New `enrich_barriers_with_ruptures(gdf_barriers, gdf_ruptures)`: exact, order-independent
  (node_1,node_2) match; adds 'obstacle' (comma-joined sorted unique crossed wc_codes, '' if none)
  and 'n_ruptures' (count). cost_threshold_exceeded barriers get obstacle=''/0 -> distinguishes a
  physical block from a distance/cost failure. Existing barrier fields kept.
- Wired in sp_pipeline before the barriers write. prep_for_dashboard.BARRIER_PROPS now keeps
  obstacle + n_ruptures. Requires pipeline re-run then prep. Dashboard JS would need a tooltip
  tweak to display the new fields (dashboard side, not this repo).

## 2026-06-11 : ruptures layer removed (folded into barriers)

Now that barriers carry `obstacle` / `n_ruptures`, the standalone ruptures layer is redundant.
- sp_pipeline: still computes the crossings (`extract_rupture_points`) internally to enrich the
  barriers, but no longer writes `ruptures_*.geojson`.
- prep_for_dashboard: the ruptures prep block is removed (the `prep_ruptures` helper kept, unused),
  so no ruptures layer reaches the dashboard.
- Deleted the 13 stale `ruptures_*.geojson` from data/outputs (explicit user confirmation).
Minor tradeoff accepted: the exact black-spot point markers are gone; the barrier line + its
obstacle code carry the information instead.

## 2026-06-11 : root cause + fix of spurious isolated nodes (Gabriel graph)

Symptom: normal islets (Perpignan/ground_mammal nodes 1200, 1379, 1366) flagged isolated even
though valid neighbours sit a few metres away with a clear gap. Survived kernel restart + full
re-run. Earlier hypotheses (make_valid flipping, touching-floor alone, wrong IDs) were all
disproved empirically.

Diagnosis (instrumented `build_gabriel_graph` with a temporary `debug_node` param, traced on the
RAW df_nodes rebuilt from the saved binary_habitat tif):
- IDs verified aligned (edge endpoints land on their `node_id` patch within the smoothing offset,
  max 42 m, none at 100 m+): not an ID bug. RangeIndex confirmed clean (label == positional).
- The graph is built on the RAW (pre-smoothing) MSPA polygons, but every saved/displayed layer is
  SMOOTHED. So a node can be isolated on its raw geometry yet look connectable in the dashboard.
- Real mechanism = a degenerate interaction of two rules on raw geometry:
  1. The `0.1 < dist` floor skips creating an edge between two patches that touch (gap == 0,
     pixel-adjacent core/islet).
  2. The Gabriel pruning uses the candidate's FULL polygon (`geom_c.distance(midpoint) < radius`).
     A patch C that touches the target u sits on u's boundary at the anchor point p_u, hence inside
     the diametral circle of nearly EVERY edge of u, and prunes them all.
  Net: u has no edge to C (rule 1) and all its other edges killed by C (rule 2) -> isolated.
  Proof in the trace: 1200's edges all pruned by 276 & 256 (its exact 2 touching patches), 1379 by
  314, 1366 by 1361. Smoothing hides the bug by opening the zero gap to ~7 m.

Fix (surgical, keeps edge-to-edge distances and the polygon method):
- Pre-compute a "touching" adjacency (gap <= 0.1 m) once per node (cheap, one small-buffer index
  query each), then in the pruning loop skip any candidate C that touches u or v. A patch adjacent
  to an endpoint is a neighbour, not an obstacle between u and v.
- Result on Perpignan/ground_mammal RAW: 1200 deg 0->5, 1366 1->4, 1379 0->5; nearest edges KEPT;
  graph edges 3799 -> 4437 (+638 recovered). Remaining prunes are legitimate (genuine intervening
  patches). Rejected alternatives: centroid/point-based Gabriel (changes distance semantics, less
  faithful for dispersal cost) and zero-cost islet<->core edges (reintroduces zero-length corridors).
- A `debug_node` param stays in `build_gabriel_graph` (inert by default, zero overhead) for future
  per-node tracing.
Action pending: full pipeline re-run to regenerate outputs with the fix.

## 2026-06-11 : keep linked out-of-AOI patches in the nodes layer (no corridor dead-ends)

Context: corridors are kept whole if they intersect the AOI, so a corridor can run from a city
node to a buffer (out-of-AOI) node. But the nodes layer was clipped strictly to the AOI, so that
buffer endpoint was not displayed and the corridor appeared to dead-end at the AOI edge.
- `calculate_node_betweenness` gains a `keep_ids` param: the AOI clip now keeps nodes intersecting
  the AOI OR whose ID is in keep_ids (replaced the sjoin clip with an intersects mask, both in the
  active early-return path and the preserved NBC path).
- sp_pipeline passes `keep_ids = endpoints of gdf_lcp_city` (success corridors intersecting the AOI),
  so every kept corridor terminates on a visible habitat.
- Isolated-nodes layer unchanged (still AOI-only, computed before the reassignment); a linked buffer
  patch is connected by construction, so it never appears isolated. Constraint "an out-of-AOI node is
  never flagged isolated" already held and still holds.

## 2026-06-11 : consistent AOI clipping across all exported vector layers

Empirical check on Perpignan/ground_mammal (existing files) contradicted the earlier assumption that
only lcp needed attention:
- edges_*.geojson: 4437 features, 3352 ENTIRELY outside the AOI (the layer was exported from the full
  city+buffer graph, never clipped) -> these are the "corridors entirely outside the AOI" reported.
- segments_*.geojson: 1837 features, 118 entirely outside.
- isolated_*.geojson: 16 features, 4 straddling the AOI boundary (a part outside) flagged isolated,
  because the filter used 'intersects' (keeps a node that merely touches the AOI).
- lcp_* and barriers_* were already correctly clipped (intersects).

Rule made uniform (sp_pipeline):
- edges: full graph kept in memory for the LCP computation, but the exported file is clipped to
  intersects(AOI). New `gdf_edges_city`.
- segments: clipped to intersects(AOI) before writing (drop segments lying entirely in the buffer,
  keep whole any segment that touches the city).
- isolated nodes: 'intersects' -> 'within' (a node with any part outside the AOI is not a city patch,
  so it is not flagged isolated). [If too strict at the boundary, switch to representative_point-in-AOI.]
- nodes keep_ids: now based on the endpoints of the clipped edges (superset of all displayed line
  layers: edges/lcp/barriers), so every displayed line terminates on a visible habitat. Replaces the
  earlier lcp-success-only basis.
Principle: a feature is exported if a part of it touches the AOI (intersects), EXCEPT isolated nodes,
which require being fully inside (within). Out-of-AOI patches are shown only when they anchor a kept
line, never as standalone isolated patches.

## 2026-06-11 : vectorize PC index (scipy Dijkstra + numpy), the big-city bottleneck

On Toulouse (~9436 nodes) `calculate_pc_index_lcp` (real PC) ran 2h+ on the giant connected
component with no progress output and ~15 GB RSS: per component it called pure-Python
`nx.all_pairs_dijkstra_path_length` (builds an ~N*N dict) then an O(N^2) Python double loop
`sum a_i*a_j*exp(-d_ij)`. Same shape in `calculate_pc_index` (theoretical PC).

Fix: a shared helper `_pc_numerator(G, weight='cost_log')` computes, per connected component, a
dense cost matrix via `scipy.sparse.csgraph.dijkstra` (C-level) and the sum as a numpy outer
product `(a[:,None]*a[None,:]*exp(-D)).sum()`. Mathematically identical: within a component all
pairs are reachable, and D_ii = 0 gives exp(0)=1 (matches the old n1==n2 case). Both PC functions
now call it; `calculate_pc_index_lcp` keeps its edge-cost update unchanged.

Validation (_sandbox/validate_pc.py, old-vs-new): synthetic graphs identical to ~1e-16; real
Perpignan graphs identical to ~1e-14; reproduces the saved stats.csv pc_theory 10.0119308 exactly;
x29 speedup on Perpignan's full graph (28.5s -> 0.98s), far larger on Toulouse.

NOTE: the detached runs in flight (Toulouse baseline + scenario) imported the OLD code into memory,
so they are unaffected and still slow; the fix only takes effect on the NEXT run.

## 2026-06-12 : vectorize the segments stage (the real big-city bottleneck)

Measurement (timing each sub-step of create_urban_planning_segments on real Toulouse ground_mammal
data, _sandbox/time_segments.py) showed the ~3h Toulouse "gouffre" was NOT the PC (real PC ~12 min
old / ~30 s new) but the SEGMENTS stage, dominated by two ops run against the giant habitat union:
- `exploded.geometry.within(habitats_union.buffer(15))` per fragment: ~64 min
- `gdf.geometry.difference(habitats_union)` per corridor: ~13 min
(everything else, incl. safe_smooth_lines/weld, was sub-second to seconds.)

Fix in create_urban_planning_segments (same idea as the PC: kill O(N * huge-geometry)):
- difference: difference each corridor only against the patches it actually intersects (found via a
  spatial-index sjoin), not the full union. Identical result (a corridor is unchanged by patches it
  does not intersect).
- within (skirting test): prepare the buffered union once (`shapely.prepared.prep`) so each
  containment test is index-accelerated; within(B) == prep(B).contains(A).

Validation (_sandbox/validate_segments.py): on Perpignan, op1 geom-equal 1042/1042 with identical
total length (diff 0.0), op2 identical on 2013/2013 fragments. On Toulouse, the full function went
from ~77 min to 155.8s (~30x) for an identical 33230-segment output.

Combined with the PC fix, both Toulouse "gouffres" are gone. Per-guild cost is now dominated by the
(unchanged, inherent) Gabriel build ~23 min + LCP tracing ~24 min.

## 2026-06-12 : scenario outputs layout + single parameterized runner

Tidied the run tooling and scenario storage:
- Scenarios no longer live at the repo root (`scenarios/<slug>/data/outputs/<City>/...`, which
  also violated the data/ root rule). New layout, under data/, by city then by readable project
  name: `data/scenarios/<City>/<project-name-slug>/<guild>/...` with `project.geojson` + `meta.json`
  copied alongside for provenance (id + name). The slug is the slugified `project_name`.
- Existing three scenarios migrated: Perpignan/vegetalisation-place-de-la-catalogne,
  Toulouse/vegetalisation-ramblas-allees-jj, Toulouse/vegetalisation-allees-jj-ramblas-2.
- One parameterized launcher `_sandbox/run_pipeline.py` replaces the per-run scripts:
  `run_pipeline.py <City>` (baseline -> data/outputs/<City>) or
  `run_pipeline.py <City> --project <history_dir>` (scenario; reads project.geojson + meta.json,
  burns the polygon, writes the flat data/scenarios/<City>/<slug>/ layout). Logs go to _sandbox/logs/.
- sp_pipeline itself is unchanged (it still derives project_root from OUTPUT_DIR and writes
  project_root/data/outputs/<City>/<guild>); the runner flattens that into the scenario layout
  after the run.

## 2026-06-16 : sub-network (connected-component) metric, post-barrier

Added a sub-network count to the realized (post-barrier) network, per (city, guild).
- New stats.csv KPIs: `n_subnetworks` (connected components of >=2 patches in the realized
  graph G_success that touch the study area) and `largest_subnetwork_size`.
- New `nodes_*.geojson` column `subnetwork_id` (id of the sub-network a patch belongs to;
  null for singletons = isolated / kept-but-unrealized patches).
- Perimeter handling (the hard part): components are computed on the TRUE realized graph
  (G_success, which already includes the kept out-of-AOI endpoints), NOT on a subgraph induced
  on AOI-only nodes (that would re-create the fake dead-ends the buffer-keep logic avoids).
  Only components touching the displayed node set (intersects AOI OR in linked_ids, same rule
  as the nodes export) are counted/labelled. A patch linked to a kept buffer patch stays in
  its real sub-network. Consistent with isolated_nodes (singletons) and the displayed corridors.
- Cost: O(V+E), negligible. Takes effect on the NEXT pipeline run only; the existing 5-city
  batch predates it (re-run needed to populate the new fields there).

### 2026-06-16 (same day) : sub-network metric refinement + Ardennes in-place patch

After the first Ardennes run two consistency issues surfaced and were fixed:
- **Size on displayed patches.** `largest_subnetwork_size` was counting all patches of a
  component (AOI + buffer reachable via AOI-touching corridors), so it could exceed `nb_nodes`
  (arboreal: 4188 > 4174). Now size and the >=2 threshold count only displayed patches
  (`|comp ∩ displayed|`); connectivity is still read on the true graph (no fake split), so
  `largest <= nb_nodes` always.
- **Theory on the AOI-clipped Gabriel.** `n_subnetworks_theory` was computed on the full
  buffered Gabriel graph G, which merges displayed patches through buffer-only links and
  under-counts (gave 1 everywhere). It now uses `gdf_edges_city` (the kept Gabriel edges,
  AOI-clipped), the same link set as the realized side, so `subnetworks_split_by_barriers`
  cleanly isolates the barrier effect.
- **Ardennes outputs patched in place** (no 5h23 re-run) with `_sandbox/patch_subnetworks.py`,
  which recomputes from lcp (realized, exact) + edges (theory, AOI-clipped) + nodes (displayed).
  Result e.g. ground_reptile theory=6 -> realized=232 (barriers shatter the reptile network,
  PC loss 97%); arboreal 2 -> 2 (forest network robust).

### 2026-06-16 : sub-network threshold raised to >=3 patches

A sub-network now requires at least 3 patches (was 2). A lone pair (2 patches joined by a single
corridor) no longer counts as a sub-network and its patches get no subnetwork_id (null, alongside
isolated patches). Applied in `utils/sp_pipeline.py` (`_subnetworks`, min_patches=3) and the patch
tool `_sandbox/patch_subnetworks.py`; Ardennes outputs re-patched in place. Effect on Ardennes:
ground_mammal realized 4->1, forest_edge_bird 4->2, ground_reptile 232->151, herbaceous 241->138
(many 2-node pairs dropped); largest_subnetwork_size unchanged.

### 2026-06-16 : sub-networks counted on in-AOI patches (no id gap) + Ardennes renamed

- **In-AOI counting.** Sub-network count/size and the >=3 threshold now use only patches
  strictly inside the AOI (`in_aoi_ids`), not the displayed set (AOI + kept out-of-AOI ring).
  Connectivity is still read on the true graph, so a patch linked through a kept ring patch
  stays in its sub-network; a component straddling AOI+ring counts only if it has >=3 in-AOI
  patches, and its size = in-AOI patches. The id is still written on the ring members of a
  counted component (file stays complete) but they don't add to count/size. Reason: ids were
  assigned over the displayed set, so a component sitting entirely in the ring got an id that
  vanished when the dashboard clips to the AOI, leaving a numbering gap. Verified gap-free:
  AOI-clipped ids are contiguous 1..n for every guild. Ardennes re-patched in place.
- **Rename Ardennes -> PNR_Ardennes** (folder, 55 files, CITY_CONFIG key, patch default). Used
  an underscore (path-safe) rather than a space, for the dashboard/Drive/S3. AOI source unchanged
  (`get_boundary('Parc naturel régional des Ardennes')`).

### 2026-06-17 : water (80) now counted as a rupture-point obstacle

`extract_rupture_points` previously excluded both buildings (51) and water (80) from the obstacle
set used to attribute rupture points / the `obstacle` field on barriers. Per Marion's request, the
80 exclusion is removed (51 still excluded). Effect: for the guilds where water is a barrier
(ground_mammal, ground_reptile), a failed corridor crossing an OSM water polygon now gets
obstacle='80' and a rupture point, instead of obstacle='' / n_ruptures=0. Takes effect on the next
run; existing outputs (5 cities + PNR_Ardennes) predate it.

### 2026-06-18 : smoothify mega-polygon guard + SCOT Pays Yon et Vie

- `utils/routing.py:safe_smooth` now skips smoothing (and buffer(0)) for polygons above 50,000
  vertices, keeping them RAW, and PRINTS a "⚠️ safe_smooth: N polygon(s) over 50,000 vertices ...
  kept RAW" line so it is visible. Reason: a near-region-wide habitat core (the abandoned Jura
  ground_mammal mega-core: 432k vertices, 14k holes, 1593 km2) made smoothify/simplify/buffer(0)
  grind for hours on a single geometry. Guard is inert on normal patches (even ~9k-vertex ones).
- New AOI `SCOT_PaysYonVie` = ("boundary", "Pays Yon et Vie"), ~995 km2. Verified get_boundary
  resolves it and it equals the dissolve of CA La Roche-sur-Yon Agglo (LRSY, 502) + CC de Vie et
  Boulogne (493) = 995 km2, same bounds. Agricultural/bocage -> low mega-core risk, but the guard
  protects regardless.

### 2026-06-19 : scenario re-run made idempotent + scenarios/baselines refreshed

- `_sandbox/run_pipeline.py` scenario flatten now overwrites any existing guild folder and skips
  copying project.geojson/meta.json onto themselves, so a scenario can be re-run **in place**
  (`--project <scenario_dir>`) without the previous SameFileError / nested-folder corruption.
- Refresh pass with the up-to-date code (sub-network metric, water-80 obstacle, smoothify guard):
  all baselines re-run + validated (Kourou/Nancy/Perpignan/LRSY/Toulouse/PNR_Ardennes), plus two
  new AOIs LaRochelle (CA, 331 km2) and SCOT_PaysYonVie (995 km2 = CA La Roche + CC Vie&Boulogne).
  The 3 scenarios (Perpignan Catalogne, Toulouse Ramblas x2) re-run in place. No smoothify guard
  trigger on any (all fragmented; the guard exists for future heavily-vegetated AOIs).

### 2026-06-19 : city-level AOI output (baselines only)

run_pipeline.py now writes the analysis AOI once at the city output root
(`aoi_limits_<city>.geojson`, raw CRS, like the notebook), baselines only (scenarios skip it).
The 8 existing baselines were backfilled via `_sandbox/backfill_aoi.py` (incl. LaRochelle and
SCOT_PaysYonVie, which had none). Not written per guild (engineer choice). sp_pipeline unchanged.

### 2026-06-19 : convention fixes (1,2,3,5) + paper updated

- [SECU] GEE service-account key chmod 600 (was group-readable on the shared NFS).
- [data/ root] OSM HTTP cache redirected from the stray root ./cache to data/cache via
  `ox.settings.cache_folder` in utils/landcover.py; existing 1.7G merged into data/cache (now 6.8G).
- [no creds in code] run_pipeline.py no longer hard-codes the service-account email (read from the
  key's client_email) nor the key path (from $GEE_KEY_PATH, fallback to the shared file). ADC
  ee.Initialize(project=...) is not configured here, so a key is still required.
- [promote runner] run_pipeline.py moved out of _sandbox/ to the project root; _sandbox importers
  (backfill_aoi.py, patch_subnetworks.py) updated.
- papier/methodo_paper.md rewritten to the actual method (sub-networks, water-80 obstacle, AOI
  handling, smoothify guard, 8 baselines + scenarios, disabled metrics, method-landscape mismatch);
  papier/litterature/etat_de_lart.md aligned. Not done (audit): #4 def-in-perpignan-notebook, #6 cruft.

### 2026-06-19 : runner -> utils/ + commented functions archived out of utils

- `run_pipeline.py` moved from the project root into `utils/` (engineer preference). Invocation:
  `python3 utils/run_pipeline.py <City>`. Docstring + the two _sandbox importers (backfill_aoi.py,
  patch_subnetworks.py) updated to find it in utils/.
- All commented-out / dead functions removed from the live utils modules and archived verbatim
  (still commented, as a trace) in `_sandbox/deprecated/utils_commented_functions.py` (728 lines):
  connectivity.py (KNN & RNG graph builders, extract_obstacle_crossings, calculate_node_dpc, old
  create_urban_planning_segments, lcp_heatmap, get_priority_corridors_ebc/dpc) -593 lines;
  routing.py (old safe_smooth_lines) -59; vizu_ind.py (plot_connectivity_heatmap) -58.
  Verified: all utils/*.py parse, full import chain OK (8 cities), every conn./rout. call in
  sp_pipeline resolves to an active def (conn.lcp_heatmap reference is itself commented). 0
  commented defs left in utils/.

### 2026-06-19 : bounded dispersal output added (CEREMA-like reach)

Added a second dispersal raster `dispersal_bounded_<guild>_<city>.tif` alongside the unbounded
`dispersal_*.tif`: the continuous cost surface cut at the dispersal budget `d0 * FRICTION_AVG_FAVORABLE`
(= d0*3), pixels beyond -> nodata. New `CorridorPaths.dispersal_bounded_tif`; in sp_pipeline it is
derived by masking the in-memory continuous surface (no second MCP flood). Cost is in friction x
metres (MCP sampling in metres), so the CEREMA `/resolution` term is folded into the sampling and
the budget is `d0*f_fav` directly. Effect scales inversely with d0 (herbaceous keeps ~58 % of the
AOI, ground_mammal ~100 % on a small AOI). Backfilled on all existing baselines + scenarios (55
rasters) by masking the existing dispersal tif (`_sandbox/backfill_dispersal_bounded.py`). README +
methodo_paper updated (now up to 12 files / 5 rasters per guild).

### 2026-06-26 : friction alignment on CEREMA La Rochelle + 5 -> 4 guilds

Full re-derivation of `utils/species_params.py` friction against the CEREMA La Rochelle (2025)
per-species table (annexe 5.4), after a line-by-line review.

- **Aggregation method.** Each WorldCover/OSM class takes the MEAN of the CEREMA classes it
  aggregates (11 classes vs CEREMA's ~30). Documented in `papier/annexe_coefficients_friction.md`
  (table d'agregation + exclusions: peupleraie out of tree, pelouse seche out of grass, dense built
  out of code 50, bassins/canaux principaux out of wetland).
- **Finite road scale.** motorway/2x2 (52) -> 100, secondary (53) -> 50 (was NaN for several
  guilds). Hard barriers (NaN) now limited to buildings (51) and large rivers (80, terrestrial
  guilds). Rationale: a corridor across a road is meaningful (-> rupture point), a corridor through
  a building is not; also yields precise rupture points once routes are crossable.
- **Built not valorized.** built (50) = inter-building impervious matrix (dense already 51) = 10 for
  all terrestrial (deviation: CEREMA lizard 3 kept at 10, do not signal built favorable in an urban
  de-fragmentation tool); arboreal lowered 50 -> 10 (was = road).
- **Habitat graduated, no longer forced to 1.** Habitat codes take their CEREMA mean (<= 3). Codes
  with mean > 3 are movement, not habitat: shrub (20) removed from ground_reptile habitat
  ([20,30,60] -> [30,60]). Reptile grass kept at 1 (optimum) so the guild keeps a milieu-de-vie.
- **wetland/mangrove inferred** from the mean of the water classes (no CEREMA terrestrial row): ~8
  for terrestrial guilds, kept finite (a marsh is passable, unlike a large river).
- **herbaceous_insect guild DROPPED** (5 -> 4): after alignment its habitat reduced to grass+bare
  (= reptile) and its fragmentation behaviour was redundant; CEREMA merges lizard + orthoptera into
  one herbaceous cortege.

Docs updated: methodo_paper.md (guild table/method/results), annexe_coefficients_friction.md (new,
FR, for the internship report), data/outputs/README.md, species_params.py docstring. **NOT yet done
(next session):** full re-run of all baselines + scenarios (propagates the friction change + the
option-A Gabriel touch-edge fix + in-AOI PC + precise ruptures), delete the now-orphaned
`herbaceous_insect/` output folders, regenerate `suivi/data_structure.md`, fix
`pnr_ardennes_prod.ipynb` (GUILD_KEY = "herbaceous_insect" would now fail). Env note: this session's
container had geopandas bumped to 1.1.3 (via osmnx install), requiring str() on geojson exports + a
CRS guard in sp_pipeline (already applied).

## 2026-06-30 (Marion) -- Derived AOI-clipped stats moved into the pipeline stats.csv

Six AOI-clipped derived metrics, previously recomputed only in `prep_for_dashboard.py`
(`derived.json`), are now emitted by the pipeline itself in `stats_<guild>_<city>.csv`:
`aoi_total_ha`, `habitat_ha_in_aoi`, `habitat_coverage_pct`, `nodes_in_aoi`,
`cores_in_aoi`, `islets_in_aoi`. Rationale: these are analytical (not presentation),
so they belong at the source next to the other KPIs; the dashboard-prep step stays a
separate presentation adapter (WGS84 / simplification / colormapped PNG / dashboard layout),
deliberately NOT merged into sp_pipeline.

- Code: `utils/sp_pipeline.py`, computed from `aoi_utm` + the already-present `in_aoi_ids`
  / `aoi_geom` (no extra graph work); `habitat_ha_in_aoi` = sum of node-AOI intersection area.
- Existing 24 outputs from the 2026 re-run patched post-hoc (same computation, from
  `nodes.geojson` + `aoi_limits.geojson`), validated identical to `prep_for_dashboard`
  (0.1 ha delta on one pair, from the 1 m Douglas-Peucker that prep applies for display and
  the pipeline does not -- full-fidelity source value kept). chmod a+rwX.
- `prep_for_dashboard.py` now READS these from `stats.json` (single source of truth), with a
  recompute fallback for legacy outputs lacking the keys. derived.json values are thus the
  pipeline's full-fidelity numbers (e.g. Perpignan ground_mammal habitat 2651.8 ha, not the
  2651.9 prep used to recompute on the DP-simplified geometry).

## 2026-07-06 (Marion) -- Failed-links renaming, blocked geometry + rupture layer, and a planner-facing connectivity KPI

Three linked changes, all taking effect at the next full re-run. Terminology also shifted
`guild` -> `ecoprofil` project-wide (Marion, separate pass); the notes below use `ecoprofil`.

**1. Renaming `barriers` -> `failed_links` (clarity: "barrier" conflated two very different things).**
The old `barriers` layer lumped (a) links where a route exists but is beyond the dispersal budget
and (b) links blocked by a hard obstacle, and "barrier" clashed with "rupture point". New scheme:
- layer `barriers_*.geojson` -> `failed_links_*.geojson`
- `fail_reason`: `cost_threshold_exceeded` -> `out_of_reach`, `uncrossable_barrier` -> `blocked`
  (`node_not_found` kept, technical)
- `ruptures`/`ruptures_geojson` -> `rupture_points`/`rupture_points_geojson`
- `enrich_barriers_with_ruptures` -> `enrich_failed_links_with_ruptures`
- stat `subnetworks_split_by_barriers` -> `subnetworks_split_by_failed_links`
Applied in the 4 pipeline files (routing, connectivity, paths, sp_pipeline), the 3 report figure
scripts, README, methodo, and the 6 prod notebooks (legacy). NOT applied to `prep_for_dashboard.py`
(Marion's call, handled separately) nor to the historical logs (decision_log, notebooks_overview).
The generic word "barrier" (soft_barrier=100, hard-barrier friction) is intentionally kept.

**2. `blocked` links keep their real geometry; rupture points get their own layer.**
Previously `blocked` links were drawn as a straight desire line and the soft-retrace was discarded.
Now the soft-retraced least-cost route (barrier softened to 100) is kept as the `blocked` link's
geometry (follows the terrain, crosses at the realistic point), and `rupture_points_*.geojson` is
exported as a point layer (was computed then thrown away; only `n_ruptures`/`obstacle` survived on
the link). Dashboard shows only `blocked` (out_of_reach dropped there); the full `failed_links`
layer stays in `data/outputs` (analytical). This refines the 2026-06-24 "no non-functional corridor
shown" decision: we keep the data layer, the dashboard just doesn't render out_of_reach.

**3. Connectivity KPI reworked (headline was unintuitive for planners).**
Colleague feedback: a "% loss" of PC is meaningless to an amenageur (a % loss of an abstract index,
relative to a hypothetical all-corridors-work baseline). PC is only meaningful in relative terms.
Replaced the headline with two planner-facing metrics, both derived from the same PC numerator
(which weights each patch by its in-AOI area, so they share the in-AOI basis):
- `ec_real_ha` / `ec_theory_ha` = **equivalent connected area** = sqrt(PC) x AOI area (hectares):
  "the network functions as a single connected patch of X ha". Tangible; the scenario delta is in ha.
- `connected_habitat_pct` = `ec_real_ha` / `habitat_ha_in_aoi` x 100 = **share of habitat that
  functions as connected** (0-100, linear, bounded since EC <= habitat). Chosen over the strict
  probability EC^2/habitat^2 (= r^2), which squares to tiny, alarmist values for fragmented networks.
`connectivity_loss_pct` is KEPT in the data (non-breaking) but demoted; "loss" is now read in
hectares as `ec_theory_ha - ec_real_ha`. Validated on existing stats: connected% bounded 8.6-89.7%,
EC 253-20864 ha, plausible (e.g. LRSY hedgehog 83% / 20864 ha vs LaRochelle squirrel 17% / 253 ha).
FR labels for report/dashboard: "surface equivalente connectee (ha)", "part d'habitat connectee (%)".

**Env note.** Added `restore_env.sh` at the project root: the ephemeral container wipes pip packages
on restart (osmnx for the pipeline, python-docx + xhtml2pdf for the report build). Run it after any
restart before a pipeline run.

**Pending:** full re-run (8 baselines + 2 scenarios) to regenerate `failed_links_*` + `rupture_points_*`
+ the new KPI columns, then delete the orphaned `barriers_*`/`ruptures_*` files; refresh the report
§4 numbers; update the dashboard front (barrierLayer -> failedLinksLayer, data_access, rupture layer).

## 2026-07-06 (Marion) -- Scenario burn now overrides OSM on the project footprint

Finding (from the Ramblas "vegetalize the avenues" scenario, ground_mammal): the burned zone did not
fully become habitat. In the burned footprint (481 px), the scenario land-cover was only 293 px shrub
(20) + 188 px still building(51)/road(52,53). Cause: `burn_polygon` only overwrites the WorldCover
raster, but `generate_ecoprofil_landcover` then re-stamps the OSM infrastructure (codes 50-55/80)
ON TOP (they are hard barriers). The avenues run over real streets, so OSM re-applies the roadway and
buildings and the "vegetalized" avenue stays a road; only its verges turn to habitat. This is why the
created relays had holes (enclosed road/building pixels), why they fragmented into small islets (roads
slice the shrub into <0.1 ha slivers dropped by MSPA), and why some stretches produced no node at all.

Fix: in scenario mode (`run_pipeline.py --project`), after burning the WorldCover we now ALSO clip the
OSM vectors out of the project footprint (`lc_osm.difference(project_polygon)`), so the burned class
wins over everything. This models the intended action (vegetalize / pedestrianize = remove the road
and buildings, then set the veg class). Baseline runs are untouched (scenario-only path). Takes effect
for the scenarios at the end of the in-progress full re-run.

## 2026-08-03 (Marion) -- Rename `segments_amenagement` -> `corridor_segments`

Naming change requested by the engineer: `segments_amenagement` was misleading (the layer is not a
planning proposal, it is just the LCP network aggregated and clipped to the AOI). Renamed to
`corridor_segments` everywhere the identifier appears:
- `utils/connectivity.py:832`: function `create_urban_planning_segments` -> `create_corridor_segments`
  (docstring updated).
- `utils/sp_pipeline.py:257`: call site updated; local comment updated.
- `utils/paths.py:120`: the segments output path now resolves to `corridor_segments`.
- `utils/prep_for_dashboard.py`: reads `corridor_segments_<ecoprofil>_<City>.geojson`.
- Output files, both READMEs (EN/FR) and the report follow the new name.
Behaviour-preserving rename only (no logic change). Existing outputs written under the old name must be
re-run to carry the new filename; new runs already emit `corridor_segments_*`.

## 2026-08-03 (Marion) -- Land-cover cache (`--lc-cache` / `--refresh-lc`) + per-run timeouts

Problem: every run re-fetched ESA WorldCover from Earth Engine. During the overnight sensitivity queue
one EE fetch hung ~20 h and blocked the whole sequential batch (no timeout, no reuse).

Fix, two parts:
- **Opt-in LC cache** in `utils/run_pipeline.py` (`--lc-cache`): WorldCover + OSM depend only on the
  city and the buffer (`2*d0max`), not on the sweep parameters, so they are cached once per
  `data/lc_cache/<City>_<buffer>/` as `lc_wc.tif` (rioxarray) + `lc_osm.parquet` (geopandas). A run
  reuses the cache if present, else downloads and writes it. `--refresh-lc` forces a fresh download and
  rewrites the cache. A cache-read error falls back gracefully to a normal download. `import rioxarray`
  added to register the `.rio` accessor. Cache is opt-in, so baseline behaviour is unchanged by default.
- **Per-run timeout** in the queued runners (`_sandbox/run_sens_perclass_queued.sh`,
  `run_sweeps.sh`): each pipeline call is wrapped in `timeout -k 60 900` so a hung fetch is killed and
  the queue advances instead of freezing.

Faithfulness verified (`_sandbox/verify_lc_cache.sh`): cache-read stats == fresh-download stats ==
pre-change baseline. `[Certain]`

## 2026-08-03 (Marion) -- `species_params.csv` + `refs` column as single source of truth

Created `data/outputs/species_params.csv` (generated by `_sandbox/make_species_params_csv.py`): one row
per ecological profile x 26 columns (identity, d0 / max graph link `2*d0` / cost budget `3*d0`, reference
+ representative species with Latin + FR names, habitat and impassable-barrier codes, and the full
friction value for each of the 14 land-cover codes with `inf` for NaN barriers). Machine-readable
companion of the README parameter tables.

The generator reads `utils/species_params.py` directly, so that module stays the single source of truth.
As part of this, each profile's `refs` field in `species_params.py` was curated into an author+year
literature list (the CSV surfaces it as a `refs` column). The 4 active profiles now cite: ground_mammal
= Cerema Sud-Ouest (2025), Berthoud (1978), Morris (1984), Huijser & Bergers (2000), Braaker et al.
(2017), Tarabon et al. (2019), Balbi et al. (2019); arboreal_mammal = Cerema Sud-Ouest (2025), Wauters et
al. (2010), Avon et al. (2014), Tarabon et al. (2019); forest_edge_bird = Cerema Sud-Ouest (2025),
Grafius et al. (2017), Merkens et al. (2023); ground_reptile = Cerema Sud-Ouest (2025), Beninde et al.
(2016). The 9 new short refs were also added to the report bibliography (`rapport_8_references.md`).

## 2026-08-03 (Marion) -- GBIF overall chi-square selection test

Added an overall chi-square test to the GBIF habitat-selection analysis (report §5): goodness-of-fit +
a 2xk contingency test on used vs available (target-group background) counts across the 4 land-cover
classes, complementing the per-class Manly/Jacobs selection ratios and their bootstrap 95% CIs. Gives a
single p-value for "is habitat use non-random overall" per profile. Reproducible generators kept in
`_sandbox/gbif_chi2.py` and `_sandbox/gbif_crosstest.py`.

## 2026-08-03 (Marion) -- README overhaul (EN canonical) + French translation

Reworked `data/outputs/README.md` (English, canonical) and created a synced `data/outputs/README_FR.md`
(French translation, kept in step with the EN):
- Territory table now lists each AOI with its administrative type (commune, metropole, communaute
  d'agglomeration, PNR, SCOT, bbox) and its area in km2.
- `dispersal.tif` documented (the output tree has 5 rasters, up to 13 files per city/profile).
- `species_params.csv` and the `scenario/` folder documented.
- Scenario explanation moved into the intro (§1), out of the caveats.
- Road wording clarified: unlike buildings (51) and large rivers (80), which are impassable barriers
  (infinite friction), roads carry a high but finite friction.
- `node_type` (core / islet) vs `class` (3 values: Core, Stepping Stone (Small Core), Stepping Stone
  (Islet)) corrected -- they are NOT redundant; `class` sub-classifies islets.
- PC / EC noted as to be read relatively, not as absolute values; `connectivity_loss` marked "no longer
  considered relevant"; the stale failed_links caveat removed; friction described as specific to each
  ecological profile.
- 0 em dash verified throughout both files.

## 2026-08-30 (Marion) -- Test de déterminisme : sorties identiques octet par octet

Partie D du protocole de validation (`papier/internship_report/validation_protocol.md`), prévue de
longue date et jamais exécutée jusqu'ici. Deux exécutions successives et indépendantes de Perpignan,
quatre profils écologiques, avec `--lc-cache` pour figer l'instantané d'entrée :

    python3 utils/run_pipeline.py Perpignan --lc-cache --out-tag det1
    python3 utils/run_pipeline.py Perpignan --lc-cache --out-tag det2

Résultat : les deux jeux portent les mêmes fichiers, et `diff -r` ne relève aucune différence, soit
une identité **octet par octet** sur toutes les couches (rasters `.tif`, vecteurs `.geojson`) ; les
`stats_*.csv` des quatre profils ont en outre été comparés un à un et sont identiques. Le
déterminisme de la chaîne est donc établi. `[Certain]`

Portée et réserve. Le déterminisme vaut **à entrées identiques**. `--lc-cache` est indispensable au
test : sans lui, chaque exécution réinterroge OpenStreetMap, base vivante modifiée quotidiennement,
et un écart viendrait de l'entrée et non de la chaîne. OSM n'exposant pas de version citable, c'est
`data/lc_cache/<Ville>_<tampon>/` qui archive l'instantané réellement utilisé et rend la chaîne
rejouable par un tiers : il doit être diffusé avec les sorties.

Point de vigilance pour la suite : le manifeste d'exécution prévu (`suivi/reproductibilite.md`, §4)
contiendra un horodatage et cassera l'identité octet par octet. Une fois ajouté, la comparaison
devra l'exclure (`diff -r -x 'manifest_*.json'`).

Report : §2.5 du rapport, le `[À COMPLÉTER]` est remplacé par le résultat. Jeux `det1` / `det2`
supprimés après contrôle.
