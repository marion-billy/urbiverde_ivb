# Connectivité écologique urbaine / données de sortie

Ce dossier contient les sorties de l'analyse de connectivité de la chaîne `urbiverde_connectivity` : des corridors écologiques potentiels cartographiés par profil écologique et par ville, à partir d'une occupation du sol satellitaire mondiale (ESA WorldCover 10 m) et des infrastructures OpenStreetMap.

Pour chaque ville, le paysage est modélisé comme un graphe de taches d'habitat, reliées par des chemins de moindre coût à travers une surface de friction propre à chaque profil écologique, d'où sont dérivées des métriques de corridors et de réseau exploitables pour l'aménagement urbain.

> Un tableau de bord web interactif fondé sur ces sorties est en préparation (stade maquette). Le lien sera ajouté ici une fois disponible.

---

## 1. Organisation du dossier

```
outputs/<Ville>/<profil>/<artefact>_<profil>_<Ville>.<ext>
```

Un dossier `<profil>/` par couple (ville, profil écologique), avec les fichiers décrits en section 4 (jusqu'à 14).

> **Scénarios d'aménagement.** Un scénario teste l'effet d'un projet : on fournit un polygone de projet (zone à végétaliser, piétonniser, etc.), la chaîne le brûle dans l'occupation du sol, puis recalcule toute la connectivité. Sur l'emprise du polygone, la classe dessinée écrase toutes les couches (WorldCover remplacé, infrastructure OSM découpée à l'intérieur), si bien qu'une avenue végétalisée devient entièrement de l'habitat, et non une route bordée de verdure. Les sorties ont la même structure que les sorties de base, mais dans `data/scenarios/<Ville>/<slug-du-projet>/<profil>/`, produites par `run_pipeline.py --project`.

**Territoires (6).** Le périmètre d'analyse (AOI) est celui du territoire, de type variable selon le cas :

| Territoire | Périmètre (AOI) | Aire |
|---|---|---|
| Toulouse | Toulouse Métropole | 461 km² |
| Nancy | Métropole du Grand Nancy | 143 km² |
| Perpignan | commune (ville) | 68 km² |
| La Roche-sur-Yon | communauté d'agglomération | 502 km² |
| La Rochelle | communauté d'agglomération | 331 km² |
| Kourou | emprise rectangulaire (Guyane) | 123 km² |

**Profils écologiques (4) :** voir le tableau ci-dessous.

### Système de coordonnées (CRS)

Toutes les couches vectorielles et les rasters sont dans l'**UTM métrique local** de chaque ville (par exemple Perpignan = EPSG:32631). Distances et surfaces sont en mètres / m² / hectares. Ne reprojeter en EPSG:4326 que pour l'affichage web.

---

## 2. Profils écologiques

Un profil écologique est un groupe d'espèces partageant habitats, obstacles, frictions et comportement de dispersion. Il définit quelles classes d'occupation du sol sont de l'habitat et jusqu'où l'espèce se disperse (`d0`). Les corridors sont recherchés jusqu'à `2 * d0`.

| profil écologique | espèce de référence (ancrage Cerema Sud-Ouest 2025) | d0 (m) | lien max (m) | codes habitat | obstacles (codes infranchissables) |
|---|---|---|---|---|---|
| ground_mammal    | Hérisson d'Europe (Erinaceus europaeus) | 3000 | 6000 | 10, 20, 30 | 51, 80 |
| arboreal_mammal  | Écureuil roux (Sciurus vulgaris)        | 2000 | 4000 | 10         | 51 |
| forest_edge_bird | Fauvette à tête noire (Sylvia atricapilla) | 1500 | 3000 | 10, 20 | aucun (bâti/routes en coût fini) |
| ground_reptile   | Lézard des murailles (Podarcis muralis) | 750  | 1500 | 30, 60 | 51, 80 |

