# Urban Ecological Connectivity / output data

This folder contains the connectivity analysis outputs of the `urbiverde_connectivity` pipeline: potential ecological corridors mapped per ecological profile and per city, from global satellite land cover (ESA WorldCover 10 m) + OpenStreetMap infrastructure.

For each city we model the landscape as a graph of habitat patches, connect them with least-cost paths through a friction surface specific to each ecological profile, and derive corridor and network metrics usable for urban planning.

> An interactive web dashboard built on these outputs is in preparation (mock-up stage). The link will be added here once it is available.

---

## 1\. Folder layout

```
outputs/<City>/<profile>/<artefact>_<profile>_<City>.<ext>
```

One `<profile>/` folder per (city, ecological profile), with the files described below (up to 12).

> **Planning scenarios.** A scenario tests a project's effect: you supply a project polygon (the area to vegetalize, pedestrianize, etc.), the chain burns it into the land cover, then recomputes all the connectivity. On the footprint, the drawn class overrides every layer (WorldCover replaced, OSM infrastructure clipped out inside), so a vegetalized avenue fully becomes habitat, not a road lined with greenery. Outputs have the same structure as the baseline ones, but under `data/scenarios/<City>/<project-slug>/<profile>/`, produced by `run_pipeline.py --project`.

**Territories (6).** The analysis perimeter (AOI) is the territory's own, of a type that varies:

| Territory | AOI (administrative perimeter) | Area |
|---|---|---|
| Toulouse | Toulouse Métropole | 461 km² |
| Nancy | Métropole du Grand Nancy | 143 km² |
| Perpignan | commune (city) | 68 km² |
| La Roche-sur-Yon | communauté d'agglomération | 502 km² |
| La Rochelle | communauté d'agglomération | 331 km² |
| Kourou | rectangular extent (bbox), French Guiana | 123 km² |

**Ecological profiles (4):** see table below.

### CRS

All vector layers and rasters are in the **local metric UTM** of each city (e.g. Perpignan = EPSG:32631). Distances/areas are in metres / m² / hectares. Reproject to EPSG:4326 only for web display.

---

## 2\. Ecological profiles

Each ecological profile is a group of species sharing habitats, barriers, frictions, dispersal behaviour. It defines which land-cover classes are habitat and how far the species disperses (`d0`). Corridors are searched up to `2 * d0`.

| ecological profile             | reference species (Cerema Sud-Ouest 2025 anchor)               | d0 (m) | max link (m) | habitat land-cover codes | barriers (impassable codes) |
|-----------------|-----------------------------------------------|------|------------|------------------------|---------------------------|
| ground_mammal     | European hedgehog (Erinaceus europaeus)         | 3000   | 6000         | 10, 20, 30               | 51, 80                      |
| arboreal_mammal   | Red squirrel (Sciurus vulgaris)                 | 2000   | 4000         | 10                       | 51                          |
| forest_edge_bird  | Eurasian blackcap (Sylvia atricapilla)          | 1500   | 3000         | 10, 20                   | none (buildings/roads finite) |
| ground_reptile    | Common wall lizard (Podarcis muralis)           | 750    | 1500         | 30, 60                   | 51, 80                      |

`d0` is the species' characteristic dispersal distance; link probability between two patches is `exp(-distance / d0)`. **Hard barriers** (infinite friction) are land-cover codes the ecological profile cannot cross: buildings (51) and large rivers (80, terrestrial ecological profiles only). Unlike buildings (51) and large rivers (80), which are **impassable** barriers (infinite friction), **roads** get a high but **finite** friction (Cerema Sud-Ouest 2025 scale: motorway/2x2 = 100, secondary = 50). A corridor can therefore cross a road, at high cost; the crossing point is then flagged as a **rupture point** (a conflict to address), rather than blocking the passage entirely. Every other code is crossable at a per-ecological profile movement cost (the friction). The **reference species** is the anchor calibrated by Cerema Sud-Ouest (2025), used to name the ecological profile (illustrative; the ecological profile stands for the functional syndrome shared by several species, not that single species).

---

## 3\. Land-cover codes

Base = ESA WorldCover v200 (10 m). OSM infrastructure is burned on top (codes 51-55).

