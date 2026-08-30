# Friction alignment proposal — species_params vs CEREMA La Rochelle (v2, discussed)

> STATUS: APPLIED 2026-06-26 in `utils/species_params.py`. Canonical doc =
> `papier/annexe_coefficients_friction.md`. Two final decisions beyond the tables below:
> herbaceous_insect guild DROPPED (5 -> 4 guilds), and ground_reptile grass kept at 1 (optimum).
> This file is kept as the working trace of the discussion.

Method: each WorldCover/OSM code is mapped to the CEREMA land-cover row(s) it aggregates, and the
per-species friction is the MEAN of those rows (couleuvre dropped; not one of our guilds).
Deliberate deviations from CEREMA are flagged.

## Locked decisions
- **Scale**: CEREMA finite scale on roads. `motorway (52)` -> 100, `secondary (53)` -> 50.
  Buildings `OSM_build (51)` stay BARRIER (NaN) for all guilds except the bird (100): a corridor
  through a building "does not exist"; a corridor across a road is meaningful (-> precise rupture).
- **Water (80)** stays BARRIER for the strictly terrestrial guilds (ground_mammal, ground_reptile)
  AND insect: our OSM water = large rivers only (~30 m), genuinely impassable (not CEREMA's small
  streams). Squirrel/bird keep a finite value (swim / fly).
- **built (50)** = inter-building impervious matrix (dense buildings already captured as 51).
  Maps to CEREMA "artificialise" row. Kept ~10 for all terrestrial (deviation: lizard CEREMA 3 ->
  kept 10, do NOT signal built as favorable in an urban de-fragmentation tool), 100 for insect.
  arboreal lowered 50 -> 10 (built was = road 50, an anomaly; CEREMA squirrel artificialise ~8 ~= sols nus).
- **Habitat = friction <= 3** (CEREMA: milieu de vie 1, favorable 2-3, transit >= 4). Habitat codes
  graduated to their averaged CEREMA value (all <= 3). Codes whose averaged value is > 3 are NOT
  habitat: **shrub (20) removed from ground_reptile and herbaceous_insect habitat** (avg 4 and 5).
- **wetland (90) / mangrove (95)**: no CEREMA terrestrial row (humide sub-trame handled off-LCP).
  Inferred from the mean of the water classes {surfaces en eau, cours d'eau, fosses & noues, canaux
  de marais}: ~8 terrestrial, ~52 insect. Stays finite (marsh is passable, unlike a large river).

## Proposed values per guild (current -> proposed)

### arboreal_mammal — habitat [10] (unchanged)
| code | lc | current | proposed | note |
|---|---|--:|--:|---|
| 10 | tree | 1 | 1 | habitat |
| 20 | shrub | 6 | 6 | |
| 30 | grass | 4 | 4 | |
| 40 | crop | 8 | 7 | avg CEREMA |
| 50 | built | 50 | 10 | lowered (was = road; CEREMA ~8) |
| 60 | bare | 10 | 10 | |
| 80 | water | 9 | 9 | finite (swims) |
| 90 | wetland | 9 | 8 | inferred water-classes |
| 95 | mangrove | 9 | 8 | inferred (Kourou-only) |
| 51 | OSM_build | BARRIER | BARRIER | |
| 52 | OSM_motorway | BARRIER | 100 | finite scale |
| 53 | OSM_secondary | 50 | 50 | |
| 54 | OSM_path | 8 | 8 | |
| 55 | OSM_rail | 9 | 9 | |

### forest_edge_bird — habitat [10, 20] (unchanged)
| code | lc | current | proposed | note |
|---|---|--:|--:|---|
| 10 | tree | 1 | 2 | graduate (CEREMA boisement 2) |
| 20 | shrub | 1 | 1 | habitat (optimum) |
| 30 | grass | 7 | 7 | |
| 40 | crop | 8 | 6 | avg CEREMA |
| 50 | built | 10 | 10 | |
| 60 | bare | 10 | 10 | |
| 80 | water | 7 | 7 | finite (flies) |
| 90 | wetland | 7 | 6 | inferred |
| 95 | mangrove | 7 | 6 | inferred |
| 51 | OSM_build | 100 | 100 | flies over |
| 52 | OSM_motorway | 100 | 100 | |
| 53 | OSM_secondary | 50 | 50 | |
| 54 | OSM_path | 6 | 8 | avg CEREMA |
| 55 | OSM_rail | 7 | 7 | |