`d0` est la distance caractéristique de dispersion de l'espèce ; la probabilité de lien entre deux taches vaut `exp(-distance / d0)`. Les **obstacles durs** (friction infinie) sont les codes d'occupation du sol que le profil ne peut franchir : bâtiments (51) et grandes rivières (80, profils terrestres seulement). Contrairement aux bâtiments (51) et aux grandes rivières (80), qui sont des obstacles **infranchissables** (friction infinie), les **routes** reçoivent une friction élevée mais **finie** (échelle Cerema Sud-Ouest 2025 : autoroute/2×2 = 100, route secondaire = 50). Un corridor peut donc traverser une route, à coût élevé ; l'endroit du franchissement est alors signalé comme **point de rupture** (un point de conflit à traiter), au lieu de bloquer totalement le passage. Tout autre code est franchissable à un coût de déplacement propre au profil (la friction). L'**espèce de référence** est l'ancrage calibré par le Cerema Sud-Ouest (2025), utilisé pour nommer le profil (illustratif ; le profil représente le syndrome fonctionnel partagé par plusieurs espèces, non cette seule espèce).

---

## 3. Codes d'occupation du sol

Base = ESA WorldCover v200 (10 m). Les infrastructures OSM sont brûlées par-dessus (codes 51-55).

| code | signification | base |
|---|---|---|
| 10 | Couvert arboré | WorldCover |
| 20 | Arbustes | WorldCover |
| 30 | Prairies | WorldCover |
| 40 | Cultures | WorldCover |
| 50 | Bâti | WorldCover |
| 60 | Sols nus / végétation clairsemée | WorldCover |
| 80 | Eaux permanentes | WorldCover |
| 90 | Zones humides herbacées | WorldCover |
| 95 | Mangroves | WorldCover |
| 51 | Bâtiments | OSM |
| 52 | Routes principales / autoroutes | OSM |
| 53 | Routes secondaires | OSM |
| 54 | Chemins / sentiers | OSM |
| 55 | Voies ferrées | OSM |

Dans la surface de friction, chaque code correspond à un coût de déplacement ; certains sont des **obstacles infranchissables** (coût infini). La friction est calibrée par profil écologique (Cerema, direction territoriale Sud-Ouest (JAMIN F. & RAUEL V.), 2025, *Identification des continuités écologiques urbaines, Communauté d'agglomération de La Rochelle*, CeremaDoc) ; voir `utils/species_params.py` dans le dépôt de code. Le fichier `species_params.csv` de ce dossier reprend tous les paramètres par profil (d0, friction par code d'occupation du sol, codes habitat et barrières, espèce de référence, références).

---

## 4. Fichiers par (ville, profil écologique)

Jusqu'à 12 fichiers par dossier de profil : 5 rasters (`.tif`) + 5 couches vectorielles (`.geojson`) + 1 table (`.csv`) + 1 manifeste (`.json`). `failed_links_*.geojson` est optionnel (absent quand le profil n'a aucun lien en échec) ; un dossier peut donc en contenir moins.

### Rasters (GeoTIFF, 10 m, UTM)

| fichier | contenu |
|---|---|
| landcover_*.tif | Grille d'occupation du sol du profil : WorldCover avec infrastructures OSM brûlées (codes uint8 ci-dessus). |
| binary_habitat_*.tif | 1 = habitat pour ce profil, 0 = non-habitat. |
| friction_*.tif | Surface de coût de déplacement utilisée pour les chemins de moindre coût (élevé = difficile à franchir ; obstacles infinis). |
| dispersal_*.tif | Surface de dispersion en coût cumulé depuis toutes les taches d'habitat, découpée à l'AOI mais **non plafonnée** : pour chaque pixel, le coût de moindre chemin jusqu'à l'habitat le plus proche (plus bas = plus accessible). La version non plafonnée de `dispersal_bounded`. |
| dispersal_bounded_*.tif | La même surface de dispersion en coût cumulé mais **coupée au budget de dispersion** `d0 * 3` (portée à la Cerema) : plus bas = plus facilement atteint ; les pixels au-delà du budget (ou inatteignables) sont nodata. |

### Couches vectorielles (GeoJSON, UTM)

**`nodes_*.geojson`** : taches d'habitat (nœuds du graphe), polygones.

