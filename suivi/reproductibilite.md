# Reproductibilité, versionnage et passation

> Fiche opérationnelle. Chaque section indique **ce que ça débloque dans le rapport**, le coût, et la
> commande exacte. À exécuter depuis la racine du projet sur la VM
> (`/home/jovyan/work/team/marion/corridor_project`), qui est la copie de référence.
> Rédigée le 2026-08-29. Les cases à cocher servent de suivi avant dépôt.

## 0. Périmètre : ce qui entre dans le dépôt

Mesures relevées le 2026-08-29 sur la copie locale :

| Contenu | Poids | Dans le dépôt |
|---|---|---|
| `utils/` + `tests/` (18 fichiers `.py`) | 218 Ko | oui |
| `libs/smoothify/` (dépendance vendue) | 1 Mo | oui |
| `suivi/`, `README.md`, `requirements.txt`, `restore_env.sh` | 3 Mo | oui |
| notebooks `*_prod.ipynb` (legacy) | 3 Mo | oui, sorties retirées |
| `papier/` (sources `.md`, `.tex`, figures `.png`) | ~30 Mo | oui |
| `papier/` (docx, pptx, zip, PDF de littérature) | ~300 Mo | non |
| `data/` (sorties, sensibilité, caches) | **116 Go** | non, diffusé à part |

Le code utile tient donc dans un dépôt de quelques mégaoctets. C'est un argument à faire valoir :
le volume est dans les sorties, pas dans la chaîne.

## 1. Outils de suivi : état réel

| Outil | Usage effectif | À faire |
|---|---|---|
| GitHub personnel, `marion-billy/urbiverde_ivb` | dépôt ouvert et alimenté **en début de stage**, non tenu au fil de l'eau ensuite | y synchroniser l'état livré (§1.1) |
| VM, dossiers par prénom | partage quotidien réel au sein de l'équipe, sans gestion de version | — (constat, à décrire au chapitre 6) |
| GitLab d'entreprise, `services/dash-dashboards/urban-connectivity-atlas` | maquette du tableau de bord, circuit habituel de l'entreprise | — (déjà en place) |
| Jira | peu utilisé sur ce sujet : une seule personne dessus, en avance sur le jalon UrbiVerde | — (constat assumé) |

Conséquence pour le rapport : le §2.5 cite désormais le dépôt GitHub, et le chapitre 6 décrit
honnêtement cet usage inégal, en assumant que le versionnage n'a pas été tenu en continu. Ne pas
fabriquer d'historique antidaté : une synchronisation datée d'aujourd'hui, annoncée comme telle,
est défendable, contrairement à des commits rétrodatés.

### 1.1. Synchroniser le dépôt avec l'état livré

**Débloque** : §2.5 et §5.3 (passation).  **Coût** : 30 min.  Procédure suivie le 2026-08-30.

Le dépôt est initialisé **dans** le dossier de travail, puis rattaché à l'historique distant sans
que les fichiers soient touchés. Aucune commande ci-dessous ne modifie le répertoire de travail.

