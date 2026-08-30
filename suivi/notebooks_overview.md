# notebooks_overview.md: project corridor_project

> Generated on 2026-06-09 14:50 by `refresh_notebook_overview.py`. One Mermaid
> flow diagram per notebook, intermediate level: sources / files in,
> main steps, files out. Mechanical I/O detection; file names held in a
> variable appear by type (CSV, GeoTIFF).
> To be enriched via the AI prompt `prompts/notebook_overview.md`.

Legend: `[(file)]` = local file, `[/source/]` = external source,
`[step]` = notebook section, `-.->` = sequential chaining.

## `kourou_prod.ipynb`

**Ville de Kourou**  
_Summary: [to be completed by the AI]_

```mermaid
flowchart LR
  S0["0. Configuration"]
  S0src0[/"OSM"/] --> S0
  S0 --> S0w0[("...IR}/aoi_limits_{CITY}.geojson")]
  S1["1. Landcover"]
  S1 --> S1w0[("...PUT_DIR}/landcover_{CITY}.tif")]
  S0 -.-> S1
  S2["2. Habitat Morphology - MSPA"]
  S2 --> S2w0[("...IR}/binary_habitat_{CITY}.tif")]
  S1 -.-> S2
  S3["3.2. Theoretical PC index"]
  S3 --> S3w0[("{OUTPUT_DIR}/edges_{CITY}.json")]
  S2 -.-> S3
  S4["4. Least Cost Path Analysis"]
  S4 --> S4w0[("{OUTPUT_DIR}/friction_{CITY}.tif")]
  S4 --> S4w1[("...PUT_DIR}/dispersal_{CITY}.tif")]
  S3 -.-> S4
  S5["...idors metrics: dPC, ebc, current_flow"]
  S5 --> S5w0[("{OUTPUT_DIR}/lcp_{CITY}.json")]
  S5 --> S5w1[("...ments_amenagement_{CITY}.json")]
  S4 -.-> S5
  S6["4.4. Nodes metrics: nbc, (dPC)"]
  S6 --> S6w0[("...PUT_DIR}/nodes_{CITY}.geojson")]
  S6 --> S6w1[("...UT_DIR}/dpc_nodes_{CITY}.json")]
  S5 -.-> S6
```

## `lrsy_prod.ipynb`

**La Roche-sur-Yon Agglomération**  
_Summary: [to be completed by the AI]_

```mermaid
flowchart LR
  S0["0. Configuration"]
  S0r0[("...s/gee161025-533af22f806b.json")] --> S0
  S0src0[/"OSM"/] --> S0
  S0 --> S0w0[("...IR}/aoi_limits_{CITY}.geojson")]
  S1["1. Landcover"]
  S1 --> S1w0[("...PUT_DIR}/landcover_{CITY}.tif")]
  S0 -.-> S1
  S2["2. Habitat Morphology - MSPA"]
  S2 --> S2w0[("...IR}/binary_habitat_{CITY}.tif")]
  S1 -.-> S2
  S3["3.2. Theoretical PC index"]
  S3 --> S3w0[("{OUTPUT_DIR}/edges_{CITY}.json")]
  S2 -.-> S3
  S4["4. Least Cost Path Analysis"]
  S4 --> S4w0[("{OUTPUT_DIR}/friction_{CITY}.tif")]
  S4 --> S4w1[("...PUT_DIR}/dispersal_{CITY}.tif")]
  S3 -.-> S4
  S5["...idors metrics: dPC, ebc, current_flow"]
  S5 --> S5w0[("{OUTPUT_DIR}/lcp_{CITY}.json")]
  S5 --> S5w1[("...ments_amenagement_{CITY}.json")]
  S4 -.-> S5
  S6["4.4. Nodes metrics: nbc, (dPC)"]
  S6 --> S6w0[("...PUT_DIR}/nodes_{CITY}.geojson")]
  S6 --> S6w1[("...UT_DIR}/dpc_nodes_{CITY}.json")]
  S5 -.-> S6
```

## `my_custom_libs/overturemaps/examples/geopandas_example.ipynb`

**geopandas_example**  
_Summary: [to be completed by the AI]_

```mermaid
flowchart LR
  vide["(no I/O detected)"]
```

## `nancy_prod.ipynb`

**Métropole du Grand Nancy**  
_Summary: [to be completed by the AI]_

