# Methodological paper : corridor_project (TVB.urban)

> Living methodological note, kept in sync with the implementation (`utils/`, `run_pipeline.py`)
> and `suivi/decision_log.md`. Reality Filter on: labels mark provenance, confidence tags mark
> certainty. Last substantive update: 2026-06-25 (friction alignment on CEREMA, 5 -> 4 guilds).

## Abstract

Ecological connectivity is mapped for French territories, per functional guild, from globally
available open data (ESA WorldCover 10 m + OpenStreetMap), to derive planning-ready corridors
and fragmentation indicators. For each study area and guild, a guild-specific land cover is built,
habitat patches are extracted by morphological analysis and connected with a Gabriel graph, each
link is routed as a least-cost path over a species-calibrated friction surface, and network and
corridor metrics are computed (Probability of Connectivity as equivalent connected area and share of habitat connected, sub-network
fragmentation, tortuosity, barriers and rupture points). The approach trades species-specific precision for
reproducibility on open global inputs. `[Certain]`

## 1. Context and objective

Map the ecological network ("Trame Verte et Bleue") of a territory from
satellite + open data, per functional guild, and produce per-entity layers usable for urban and
territorial planning (corridors to protect, barriers to mitigate, fragmentation to reduce).

Study areas produced (baselines): Toulouse, Nancy, Perpignan, Kourou (French Guiana),
La Roche-sur-Yon agglomeration (LRSY), PNR des Ardennes, La Rochelle agglomeration, and the SCOT
du Pays Yon et Vie (= LRSY + CC de Vie et Boulogne). Project-simulation scenarios (a drawn
polygon burned on top of every layer (WorldCover and OSM infrastructure) on its footprint,
then the pipeline re-run) exist for Perpignan and Toulouse
(vegetalisation projects). `[Certain]`

## 2. Data

- **Land cover**: ESA WorldCover v200, 10 m, pulled via Earth Engine (xee), over the AOI buffered
  by `2 * d0_max`.
- **Infrastructure**: OpenStreetMap (OSMnx): highways, railways, buildings, water bodies, plus
  managed artificial surfaces (airports, stadiums). Rasterized on top of WorldCover with a fixed
  priority order, producing extra codes 50-55 (51 buildings, 52 major roads/motorways, 53
  secondary roads, 54 paths, 55 railways) over the WorldCover codes (10 tree, 20 shrub, 30 grass,
  40 crop, 50 built, 60 bare, 80 water, 90 wetland, 95 mangrove).
- **Friction / dispersal calibration**: CEREMA La Rochelle 2025 (Tab. 8 p44, pp. 96-98).
- **CRS**: local metric UTM per AOI; all distances/areas in m / m2 / ha.

## 3. Functional guilds

Each guild is a functional syndrome (not a focal species, not a CEREMA sub-trame), named after a
CEREMA-calibrated reference species, defined by its habitat land-cover codes, characteristic
dispersal distance `d0` (links searched up to `2*d0`), per-code movement friction, and hard
barriers (friction `NaN` -> `inf`). Definitions live in `utils/species_params.py`. `[Certain]`

| guild | reference species | d0 (m) | habitat codes | hard barriers (NaN) |
|---|---|---:|---|---|
| ground_mammal | European hedgehog | 3000 | 10, 20, 30 | 51, 80 |
| arboreal_mammal | Red squirrel | 2000 | 10 | 51 |
| forest_edge_bird | Eurasian blackcap | 1500 | 10, 20 | none (buildings/roads finite) |
| ground_reptile | Common wall lizard | 750 | 30, 60 | 51, 80 |

Friction is calibrated on CEREMA La Rochelle, each WorldCover/OSM class taking the mean of the
CEREMA classes it aggregates (`papier/annexe_coefficients_friction.md`). Following CEREMA's finite
scale, roads are crossable at high cost (motorway/2x2 = 100, secondary = 50) so that road conflicts
surface as rupture points; hard barriers (`NaN`) are reserved for buildings (51) and large rivers
(80, terrestrial guilds only: OSM captures only large permanent water ~30 m wide). Habitat-code
friction is graduated on the CEREMA mean (always <= 3), not forced to 1; a code whose mean exceeds
3 is movement, not habitat (shrub, mean 4, removed from the reptile habitat). The fifth guild
(herbaceous_insect) was dropped: after alignment its habitat reduced to grass + bare, redundant
with ground_reptile, which CEREMA itself merges into a single herbaceous assemblage. `[Certain]`

## 4. Method

Orchestration: `run_pipeline.py <City> [--project <polygon>] [--guild <name>]` (project root)
iterates the 4 guilds (or a single one with `--guild`), calling `utils/sp_pipeline.py`. Per
(city, guild):

