# Corridor project : chaîne de connectivité écologique urbaine (UrbiVerde)

Chaîne Python qui identifie les continuités écologiques urbaines potentielles à partir de données
ouvertes (ESA WorldCover 10 m + OpenStreetMap), par profil écologique. 

## 1. Installation

Conteneur éphémère : les paquets pip hors image de base sont effacés au redémarrage. Après tout
redémarrage :

```bash
bash restore_env.sh        # réinstalle osmnx (requis pour la chaîne)
```

Deux points d'environnement à connaître (voir la section Reproductibilité) :
- **Earth Engine** : la chaîne lit une clé de compte de service (`$GEE_KEY_PATH`)
- **urllib3** : lancer avec `PYTHONPATH=/opt/conda/lib/python3.11/site-packages` pour éviter le fork
  `urllib3-future` de `~/.local` qui casse le client Earth Engine.

## 2. Lancer la chaîne

Depuis la racine du projet :

```bash
export PYTHONPATH=/opt/conda/lib/python3.11/site-packages
python3 utils/run_pipeline.py <Ville> [--ecoprofil <profil>]
```

- `<Ville>` : une clé de `CITY_CONFIG` (Perpignan, Nancy, Kourou, LRSY, LaRochelle, Toulouse…).
- `--ecoprofil` : `ground_mammal` | `ground_reptile` | `arboreal_mammal` | `forest_edge_bird`
  (omis = les quatre). Défini dans `utils/species_params.py`.
- Options d'analyse de sensibilité : `--d0-scale`, `--friction-scale [--friction-class]`,
  `--friction-contrast`, avec `--out-tag <tag>` pour écrire sous `_sandbox/sensitivity/<tag>/`.
- Mode scénario d'aménagement : `--project <polygone.geojson>`.

Une même commande régénère l'ensemble des sorties d'un territoire (chaîne déterministe).

## 3. Entrées

- **Occupation du sol** : ESA WorldCover v200 (10 m), récupérée via Earth Engine sur l'emprise
  d'étude élargie d'un tampon (2 × distance de dispersion maximale).
- **Infrastructures** : OpenStreetMap (routes, voies ferrées, bâti, eau), fusionnées sur WorldCover.
- **Aire d'étude** : par ville, via `CITY_CONFIG` (URL de limites administratives, nom de commune, ou
  bbox). Projetée dans l'UTM local ; distances et surfaces en mètres/hectares.

## 4. Sorties (`data/outputs/<Ville>/<profil>/`)

Par couple (ville, profil), une arborescence normalisée : rasters `landcover_*`, `binary_habitat_*`,
`friction_*`, `dispersal_*` (.tif) ; couches vectorielles `edges_*` (nœuds/graphe), `lcp_*` (corridors),
`failed_links_*`, `corridor_segments_*` (.geojson) ; `stats_*.csv` (indicateurs).
Tous en projection métrique locale, directement exploitables en SIG et par le tableau de bord.

## 5. Reproductibilité et dettes connues (à lever pour l'industrialisation)

La chaîne est reproductible **sous conditions**, pas inconditionnellement :
- **Chemins inter-espaces** : certains imports passent par des chemins relatifs vers d'autres espaces
  de travail (`sys.path`), ce qui lie la chaîne à une arborescence précise. À empaqueter proprement
  avant une reprise sur une autre machine.
- **Dépendance Earth Engine** : authentification, quotas et disponibilité de l'API sont des points de
  défaillance externes à déclarer et à encapsuler.
- **Environnement éphémère** : `restore_env.sh` après chaque redémarrage (osmnx).

Isolation métier/code : `utils/species_params.py` isole les paramètres écologiques (habitat, d₀,
frictions) du reste ; un profil se modifie sans toucher à la chaîne.

## 6. Tests