```mermaid
flowchart LR
  S0["0. Configuration"]
  S0r0[("...s/gee161025-533af22f806b.json")] --> S0
  S0src0[/"OSM"/] --> S0
  S0 --> S0w0[("...IR}/aoi_limits_{CITY}.geojson")]
  S1["1. Landcover"]
  S1 --> S1w0[("...PUT_DIR}/landcover_{CITY}.tif")]
  S0 -.-> S1
  S2["2. Habitat Morphology - MSPA"]
  S2 --> S2w0[("...IR}/binary_habitat_{CITY}.tif")]
  S1 -.-> S2
  S3["3.2. Theoretical PC index"]
  S3 --> S3w0[("{OUTPUT_DIR}/edges_{CITY}.json")]
  S2 -.-> S3
  S4["4. Least Cost Path Analysis"]
  S4 --> S4w0[("{OUTPUT_DIR}/friction_{CITY}.tif")]
  S4 --> S4w1[("...PUT_DIR}/dispersal_{CITY}.tif")]
  S3 -.-> S4
  S5["...etwork metrics: median tortuosity, PC"]
  S5 --> S5w0[("...PUT_DIR}/barriers_{CITY}.json")]
  S5 --> S5w1[("...es_{guild_key}_{CITY}.geojson")]
  S4 -.-> S5
  S6["...idors metrics: dPC, ebc, current_flow"]
  S6 --> S6w0[("{OUTPUT_DIR}/lcp_{CITY}.json")]
  S6 --> S6w1[("GeoJSON/GPKG")]
  S6 --> S6w2[("...ments_amenagement_{CITY}.json")]
  S5 -.-> S6
  S7["4.4. Nodes metrics: nbc, (dPC)"]
  S7 --> S7w0[("...PUT_DIR}/nodes_{CITY}.geojson")]
  S7 --> S7w1[("...UT_DIR}/dpc_nodes_{CITY}.json")]
  S6 -.-> S7
```

## `perpignan_prod.ipynb`

**Ville de Perpignan**  
_Summary: [to be completed by the AI]_

```mermaid
flowchart LR
  S0["0. Configuration"]
  S0r0[("...s/gee161025-533af22f806b.json")] --> S0
  S0src0[/"OSM"/] --> S0
  S0 --> S0w0[("...IR}/aoi_limits_{CITY}.geojson")]
  S1["1. Landcover"]
  S1 --> S1w0[("...PUT_DIR}/landcover_{CITY}.tif")]
  S0 -.-> S1
  S2["2. Habitat Morphology - MSPA"]
  S2 --> S2w0[("...IR}/binary_habitat_{CITY}.tif")]
  S1 -.-> S2
  S3["3.2. Theoretical PC index"]
  S3 --> S3w0[("{OUTPUT_DIR}/edges_{CITY}.json")]
  S2 -.-> S3
  S4["4. Least Cost Path Analysis"]
  S4 --> S4w0[("{OUTPUT_DIR}/friction_{CITY}.tif")]
  S4 --> S4w1[("...PUT_DIR}/dispersal_{CITY}.tif")]
  S3 -.-> S4
  S5["...idors metrics: dPC, ebc, current_flow"]
  S5 --> S5w0[("{OUTPUT_DIR}/lcp_{CITY}.json")]
  S5 --> S5w1[("...ments_amenagement_{CITY}.json")]
  S4 -.-> S5
  S6["4.4. Nodes metrics: nbc, (dPC)"]
  S6 --> S6w0[("...PUT_DIR}/nodes_{CITY}.geojson")]
  S6 --> S6w1[("...UT_DIR}/dpc_nodes_{CITY}.json")]
  S5 -.-> S6
```

## `tlse_prod.ipynb`

**Toulouse Métropole**  
_Summary: [to be completed by the AI]_

```mermaid
flowchart LR
  S0["0. Configuration"]
  S0src0[/"OSM"/] --> S0
  S0 --> S0w0[("...IR}/aoi_limits_{CITY}.geojson")]
  S1["1. Landcover"]
  S1 --> S1w0[("...PUT_DIR}/landcover_{CITY}.tif")]
  S0 -.-> S1
  S2["2. Habitat Morphology - MSPA"]
  S2 --> S2w0[("...IR}/binary_habitat_{CITY}.tif")]
  S1 -.-> S2
  S3["3.2. Theoretical PC index"]
  S3 --> S3w0[("{OUTPUT_DIR}/edges_{CITY}.json")]
  S2 -.-> S3
  S4["4. Least Cost Path Analysis"]
  S4 --> S4w0[("{OUTPUT_DIR}/friction_{CITY}.tif")]
  S4 --> S4w1[("...PUT_DIR}/dispersal_{CITY}.tif")]
  S3 -.-> S4
  S5["...idors metrics: dPC, ebc, current_flow"]
  S5 --> S5w0[("{OUTPUT_DIR}/lcp_{CITY}.json")]
  S5 --> S5w1[("...ments_amenagement_{CITY}.json")]
  S4 -.-> S5
  S6["4.4. Nodes metrics: nbc, (dPC)"]
  S6 --> S6w0[("...PUT_DIR}/nodes_{CITY}.geojson")]
  S6 --> S6w1[("...UT_DIR}/dpc_nodes_{CITY}.json")]
  S5 -.-> S6
```

