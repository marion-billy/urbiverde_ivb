# Corridor project : chaîne de connectivité écologique urbaine (UrbiVerde)

Chaîne Python qui identifie les continuités écologiques urbaines potentielles à partir de données
ouvertes (ESA WorldCover 10 m + OpenStreetMap), par profil écologique. Pour la méthode et les
résultats, voir `papier/internship_report/`. Ce README est le point d'entrée de **passation** : comment
installer, lancer, ce qui entre et ce qui sort, et les limites de reprise connues.

## 1. Installation

Conteneur éphémère : les paquets pip hors image de base sont effacés au redémarrage. Après tout
redémarrage :

```bash
bash restore_env.sh        # réinstalle osmnx (requis) + python-docx/xhtml2pdf (build du rapport)
```

Deux points d'environnement à connaître (voir §5) :
- **Earth Engine** : la chaîne lit une clé de compte de service (`$GEE_KEY_PATH`, sinon la clé
  partagée `marion/credentials/*.json`). Sans elle, le téléchargement WorldCover échoue.
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
  `--friction-contrast`, avec `--out-tag <tag>` pour écrire sous `data/sensitivity/<tag>/`.
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
`failed_links_*`, `rupture_points_*`, `corridor_segments_*` (.geojson) ; `stats_*.csv` (indicateurs).
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

```bash
export PYTHONPATH=/opt/conda/lib/python3.11/site-packages
python3 tests/test_pipeline.py          # ou : python3 -m pytest tests/ -q  (si pytest installé)
```

Tests de non-régression sur les fonctions pures (état au dernier lancement) :

| Fonction | Jeu de test | Attendu | Observé | Environnement |
|---|---|---|---|---|
| `get_binary_habitat` | raster jouet {10, 20, 50, NaN}, codes habitat {10, 20} | {1, 1, 0, 0}, dtype uint8 | conforme | local |
| `calculate_tortuosity` | (réel, théorique) = (100, 100), (150, 100), (5, 0) | 1.0 ; 1.5 ; NaN (pas inf) | conforme | local |

À compléter : indice PC sur un graphe jouet, seuils MSPA, profilage petite ville vs grande ville
(chiffres au chapitre 6 du rapport).
