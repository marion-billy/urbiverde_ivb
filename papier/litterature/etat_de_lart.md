# State of the art : urban ecological connectivity from satellite observation

> Reality Filter on: claims to be checked against the cited sources before they feed
> `methodo_paper.md`. Aligned with the implementation on 2026-06-19; full references with DOIs
> still to verify before formal citation.

## 1. Positioning

This project estimates ecological connectivity for several French urban areas, per functional
guild, from globally available satellite/open data (ESA WorldCover 10 m + OpenStreetMap), and
derives planning-ready corridors. It deliberately trades species-specific precision for global
reproducibility. `[Unverified]` (positioning claim, to confirm against the literature below)

## 2. Reference methods (to document)

- **Graph-based connectivity / Probability of Connectivity (PC, dPC)**: Saura & Pascual-Hortal
  (2007), Saura & Rubio (2010). Used here for PC theoretical/real and per-edge dPC. `[Unverified]`
- **Morphological Spatial Pattern Analysis (MSPA)**: Soille & Vogt (2009) (GUIDOS). Here a
  simplified erosion-based core/stepping-stone split. `[Unverified]`
- **Least-cost path / resistance surfaces**: Adriaensen et al. (2003); circuit theory and
  pinch points, McRae et al. (2008) (Circuitscape). Here MCP_Geometric for corridors; a vectorial
  current-flow / pinch-point approximation is implemented but disabled in the current batch
  (compute cost). `[Unverified]`
- **Network fragmentation**: number and size of connected components of the realized
  (post-barrier) network ("sub-networks"), compared to the pre-barrier graph to quantify the
  barrier effect; relates to graph-component / habitat-availability metrics (Saura). `[Unverified]`
- **Friction / dispersal calibration**: CEREMA La Rochelle (2025), Tab.8 p44 and pp.96-98.
  Primary calibration source for frictions and dispersal distances. `[Unverified]`
- **Land cover**: ESA WorldCover v200 (Zanaga et al.). OSM completeness for infrastructure. `[Unverified]`

## 3. Comparable data / approaches (to position against)

- CEREMA sub-trame ("cortege par sous-trame") approach vs the functional-guild approach chosen
  here (see `utils/species_params.py` header for the explicit distinction). `[Certain]`
- National products (OCS GE, BD Topo, RPG) offer finer land-cover granularity but are not
  globally available; the project argues this granularity has no spatial support in
  WorldCover 10 m + OSM. `[Certain]` (argument stated in code; ecological validity `[Unverified]`)

## 4. Gaps this work addresses / leaves open

- Addresses: reproducible multi-city connectivity from open global data, multi-guild.
- Leaves open: field validation (occurrence data GBIF/INPN), sub-class granularity, rail vs
  motorway separation, water-as-barrier assumption for terrestrial guilds. `[Certain]`
- Method scope: the discrete patch-graph framing fits fragmented (urban / peri-urban /
  agricultural) landscapes; on near-continuous-habitat AOIs (e.g. a heavily forested PNR for the
  forest guilds) it degenerates to a single mega-patch and the connectivity metrics lose meaning
  (observed on the PNR du Haut-Jura, which was abandoned for this reason). `[Inference]`

## 5. Sources to complete

(Add full references with DOIs once verified. Do not cite from memory.)