### ground_reptile — habitat [20, 30, 60] -> [30, 60]  (shrub removed)
| code | lc | current | proposed | note |
|---|---|--:|--:|---|
| 10 | tree | 8 | 4 | avg CEREMA |
| 20 | shrub | 1 | 4 | REMOVED from habitat -> transit (CEREMA 4) |
| 30 | grass | 1 | 2 | graduate |
| 40 | crop | 6 | 5 | avg CEREMA |
| 50 | built | 10 | 10 | deviation (CEREMA 3; do not valorize built) |
| 60 | bare | 1 | 3 | graduate |
| 80 | water | BARRIER | BARRIER | large rivers |
| 90 | wetland | 10 | 8 | inferred |
| 95 | mangrove | 10 | 8 | inferred |
| 51 | OSM_build | BARRIER | BARRIER | |
| 52 | OSM_motorway | BARRIER | 100 | finite scale |
| 53 | OSM_secondary | BARRIER | 50 | align CEREMA routes |
| 54 | OSM_path | 3 | 3 | |
| 55 | OSM_rail | 3 | 3 | |

### herbaceous_insect — habitat [20,30,60,90,95] -> [30, 60]  (shrub removed; 90/95 PENDING)
| code | lc | current | proposed | note |
|---|---|--:|--:|---|
| 10 | tree | 8 | 8 | |
| 20 | shrub | 1 | 5 | REMOVED from habitat -> transit (CEREMA 5) |
| 30 | grass | 1 | 1 | habitat (optimum) |
| 40 | crop | 5 | 5 | |
| 50 | built | 10 | 100 | CEREMA ortho artificialise = 100 |
| 60 | bare | 1 | 3 | graduate |
| 80 | water | 10 | BARRIER | large rivers (consistency) |
| 90 | wetland | 1 | **52** | PENDING: inferred (flooded marsh != open-habitat ortho) -> drop 90 from habitat. Else keep 1. |
| 95 | mangrove | 1 | **52** | PENDING: same; Kourou-only |
| 51 | OSM_build | BARRIER | BARRIER | |
| 52 | OSM_motorway | 100 | 100 | |
| 53 | OSM_secondary | 50 | 50 | |
| 54 | OSM_path | 2 | 2 | |
| 55 | OSM_rail | 3 | 3 | |

### ground_mammal — habitat [10, 20, 30] (unchanged)
| code | lc | current | proposed | note |
|---|---|--:|--:|---|
| 10 | tree | 1 | 1 | habitat |
| 20 | shrub | 1 | 1 | habitat |
| 30 | grass | 1 | 2 | graduate (CEREMA prairie 2) |
| 40 | crop | 7 | 6 | avg CEREMA |
| 50 | built | 10 | 10 | |
| 60 | bare | 10 | 10 | |
| 80 | water | BARRIER | BARRIER | large rivers |
| 90 | wetland | 9 | 8 | inferred |
| 95 | mangrove | 9 | 8 | inferred |
| 51 | OSM_build | BARRIER | BARRIER | |
| 52 | OSM_motorway | BARRIER | 100 | finite scale |
| 53 | OSM_secondary | 50 | 50 | |
| 54 | OSM_path | 5 | 5 | |
| 55 | OSM_rail | 10 | 10 | |

## Open decision
- **insect wetland/mangrove (90/95)**: adopt 52 + drop 90/95 from insect habitat (habitat -> [30,60]),
  OR keep 1 as habitat. Low impact (wetland rare outside La Rochelle marais).