1. **Guild land cover**: clip WorldCover to the AOI + `2*d0` buffer, burn the OSM infrastructure
   on top (priority-ordered). `utils/landcover.py`.
2. **Habitat morphology (MSPA)**: binary habitat from the guild habitat codes; erosion-based split
   into biodiversity cores (>= 1 ha core area) and small-core stepping-stone islets (0.1-1 ha).
   `utils/connectivity.py`.
3. **Graph nodes**: patches become graph nodes; polygon outlines are smoothed (`smoothify`). A
   guard keeps any pathological mega-polygon (> 50 000 vertices) raw and logs it, to avoid a
   smoothing hang on a near-region-wide habitat blob.
4. **Gabriel graph**: edge-to-edge polygon distance, `max_dist = 2*d0`, diametral-circle pruning
   that excludes patches touching an endpoint (so an adjacent patch is not a false obstacle). Link
   probability `exp(-d/d0)`, cost `-log(prob)`. `utils/connectivity.py`.
5. **Theoretical PC**: Probability of Connectivity on straight-line distances, vectorized
   (scipy Dijkstra per connected component + numpy area-product matrix).
6. **Least-cost routing**: per-guild friction/resistance surface (barriers `NaN -> inf`); each
   Gabriel edge routed with `skimage.MCP_Geometric`. A link whose path has no finite cost, or a
   cost above `d0 * FRICTION_AVG_FAVORABLE` (= 3), is reclassified as a failed link.
   `utils/routing.py`. Two dispersal cost surfaces from all patches are exported: an unbounded
   continuous field (`dispersal_*.tif`) and a variant cut at the dispersal budget `d0 * 3`
   (`dispersal_bounded_*.tif`, the CEREMA "carte de dispersion" reach). Cost is in friction x
   metres, so CEREMA's `/resolution` term is absorbed by the metre-based MCP sampling.
7. **Failed links and rupture points**: failed links are split into `blocked` (hard obstacle) and
   `out_of_reach` (route exists but beyond the dispersal budget). Blocked links are enriched with the
   obstacle land-cover code(s) they cross and the rupture points (crossings with linear
   infrastructure); their geometry follows the real least-cost route up to the obstacle. Water (80) is
   reported as an obstacle for the guilds where it is a barrier; buildings (51) are excluded
   (areal, not a crossing point). `extract_rupture_points` / `enrich_failed_links_with_ruptures`.
8. **Real PC and planner-facing connectivity metrics**: PC on the realized least-cost network,
   expressed as equivalent connected area `ec_real_ha = sqrt(PC) * AOI area` (ha) and
   `connected_habitat_pct = ec_real_ha / habitat_ha_in_aoi` (share of habitat functioning as connected);
   loss read in hectares as `ec_theory_ha - ec_real_ha`; tortuosity `real_dist/theoretical_dist`. (Per-corridor dPC,
   edge betweenness, classification and pinch points are implemented but switched OFF in the
   current batch for compute cost: their columns are present but null.)
9. **Sub-networks (fragmentation)**: connected components of the realized (post-barrier) network.
   Counted on patches strictly inside the AOI (connectivity may pass through kept out-of-AOI
   patches, but only in-AOI patches count), threshold >= 3 patches. Exposed as
   `n_subnetworks` (realized), `n_subnetworks_theory` (same rule on the AOI-clipped Gabriel graph),
   `subnetworks_split_by_failed_links` (= realized - theoretical), `largest_subnetwork_size`, and a
   `subnetwork_id` per node. This isolates how much the failed links fragment the network.
10. **Planning segments**: corridors cut into the unique parts lying outside habitat patches (the
    land to act on), smoothed and welded.
11. **Isolated nodes**: patches with no successful corridor, kept only if strictly within the AOI.

**AOI handling.** The full graph (city + buffer) is kept in memory for routing, but the exported
line layers (edges, corridors, barriers, segments) are clipped to keep anything that touches the
AOI; out-of-AOI patches that anchor a kept line are retained so no line dead-ends at the boundary;
a patch is flagged isolated only if fully inside the AOI. The city AOI boundary is exported once
per baseline as `aoi_limits_<city>.geojson`.

**Outputs** per (city, guild), up to 12 files: 5 rasters (land cover, binary habitat, friction,
dispersal, dispersal_bounded), 6 vectors (nodes, edges, lcp corridors, barriers, isolated_nodes,
planning segments), 1 `stats.csv` of KPIs (`isolated_nodes` absent when 0 isolated patches). Documented field-by-field in `data/outputs/README.md`. Baselines under
`data/outputs/<City>/`, scenarios under `data/scenarios/<City>/<project-slug>/`.