```bash
cd /home/jovyan/work/team/marion/corridor_project

# 1. Dépôt local et rattachement au distant
git init
git config user.name  "Marion Billy"
git config user.email "<prenom.nom@murmuration-sas.com>"
git remote add origin https://github.com/marion-billy/urbiverde_ivb.git
git fetch origin
git log --oneline origin/HEAD | head     # où le dépôt s'était arrêté
git branch -r                            # nom de la branche : main ou master

BR=main                                  # adapter si besoin

# 2. Ancrer l'historique SANS toucher aux fichiers
git reset --soft origin/$BR

# 3. Retirer les sorties des notebooks (images embarquées)
pip install nbstripout && nbstripout *.ipynb

# 4. CONTRÔLE avant de commiter
git add -A
git status --short | wc -l               # ordre de grandeur : la centaine de fichiers
git diff --cached --name-only | grep -iE '\.tif$|\.geojson$|credential|gee.*\.json' \
  && echo ">>> STOP : donnée ou secret indexé" || echo ">>> périmètre propre"
du -sh .git                              # doit rester de l'ordre de quelques Mo

# 5. Commit : message passé par l'entrée standard, pour éviter tout piège de guillemets
git commit -F - <<'EOF'
Synchronisation de l'etat livre en fin de stage

Chaine complete (utils/), tests, configuration des profils ecologiques,
documentation de suivi et sources du rapport. Le depot n'ayant pas ete tenu
au fil du developpement, ce commit reporte l'etat final ; l'historique des
decisions est dans suivi/decision_log.md. Sorties (data/, 116 Go) diffusees
separement.
EOF

# 6. Étiquette et publication
BR=$(git rev-parse --abbrev-ref HEAD)
git tag -a v1.0-stage -m "Etat livre en fin de stage (14 aout 2026)"
git push -u origin "$BR"
git push --tags

# 7. Confirmer que c'est arrivé
git fetch origin && git log --oneline -1 "origin/$BR"
git ls-remote --tags origin | grep v1.0-stage
```

**Ne jamais lancer `git checkout .`, `git reset --hard` ni `git clean` dans ce dossier** : ce sont
les seules commandes qui pourraient écraser le travail. Les étapes ci-dessus sont non destructrices.