Douze tests de non-régression portent sur les fonctions dont le résultat se vérifie à la main.
Ils complètent le contrôle automatisé des sorties (`utils/output_check.py`) : le premier vérifie que
les fonctions calculent ce qu'elles annoncent, le second que les sorties produites sont conformes.

```bash
export PYTHONPATH=/opt/conda/lib/python3.11/site-packages
python3 _sandbox/pipeline_tests/test_pipeline.py
python3 _sandbox/pipeline_tests/test_pipeline_extra.py
# ou, si pytest est installé :  python3 -m pytest _sandbox/pipeline_tests/ -q
```

**État au dernier lancement : 12 / 12 conformes**, le 2026-08-30, sous Python 3.11.15 sur la machine
de traitement.

| Fonction ou invariant | Jeu de test | Attendu |
|---|---|---|
| `get_binary_habitat` | raster {10, 20, 50, NaN}, habitat {10, 20} | {1, 1, 0, 0}, dtype uint8 |
| `calculate_tortuosity` | (réel, théorique) = (100, 100), (150, 100), (5, 0) | 1,0 ; 1,5 ; NaN (pas inf) |
| `create_resistance_surface` | codes {10, 20, 51, 0}, friction {10: 1, 20: 2, 51: NaN} | 1 ; 2 ; inf (barrière) ; inf (hors emprise) |
| `create_resistance_surface`, coût par défaut | code 40 absent du dictionnaire | 100, et non une barrière |
| `fast_mspa`, tache compacte | bloc de 5 × 5 pixels | cœur 9 px, lisière 16 px, aucun îlot |
| `fast_mspa`, tache filiforme | ligne de 1 × 5 pixels | aucun cœur, 5 px classés îlot |
| `calculate_pc_index`, taches reliées | 2 taches de 100 ha, coût ln 2, zone de 2 km² | 0,75 |
| `calculate_pc_index`, taches isolées | les mêmes, sans lien | 0,50 |
| `graph_to_gdf_edges` | taches jointives, points d'ancrage confondus | segment valide de 1 mm, pas de géométrie dégénérée |
| Calibration : habitat | les 4 profils écologiques | tout code d'habitat a une friction ≤ 3 et n'est jamais une barrière |
| Calibration : barrières | les 4 profils écologiques | {51, 80} ; {51} ; aucune ; {51, 80} |
| Calibration : dispersion | les 4 profils écologiques | d₀ de 3000, 2000, 1500 et 750 m ; budget = 3 × d₀ |

## 7. Organisation du code (`utils/`)

Cœur de la chaîne :

| Fichier | Rôle |
|---|---|
| `run_pipeline.py` | Point d'entrée en ligne de commande ; lance la chaîne pour une ville (modes baseline, sensibilité, scénario). |
| `sp_pipeline.py` | Orchestration d'un couple (ville, profil) : enchaîne occupation du sol -> habitat -> graphe -> LCP -> indicateurs -> sorties. |
| `landcover.py` | Acquisition et construction de l'occupation du sol enrichie (WorldCover via Earth Engine + OpenStreetMap). |
| `species_params.py` | Profils écologiques : `d0`, tables de friction, codes d'habitat et de barrière par profil. |
| `connectivity.py` | Taches d'habitat (segmentation morphologique MSPA), graphe de Gabriel, indicateurs de connectivité. |
| `routing.py` | Surface de friction, chemins de moindre coût (`MCP_Geometric`), surfaces de dispersion. |
| `paths.py` | Gestion centralisée des chemins de sortie (`CorridorPaths`). |

Utilitaires :

| Fichier | Rôle |
|---|---|
| `output_check.py` | Contrôle automatique des sorties produites. |
| `sensitivity_metrics.py` | Métriques de l'analyse de sensibilité. |
| `gbif_validation.py` | Validation externe côté habitat (occurrences GBIF). |
| `prep_for_dashboard.py` | Conversion des sorties en couches pour le tableau de bord. |
| `vizu_ind.py` | Fonctions de visualisation (utilisées par les notebooks d'orchestration). |