**Scenarios.** `run_pipeline.py <City> --project <polygon>` burns the polygon's `class_code` into
the land cover, then runs the full pipeline, so a planted/vegetalised project can be compared to
the baseline with identical metrics.

## 5. Results

Per (city, guild) KPIs in `data/outputs/<city>/<guild>/stats_*.csv`. Read patterns observed in the
outputs (`[Inference]` from the produced data, not field-validated):
- Fragmentation tracks barriers and dispersal: `ground_reptile` (most barriers, short d0) shows
  many sub-networks and a low share of connected habitat; the forest guilds stay nearly
  connected (1-2 sub-networks).
- The patch-graph framing degenerates on near-continuous-habitat landscapes: a heavily forested
  PNR yields a single region-wide habitat core for the forest guilds, where "between-patch"
  connectivity loses meaning (see Limits). The PNR du Haut-Jura was attempted and abandoned for
  this reason.

PC is a landscape-scale index, not bounded to [0,1] here (normalisation by the strict AOI area can
exceed 1); use it for relative comparison, not as an absolute score. `[Certain]`

## 6. Limits and perspectives

- **No empirical validation**: frictions/dispersal are CEREMA proxies, not fitted to local
  occurrence data. `[Certain]`
- **Method-landscape mismatch**: the discrete patch-graph approach assumes a fragmented habitat in
  a hostile matrix; for near-continuous-habitat AOIs (forested PNR, broad-habitat guilds) it
  collapses to one mega-patch and the connectivity metrics become uninformative. Suited to
  fragmented (urban/peri-urban/agricultural) territories. `[Inference]`
- **Input resolution / aggregation**: WorldCover 10 m can be coarse for urban fabric; large water
  only (80) captured; OSM completeness varies. Movement inside habitat patches is treated as free,
  which can overestimate connectivity. `[Certain]`
- **Fences, walls and fine-scale barriers not modelled**: property fences, walls and fine-mesh
  grilles that block ground fauna (especially in urban tissue) are unknown at this scale and absent
  from the inputs, so on-the-ground permeability can be lower than modelled. Not mitigated (same
  data gap as CEREMA La Rochelle). `[Certain]`
- **Diffuse pressures not captured**: light/noise/chemical pollution, intensive garden management
  and human disturbance are not represented (no data). Unlike CEREMA La Rochelle, no site-management
  proxy (public / private / cemetery) is available, so any patch-quality measure is purely structural; swimming
  pools (a drowning-mortality sink CEREMA caught via CoSIA) are not captured either. Not mitigated. `[Certain]`
- **Canopy over impervious surfaces**: tree canopy overhanging concrete/asphalt is classified as
  tree (code 10), so a ground guild can read continuous habitat along tree-lined streets where the
  ground is impervious. Partly offset where OSM roads are burned over the canopy, not elsewhere
  (parking, courtyards absent from OSM). Top-down imagery (incl. Pléiades/Planet) cannot resolve it;
  only a height / LiDAR layer (e.g. IGN LiDAR HD) would. Not mitigated. `[Certain]`
- **Wetland and blue-trame (aquatic) not modelled**: deliberately out of scope. CEREMA itself
  handles the wetland sub-trame off-LCP (200 m dilation-erosion, no friction surface, no target
  species), and aquatic continuity needs a different method (longitudinal / lateral river
  continuity, hydraulic obstacles via the OFB ROE) and different species (amphibians, odonata,
  fish); WorldCover resolves wetland (90) and water (80) only coarsely. A known gap (no amphibian
  guild), to revisit with the appropriate data and method. `[Certain]`
- **Road traffic and width not modelled**: friction per road type is uniform across guilds (CEREMA
  finite scale: motorway/2x2 = 100, secondary = 50). Traffic volume, a key fragmentation driver, is
  unavailable; the OSM highway class (size) is the only proxy for it. `[Certain]`
- **Outputs are potentialities at a single instant T**: cores, stepping stones, corridors and
  rupture / black points are theoretical, derived from one land-cover snapshot. Corridors are
  potential movement axes, some may not be functional on the ground; results evolve as land cover
  changes. `[Certain]`
- **PC > 1 normalisation** to confirm against the scoping definition of the AOI (the in-AOI patch
  weighting bounds it to [0,1], but only on outputs regenerated with that fix). `[Assumption]`
- **Metrics off in the current batch**: node betweenness, dPC, edge betweenness, pinch points
  (compute cost); geometry, PC, sub-networks, tortuosity, counts are valid.
- **Perspectives**: field validation (GBIF/INPN occurrences), finer land cover (Green Urban Sat or
  national products), re-enable the corridor-importance metrics, interactive dashboard (in prep).

## 7. References

See `papier/litterature/etat_de_lart.md` (verify each source before citing; do not cite from
memory).