| champ | signification |
|---|---|
| node_id | identifiant de tache ; correspond à node_1/node_2 dans edges/lcp/failed_links (l'identifiant du graphe). |
| node_type | `core` (noyau : cœur intérieur ≥ 1 ha, réservoir de biodiversité) ou `islet` (tache plus petite, sans cœur qualifiant : relais / pas japonais). |
| class | étiquette plus fine : `Core (Noyau)` (= node_type core) ; ou, pour les îlots, `Stepping Stone (Small Core)` (petit cœur, 0 < cœur < 1 ha) et `Stepping Stone (Islet)` (aucun cœur, tache ≥ 0,1 ha). Une tache avec un cœur inférieur à 1 ha est donc node_type `islet` et class « Stepping Stone (Small Core) ». |
| subnetwork_id | identifiant du sous-réseau connecté auquel la tache appartient dans le réseau réalisé (post-obstacles) ; null si la tache est isolée ou hors d'un sous-réseau d'au moins 3 taches dans l'AOI. |
| total_area_ha | surface totale de la tache (ha). |
| max_core_ha | plus grande surface de "cœur" interne dans la tache (ha). |
| x, y | point représentatif (UTM). |
| nbc_score | intermédiarité du nœud (score de hub). Actuellement désactivé -> null. |

> Les taches affichées peuvent déborder légèrement de l'AOI de la ville lorsqu'elles ancrent un corridor retenu.

**`edges_*.geojson`** : le graphe de connectivité (graphe de Gabriel) : liens potentiels entre taches, lignes droites de tache à tache.

| champ | signification |
|---|---|
| node_1, node_2 | les deux taches reliées. |
| dist_m | distance bord à bord entre les deux taches (m). |
| cost_log | -log(exp(-dist/d0)) = coût de lien utilisé par le graphe. |

**`lcp_*.geojson`** : les corridors réalisés : chemins de moindre coût pour les liens **réussis** (routés à travers la surface de friction), lignes.

| champ | signification |
|---|---|
| node_1, node_2 | taches reliées. |
| status | success. |
| theoretical_dist | distance en ligne droite (euclidienne) (m). |
| real_dist | longueur du chemin de moindre coût réellement tracé (m). |
| accumulated_cost | coût de friction cumulé le long du chemin. |
| efficiency | theoretical_dist / real_dist (1 = droit ; plus bas = plus de détour). |
| tortuosity | real_dist / theoretical_dist (1 = droit ; plus haut = plus sinueux). |
| dPC_val, dPC_relative, ebc_score, category, pinch_point_score | métriques d'importance de corridor. Actuellement désactivées -> null. |

**`failed_links_*.geojson`** : les liens **en échec** (un corridor était voulu mais n'a pu être réalisé). Les liens `blocked` et `out_of_reach` sont **tous deux tracés** le long de leur vrai chemin de moindre coût : `blocked` jusqu'à l'obstacle adouci (où est placé le point de rupture), `out_of_reach` un tracé complet dont le coût dépasse le budget de dispersion `d0 * 3`. Seul `node_not_found` (rare, technique) garde la ligne de désir droite. Le tableau de bord n'affiche que les `blocked`.

| champ | signification |
|---|---|
| node_1, node_2 | les deux taches qui n'ont pu être reliées. |
| status | failed. |
| fail_reason | blocked (aucun chemin fini : un obstacle dur les sépare), out_of_reach (un chemin existe mais au-delà du budget de dispersion), ou node_not_found (échec technique de correspondance). |
| theoretical_dist, real_dist, accumulated_cost, efficiency | comme dans lcp (peuvent être NaN si aucun chemin). |
| obstacle | code(s) d'occupation du sol de l'obstacle bloquant, séparés par des virgules (par ex. 52 = route principale, 80 = eau). L'eau (80) est reportée pour les profils où elle est un obstacle (ground_mammal, ground_reptile) ; les bâtiments (51) sont exclus (surfaciques, pas un point de franchissement). |
| n_ruptures | nombre de franchissements d'obstacle détectés sur le lien. |



**`corridor_segments_*.geojson`** : corridors découpés en segments uniques, en gardant les parties situées **hors** des taches d'habitat (les portions de corridor dans la matrice, agrégées par nombre de corridors se superposant), lignes. Purement géométrique (découpé + agrégé), ce n'est pas une prescription d'aménagement.

| champ | signification |
|---|---|
| segment_id | identifiant de segment. |
| corridor_count | nombre de corridors passant par ce segment (plus élevé = plus partagé / important). |
| sum_dPC, max_ebc, max_pinch_point | métriques d'importance agrégées. Actuellement désactivées -> 0/null. |

> Note : le lissage des segments est encore imparfait (artefacts occasionnels en escalier issus du raster 10 m). Cela n'affecte pas quels segments existent ni `corridor_count`.

### `stats_*.csv` : une ligne de KPI par ville / profil écologique

| champ | signification |
|---|---|
| nb_nodes | taches retenues pour la ville. |
| isolated_nodes_count | taches sans corridor fonctionnel. |
| cores_count, islets_count | réservoirs vs petits relais détectés (emprise tamponnée complète). |
| n_subnetworks_theory | sous-réseaux potentiels (composantes connexes d'au moins 3 taches dans l'AOI) avant obstacles (graphe de Gabriel). |
| n_subnetworks | sous-réseaux réalisés (au moins 3 taches dans l'AOI) après coupure des liens par les obstacles (fragmentation effective). |
| subnetworks_split_by_failed_links | n_subnetworks - n_subnetworks_theory : sous-réseaux nets ajoutés par les liens en échec (les taches entièrement coupées basculent dans isolated_nodes_count). |
| largest_subnetwork_size | nombre de taches dans l'AOI du plus grand sous-réseau réalisé. |
| nb_corridors | corridors réussis. |
| nb_failed_corridors | liens en échec (corridors en échec). |
| pc_theory | Probability of Connectivity sur les distances en ligne droite (connectivité potentielle). |
| pc_real | PC sur les vrais chemins de moindre coût (connectivité effective à travers le paysage réel). |
| ec_theory_ha, ec_real_ha | surface équivalente connectée = sqrt(PC) * surface AOI (ha) : la taille d'une unique tache entièrement connectée donnant le même PC (théorique vs réalisée). Indicateur de tête pour l'aménageur. |
| connected_habitat_pct | ec_real_ha / habitat_ha_in_aoi * 100 = part de l'habitat dans l'AOI qui fonctionne comme connectée (0-100, linéaire). |
| connectivity_loss_pct | (pc_theory - pc_real) / pc_theory * 100. **N'est plus considéré comme pertinent** : une perte en % d'un indice abstrait ne parle pas à un aménageur. Conservé dans les sorties mais à ignorer ; préférer ec_*_ha / connected_habitat_pct. |
| median_tortuosity, mean_tortuosity | sinuosité des corridors (réel/théorique). |

### `manifest_*.json` - provenance du jeu de sorties

Écrit à la fin de chaque exécution. Consigne ce qui a produit le dossier, de sorte qu'un jeu soit traçable sans journal externe : horodatage, territoire et profil écologique, projection, empreinte du commit et état propre ou non de l'arborescence, version de Python et de la plateforme, versions des dix bibliothèques principales, et l'ensemble des paramètres du calcul (`d0`, tampon, codes d'habitat, table de friction complète, budget de déplacement, seuils de cœur, d'îlot et de sous-réseau).

> Le fichier porte un horodatage : l'exclure de tout contrôle de reproductibilité octet par octet (`diff -r -x 'manifest_*.json'`).

> **Lire ces indices en relatif.** Le PC (Probability of Connectivity) est un indice de paysage **relatif**, non borné à [0,1] (la normalisation par la seule AOI peut dépasser 1) : sa valeur absolue n'a pas de sens en soi, il sert à **comparer** (profils, villes, avant/après un scénario). `ec_real_ha` (surface connectée équivalente, une construction de modélisation, pas une tache réelle) et `connected_habitat_pct` (= EC / habitat dans l'AOI) en héritent et dépendent de l'AOI : à lire eux aussi relativement. `connectivity_loss_pct` n'est plus considéré comme pertinent (conservé dans les sorties, mais à ignorer).

---

## 5. Méthodologie

Par (ville, profil écologique) : construire l'occupation du sol du profil (WorldCover + OSM) -> extraire les taches d'habitat par analyse morphologique (MSPA : noyaux d'au moins 1 ha de cœur, relais 0,1-1 ha) -> relier les taches par un **graphe de Gabriel** (liens dans `2 * d0`) -> calculer la Probability of Connectivity théorique -> router chaque lien en **chemin de moindre coût** sur la surface de friction (`skimage.MCP_Geometric`) dans un budget de coût `d0 * 3`. Les liens réussis sont exportés en `lcp` ; ceux sans chemin fini ou au-delà du budget deviennent `failed_links` (fail_reason : blocked / out_of_reach / node_not_found). Une surface de dispersion bornée (`dispersal_bounded`) est masquée au même budget. Enfin la chaîne calcule les métriques réseau/corridor, découpe les corridors en `corridor_segments`, et écrit les KPI par profil dans `stats.csv`.


---

## 6. Comment ouvrir / comparer

- **QGIS / ArcGIS** : glisser les `.geojson` et `.tif` (régler le CRS du projet sur l'UTM de la ville).
- **Python** : `geopandas.read_file(...)` pour les vecteurs, `rioxarray.open_rasterio(...)` pour les rasters.
- **Comparer avec vos propres résultats** : aligner sur la même définition de profil écologique (codes habitat + `d0` en section 2), les mêmes codes d'occupation du sol (section 3), et le même CRS. Le PC est un indice relatif : comparer des écarts / classements plutôt que des valeurs absolues.

---

## 7. Précautions

- **Le tableau de bord n'affiche que les liens en échec `blocked` ; ce dossier les conserve tous.** Les `out_of_reach` sont majoritaires et encombreraient la carte, le tableau de bord les filtre ; ils restent ici (dans `failed_links_*.geojson`) pour l'analyse.

- Métriques **désactivées dans ce lot** (colonnes présentes mais null/0) : intermédiarité de nœud (`nbc_score`), importance de corridor (`dPC_*`, `ebc_score`, `category`, `pinch_point_score`, `sum_dPC` / `max_ebc` / `max_pinch_point` des segments). Désactivées pour le coût de calcul ; la géométrie et les métriques de base (distances, sinuosité, PC, comptages) sont valides.

- Les champs de sous-réseaux (`subnetwork_id`, `n_subnetworks`, `n_subnetworks_theory`, `subnetworks_split_by_failed_links`, `largest_subnetwork_size`) sont présents dans **toutes les sorties actuelles**. Un sous-réseau est une composante connexe du réseau réalisé (post-obstacles) d'**au moins 3 taches dans l'AOI** ; la connectivité peut passer par des taches hors AOI conservées, mais seules les taches dans l'AOI sont comptées (donc `largest_subnetwork_size <= nb_nodes`).

- Le lissage des segments est approximatif (voir note plus haut).

- Source : ESA WorldCover v200 + OSM (instantané au moment du run, juin 2026). Friction calibrée sur les références Cerema Sud-Ouest (2025, La Rochelle), sans validation empirique.

- **Les taches d'habitat sont qualifiées structurellement, pas écologiquement.** Noyaux vs relais (`node_type`, `class`, `max_core_ha`) proviennent seulement de la taille et de la compacité des taches (morphologie MSPA), pas de la qualité de l'habitat : les pressions diffuses (pollution lumineuse et sonore, dérangement, gestion, prédateurs domestiques) ne sont pas captées, si bien qu'un grand noyau compact peut recouvrir un habitat dégradé. Une qualification multicritère de qualité était prévue mais réduite au critère morphologique pour ce lot.

- Les déplacements à l'intérieur des taches d'habitat sont considérés comme libres, ce qui peut surestimer la connectivité.

- La résolution peut être trop grossière pour les milieux urbains ; itérer avec Green Urban Sat ou une occupation du sol plus détaillée ?