Deux pièges rencontrés. Un `git commit -m "..."` sur plusieurs lignes laisse le shell en attente du
guillemet fermant et avale les commandes suivantes dans le message : d'où le `-F -` avec document
en ligne. Et GitHub n'accepte plus le mot de passe : il faut un jeton personnel à portée
`Contents: read and write`, saisi à la place du mot de passe (`git config credential.helper store`
pour ne le fournir qu'une fois).

- [ ] dépôt synchronisé, commit et étiquette poussés
- [x] URL du dépôt reportée en §2.5 (appliquée le 2026-08-29)

## 2. Figer l'environnement

**Débloque** : annexe A. Aujourd'hui `requirements.txt` ne contient qu'une ligne
(`smoothify==0.2.3`) ; les versions listées en annexe sont celles observées dans le conteneur,
relevées après coup, et **ne sont figées dans aucun fichier**.  **Coût** : 5 min.

```bash
bash env/freeze_env.sh        # écrit env/requirements-lock.txt + env/environment.yml
git add env/ && git commit -m "Fige l'environnement d'exécution (pip freeze + export conda)"
```

Puis, en annexe A, remplacer « Ces versions sont fixées pour garantir la reproductibilité » par une
formulation exacte : « Les versions de l'environnement d'exécution sont relevées et figées dans
`env/requirements-lock.txt`. »

- [ ] `env/requirements-lock.txt` produit et commité
- [x] phrase de l'annexe A corrigée (appliquée le 2026-08-29)

## 3. Test de déterminisme

**Débloque** : la partie D du protocole de validation (`papier/internship_report/validation_protocol.md`),
prévue et jamais exécutée. C'est la preuve de reproductibilité la plus convaincante disponible, et
la moins chère.  **Coût** : ~35 min machine sur Perpignan.

```bash
export PYTHONPATH=/opt/conda/lib/python3.11/site-packages
bash restore_env.sh                       # si le conteneur a redémarré
ls -la data/lc_cache/Perpignan_6000/      # l'instantané d'entrée doit exister

python3 utils/run_pipeline.py Perpignan --lc-cache --out-tag det1
python3 utils/run_pipeline.py Perpignan --lc-cache --out-tag det2

A=data/sensitivity/det1/data/outputs/Perpignan
B=data/sensitivity/det2/data/outputs/Perpignan

# 1. mêmes fichiers produits
diff <(cd "$A" && find . -type f | sort) <(cd "$B" && find . -type f | sort)

# 2. identité octet par octet
diff -r "$A" "$B" && echo "DÉTERMINISME : sorties identiques octet par octet"

# 3. contrôle ciblé des indicateurs
for p in ground_mammal arboreal_mammal forest_edge_bird ground_reptile; do
  diff -q "$A/$p/stats_${p}_Perpignan.csv" "$B/$p/stats_${p}_Perpignan.csv" >/dev/null \
    && echo "  $p : indicateurs identiques" || echo "  $p : INDICATEURS DIFFÉRENTS"
done

rm -rf data/sensitivity/det1 data/sensitivity/det2   # ~700 Mo, après relevé du résultat
```

**Résultat obtenu le 2026-08-30** : les trois niveaux sont passés, identité octet par octet sur
toutes les couches et indicateurs identiques pour les quatre profils (cf. `decision_log.md`).

**`--lc-cache` est indispensable** : sans lui chaque exécution réinterroge OpenStreetMap, base
vivante modifiée quotidiennement, et les sorties diffèrent pour une raison d'entrée et non de
chaîne. Ce point mérite d'être dit dans le rapport : le déterminisme vaut **à entrées identiques**,
et `data/lc_cache/<Ville>_<tampon>/` est précisément l'archive de l'instantané d'entrée qui rend la
chaîne rejouable. Diffuser ce cache avec les sorties est ce qui permet à un tiers de reproduire les
résultats exactement, plutôt qu'approximativement.

- [x] test lancé le 2026-08-30 : identité octet par octet, consigné dans `decision_log.md`
- [x] phrase ajoutée en §2.5 (déterminisme à instantané archivé)
- [x] `[À COMPLÉTER]` du §2.5 remplacé par le résultat

## 4. Manifeste d'exécution

**Débloque** : transforme « chaîne déterministe » en trace vérifiable, jeu de sorties par jeu de
sorties.  **Coût** : ~25 lignes dans `utils/sp_pipeline.py`, à insérer juste avant l'écriture de
`stats.csv`.

```python
    # Manifeste d'exécution : empreinte du code, de l'environnement et des paramètres qui ont
    # produit ce jeu de sorties. Rend chaque dossier auto-documenté et vérifiable a posteriori.
    import json, platform, subprocess, sys, datetime
    def _git(*args):
        try:
            return subprocess.run(["git", *args], cwd=str(paths.project_root),
                                  capture_output=True, text=True, check=True).stdout.strip()
        except Exception:
            return None
    manifest = {
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "city": CITY,
        "ecoprofil": ecoprofil_key,
        "git_commit": _git("rev-parse", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain")),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "params": {
            "d0_m": d0,
            "habitat_codes": specie["habitat_codes"],
            "friction": {str(k): (None if pd.isna(v) else float(v))
                         for k, v in specie["friction"].items()},
            "friction_avg_favorable": spp.FRICTION_AVG_FAVORABLE,
            "cost_budget": threshold,
            "core_min_ha": 1.0,
            "islet_min_ha": 0.1,
            "subnetwork_min_patches": 3,
            "aoi_buffer_m": 2 * d0,
        },
        "crs": str(utmb_epsg),
        "packages": {m: __import__(m).__version__ for m in
                     ("numpy", "pandas", "geopandas", "shapely", "rasterio",
                      "xarray", "networkx", "skimage")},
    }
    with open(str(ecoprofil_dir) + f"/manifest_{ecoprofil_key}_{CITY}.json", "w") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
```

À documenter ensuite dans `data/outputs/README.md` (le fichier passe à 14 par couple).

**Attention** : l'horodatage du manifeste cassera l'identité octet par octet du test §3. Une fois le manifeste en place, la comparaison devra l'exclure (`diff -r -x 'manifest_*.json'`).

- [ ] manifeste ajouté et vérifié sur un couple
- [ ] README des sorties mis à jour

## 5. Étendre les tests

**Débloque** : la question posée trois fois par le tuteur. `tests/test_pipeline_extra.py` ajoute
8 tests aux 2 existants (indice PC sur graphe jouet, seuils MSPA, surface de friction, invariants
de calibration), soit exactement les manques listés dans le README.  **Coût** : une exécution.

```bash
export PYTHONPATH=/opt/conda/lib/python3.11/site-packages
python3 -m pytest tests/ -q            # ou : python3 tests/test_pipeline_extra.py
```

> Ces tests ont été écrits sans pouvoir être exécutés (environnement géospatial absent de la machine
> de rédaction). **Les lancer une fois et corriger ce qui casse avant de les citer dans le rapport.**
> Mettre ensuite à jour le tableau attendu/observé du README racine.

- [ ] suite exécutée, 10/10 au vert
- [ ] tableau du README complété

## 6. Provenance des données

**Débloque** : le volet FAIR du §5.3, aujourd'hui affirmé sans traçabilité des millésimes.
**Coût** : 15 min, à remplir depuis les logs d'exécution.

| Source | Version / millésime | Date d'acquisition | Accès |
|---|---|---|---|
| ESA WorldCover | v200 (millésime 2021) | [à compléter : date des runs] | Earth Engine, `ESA/WorldCover/v200` |
| OpenStreetMap | instantané via Overpass | [à compléter : dates, cf. `data/lc_cache/`] | OSMnx, cache `data/cache/` |
| GBIF | requêtes API REST | [à compléter, cf. `_sandbox/gbif_validation/`] | `api.gbif.org/v1/occurrence/search` |
| Limites administratives | geo.api.gouv.fr / OSM | [à compléter] | URLs dans `CITY_CONFIG` |

OSM n'a pas de version citable : l'instantané effectivement utilisé est celui archivé dans
`data/lc_cache/`. Pour GBIF, une requête API n'a pas de DOI ; si une citation stable est voulue,
refaire un téléchargement via l'interface GBIF, qui en attribue un.

- [ ] tableau rempli et repris en annexe A

## 7. Après le dépôt : industrialisation

**Non engagée pendant le stage**, et annoncée comme telle dans le rapport (chapitre 6) : c'est le
prolongement immédiat, à porter avec l'équipe. La cible d'ordonnancement est **Prefect**, en usage
dans l'équipe, qui déclencherait les exécutions par territoire, gérerait les reprises sur incident
et journaliserait les traitements. Par ordre de valeur :

0. **Orchestration Prefect.** Transformer `run_pipeline.py` en flux : une tâche par étape
   (acquisition de l'occupation du sol, segmentation, graphe, moindre coût, indicateurs), un
   paramétrage par territoire et par profil, la reprise au point d'échec plutôt qu'au début, et la
   journalisation centralisée. Prérequis : les points 1 et 2 ci-dessous, sans lesquels le flux
   resterait lié à l'arborescence de la machine de développement.

1. **Supprimer les chemins inter-espaces.** `sp_pipeline.py`, `connectivity.py` et `landcover.py`
   importent via `sys.path.insert` des chemins relatifs vers `../../Hugo/a_b_c_functions/`, ce qui
   lie la chaîne à une arborescence précise et à un répertoire de travail. Cinq fonctions seulement
   sont utilisées (`raster_to_polygon`, `create_img_reference`, `get_utm_epsg`, `gdf_to_bbox`,
   `prepare_ds_xarray_ee`) : soit rendre `a_b_c_functions` installable (`pip install -e`), soit les
   vendre dans `utils/`. C'est la dette qui empêche aujourd'hui de rejouer la chaîne ailleurs.
2. **`pyproject.toml`** : le projet devient installable, `paths.py` cesse de dépendre d'une racine
   codée en dur, et les entrées de commande sont déclarées.
3. **Conteneur** : un `Dockerfile` figeant l'environnement lèverait `restore_env.sh` et la
   dépendance à l'image de base du conteneur éphémère.
4. **Intégration continue** : exécuter `pytest` et `output_check.py` à chaque commit, plus un
   analyseur statique (`ruff`) configuré dans `pyproject.toml`.
5. **Diffusion des sorties** : déposer les jeux de sorties et le `lc_cache` sur une archive à DOI
   (Zenodo) ou un stockage objet. C'est ce qui rendrait le volet « accessibles » des principes FAIR
   littéralement vrai, aujourd'hui appuyé sur la seule ouverture des données d'entrée.