| code | meaning                  | base       |
|----|------------------------|----------|
| 10   | Tree cover               | WorldCover |
| 20   | Shrubland                | WorldCover |
| 30   | Grassland                | WorldCover |
| 40   | Cropland                 | WorldCover |
| 50   | Built-up                 | WorldCover |
| 60   | Bare / sparse vegetation | WorldCover |
| 80   | Permanent water          | WorldCover |
| 90   | Herbaceous wetland       | WorldCover |
| 95   | Mangroves                | WorldCover |
| 51   | Buildings                | OSM        |
| 52   | Major roads / motorways  | OSM        |
| 53   | Secondary roads          | OSM        |
| 54   | Paths / tracks           | OSM        |
| 55   | Railways                 | OSM        |

In the friction surface each code maps to a movement cost; some are **impassable barriers** (infinite cost). Friction is calibrated per ecological profile (Cerema, direction territoriale Sud-Ouest (JAMIN F. & RAUEL V.), 2025, *Identification des continuités écologiques urbaines, Communauté d'agglomération de La Rochelle*, CeremaDoc); see `utils/species_params.py` in the code repo. The file `species_params.csv` in this folder lists every per-profile parameter (d0, friction per land-cover code, habitat and barrier codes, reference species, references).

---

## 4\. Files per (city, ecological profile)

Up to 12 files per ecological profile folder: 5 rasters (`.tif`) + 5 vector layers (`.geojson`) + 1 table
(`.csv`) + 1 manifest (`.json`). `failed_links_*.geojson` is optional (absent when the profile has no failed
link), so a folder may hold fewer.

### Rasters (GeoTIFF, 10 m, UTM)

| file                 | what it is                                                                                     |
|--------------------|----------------------------------------------------------------------------------------------|
| landcover_*.tif      | Ecological profile land-cover grid: WorldCover with OSM infrastructure burned in (uint8 codes above).       |
| binary_habitat_*.tif | 1 = habitat for this ecological profile, 0 = non-habitat.                                                   |
| friction_*.tif       | Movement cost surface used for least-cost paths (high = hard to cross; barriers are infinite). |
| dispersal_*.tif      | Accumulated-cost dispersal surface from all habitat patches, clipped to the AOI but **not capped**: each pixel's least-cost distance to the nearest habitat (lower = more reachable). The uncapped companion of `dispersal_bounded`. |
| dispersal_bounded_*.tif | Same accumulated-cost dispersal surface but **cut at the dispersal budget** `d0 * 3` (Cerema-like reach): lower = more easily reached; pixels beyond the budget (or unreachable) are nodata. |

### Vector layers (GeoJSON, UTM)

**`nodes_*.geojson`** - habitat patches (graph nodes), polygons.

| field         | meaning                                                               |
|-------------|---------------------------------------------------------------------|
| node_id       | patch id; matches node_1/node_2 in edges/lcp/failed_links (the graph id). |
| node_type     | `core` (interior core >= 1 ha, biodiversity reservoir) or `islet` (smaller patch, no qualifying core: stepping stone). |
| class         | finer label: `Core (Noyau)` (= node_type core); or, for islets, `Stepping Stone (Small Core)` (small core, 0 < core < 1 ha) and `Stepping Stone (Islet)` (no core, patch >= 0.1 ha). A patch with a core below 1 ha is thus node_type `islet` and class Stepping Stone (Small Core). |
| subnetwork_id | id of the connected sub-network this patch belongs to in the realized (post-barrier) network; null if the patch is isolated or not in a sub-network of >=3 in-AOI patches. |
| total_area_ha | total patch area (ha).                                                |
| max_core_ha   | largest interior "core" area within the patch (ha).                   |
| x, y          | representative point (UTM).                                           |
| nbc_score     | node betweenness (hub score). Currently disabled → null.              |

> Patches shown can extend slightly outside the city AOI when they anchor a kept corridor

**`edges_*.geojson`** - the connectivity graph (Gabriel graph): potential links between patches, straight lines patch-to-patch.

| field          | meaning                                            |
|--------------|--------------------------------------------------|
| node_1, node_2 | the two connected patch ids.                       |
| dist_m         | edge-to-edge distance between the two patches (m). |
| cost_log       | -log(exp(-dist/d0)) = link cost used by the graph. |

**`lcp_*.geojson`** - the realised corridors: least-cost paths for the **successful** links (routed through the friction surface), lines.

| field                                                         | meaning                                                             |
|-------------------------------------------------------------|-------------------------------------------------------------------|
| node_1, node_2                                                | connected patches.                                                  |
| status                                                        | success.                                                            |
| theoretical_dist                                              | straight-line (Euclidean) distance (m).                             |
| real_dist                                                     | length of the least-cost path actually traced (m).                  |
| accumulated_cost                                              | total friction cost along the path.                                 |
| efficiency                                                    | theoretical_dist / real_dist (1 = straight; lower = more detour).   |
| tortuosity                                                    | real_dist / theoretical_dist (1 = straight; higher = more winding). |
| dPC_val, dPC_relative, ebc_score, category, pinch_point_score | corridor-importance metrics. Currently disabled → null.             |

**`failed_links_*.geojson`** - the **failed** links (a corridor was wanted but could not be realised). Both `blocked` and `out_of_reach` links are traced along their real least-cost route: `blocked` up to the softened obstacle (where the rupture point is placed), `out_of_reach` a full route whose cost exceeds the dispersal budget `d0 * 3`. Only `node_not_found` (rare, technical) keeps the straight desire line. The dashboard no longer shows failed links; they are kept here for analysis.

| field                                                     | meaning                                                                                                                                                         |
|---------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
| node_1, node_2                                            | the two patches that could not be connected.                                                                                                                    |
| status                                                    | failed.                                                                                                                                                         |
| fail_reason                                               | blocked (no finite path: a hard obstacle separates them), out_of_reach (a path exists but beyond the dispersal budget), or node_not_found (technical lookup failure). |
| theoretical_dist, real_dist, accumulated_cost, efficiency | as in lcp (may be NaN if no path).                                                                                                                              |
| obstacle                                                  | land-cover code(s) of the blocking feature(s), comma-joined (e.g. 52 = major road, 80 = water). Water (80) is reported for the ecological profiles where it is a barrier (ground_mammal, ground_reptile); buildings (51) are excluded (areal, not a crossing point).                                                                 |
| n_ruptures                                                | number of obstacle crossings detected on the link.                                                                                                              |



**`corridor_segments_*.geojson`** - corridors cut into unique segments, keeping the parts that lie **outside** habitat patches (the corridor portions in the matrix, aggregated by how many corridors overlap), lines. Purely geometric (clipped + aggregated), not a planning prescription.

| field                             | meaning                                                                        |
|---------------------------------|------------------------------------------------------------------------------|
| segment_id                        | segment id.                                                                    |
| corridor_count                    | number of corridors overlapping this segment (higher = more shared/important). |
| sum_dPC, max_ebc, max_pinch_point | aggregated importance metrics. Currently disabled → 0/null.                    |

> Note: segment geometry smoothing is still imperfect (occasional staircase/zigzag artefacts from the 10 m raster). It does not affect which segments exist or `corridor_count`.

### `stats_*.csv` - one row of city/ecological profile KPIs

| field                              | meaning                                                                                          |
|----------------------------------|------------------------------------------------------------------------------------------------|
| nb_nodes                           | patches kept for the city.                                                                       |
| isolated_nodes_count               | patches with no working corridor.                                                                |
| cores_count, islets_count          | reservoirs vs small stepping stones detected (full buffered extent).                             |
| n_subnetworks_theory               | potential sub-networks (connected components with >=3 patches inside the AOI) before barriers (Gabriel graph). |
| n_subnetworks                      | realized sub-networks (>=3 patches inside the AOI) after barriers cut links (effective fragmentation). |
| subnetworks_split_by_failed_links      | n_subnetworks - n_subnetworks_theory: net sub-networks added by failed links (patches fully cut off drop to isolated_nodes_count instead). |
| largest_subnetwork_size            | number of in-AOI patches in the biggest realized sub-network.                                    |
| nb_corridors                       | successful corridors.                                                                            |
| nb_failed_corridors                | failed links (failed corridors).                                                                         |
| pc_theory                          | Probability of Connectivity on straight-line distances (potential connectivity).                 |
| pc_real                            | PC using real least-cost paths (effective connectivity through the real landscape).              |
| ec_theory_ha, ec_real_ha           | equivalent connected area = sqrt(PC) * AOI area (ha): the size of one fully-connected patch giving the same PC (theoretical vs realized). Planner-facing headline. |
| connected_habitat_pct              | ec_real_ha / habitat_ha_in_aoi * 100 = share of in-AOI habitat that functions as connected (0-100, linear). |
| connectivity_loss_pct              | (pc_theory - pc_real) / pc_theory * 100. **No longer considered relevant**: a % loss of an abstract index means little to planners. Kept in the outputs but to be ignored; prefer ec_*_ha / connected_habitat_pct. |
| median_tortuosity, mean_tortuosity | corridor winding (real/theoretical).                                                             |

### `manifest_*.json` - provenance of this output set

Written at the end of each run. Records what produced the folder, so a set can be traced back without an external log: generation timestamp, city and ecological profile, CRS, git commit and whether the working tree was clean, Python and platform, the versions of the ten main libraries, and every parameter of the computation (`d0`, AOI buffer, habitat codes, the full friction table, cost budget, core and islet thresholds, sub-network threshold).

> The file carries a timestamp, so exclude it from any byte-for-byte reproducibility check: `diff -r -x 'manifest_*.json'`.

> **Read these indices relatively.** PC (Probability of Connectivity) is a **relative** landscape index, not bounded to \[0,1\] (normalisation by the strict AOI can exceed 1): its absolute value is meaningless on its own, it is for **comparison** (profiles, cities, before/after a scenario). `ec_real_ha` (equivalent connected area, a modelling construct, not a real patch) and `connected_habitat_pct` (= EC / in-AOI habitat) inherit this and depend on the AOI: read them relatively too. `connectivity_loss_pct` is no longer considered relevant.

---

## 5\. Methodology

Per (city, ecological profile): build the ecological profile land cover (WorldCover + OSM) → extract habitat patches by morphological analysis (MSPA: cores ≥ 1 ha core area, stepping stones 0.1-1 ha) → connect patches with a **Gabriel graph** (links within `2 * d0`) → compute the theoretical Probability of Connectivity → route each link as a **least-cost path** over the friction surface (`skimage.MCP_Geometric`) within a cost budget `d0 * 3`. Successful links are exported as `lcp`; links with no finite path or beyond the budget become `failed_links` (fail_reason: blocked / out_of_reach / node_not_found). A bounded dispersal surface (`dispersal_bounded`) is masked at the same budget. Finally the chain computes network/corridor metrics, cuts corridors into `corridor_segments`, and writes per-profile KPIs to `stats.csv`.


---

## 6\. How to open / compare

- **QGIS / ArcGIS**: drag the `.geojson` and `.tif` (set the project CRS to the city UTM).

- **Python**: `geopandas.read_file(...)` for vectors, `rioxarray.open_rasterio(...)` for rasters.

- **Comparing with your own results**: align on the same ecological profile definition (habitat codes + `d0` under *Ecological profiles*), the same land-cover codes (under *Land-cover codes*), and the same CRS. PC is a relative index, so compare deltas / rankings rather than absolute values.

---

## 7\. Caveats

**Methodological and ecological limitations**

- Source: ESA WorldCover v200 + OSM (snapshot at run time, June 2026). Friction calibrated on Cerema Sud-Ouest (2025, La Rochelle) references, no empirical validation.
- **Habitat patches are qualified structurally, not ecologically.** Cores vs stepping stones (`node_type`, `class`, `max_core_ha`) come from patch size and compactness only (MSPA morphology), not from habitat quality: diffuse pressures (light and noise pollution, disturbance, management, domestic predators) are not captured, so a large compact core can overlie degraded habitat. A multicriteria quality qualification was planned but reduced to the morphological criterion for this batch.
- Movements inside habitat patches are considered free, which can overestimate connectivity.
- Resolution can be too coarse for urban environments; iterate with Green Urban Sat or a more detailed land cover?

**Notes on this data batch and the dashboard**

- **Failed links are no longer shown on the dashboard**; this folder keeps all of them (in `failed_links_*.geojson`) for analysis.
- Metrics **disabled in this batch** (columns present but null/0): node betweenness (`nbc_score`), corridor importance (`dPC_*`, `ebc_score`, `category`, `pinch_point_score`, segment `sum_dPC`/ `max_ebc`/`max_pinch_point`). They were switched off for compute cost; the geometry and basic metrics (distances, tortuosity, PC, counts) are valid.
- Sub-network fields (`subnetwork_id`, `n_subnetworks`, `n_subnetworks_theory`, `subnetworks_split_by_failed_links`, `largest_subnetwork_size`) are present in **all current outputs**. A sub-network is a connected component of the realized (post-barrier) network with **>=3 patches inside the AOI**; connectivity may pass through kept out-of-AOI patches, but only in-AOI patches are counted (so `largest_subnetwork_size <= nb_nodes`).
- Segment smoothing is approximate (see note above).
