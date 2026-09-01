# Frictions Cerema La Rochelle (pp. 96-98) — transcription et comparaison à l'Annexe A.3

> Extrait par lecture directe des images du PDF `Rapport_continuite_eco_CDA_2025.pdf` (section 5.4,
> pp. 96-98 ; tables non textuelles, transcrites visuellement le 2026-08-03). Échelle 1 / 10 / 100.
> Espèces de référence utilisées dans le rapport : Écureuil roux, Fauvette à tête noire (sous-trame
> arborée/arbustive) ; Lézard des murailles (sous-trame herbacée) ; Hérisson d'Europe (sous-trame
> mixte). Colonnes Cerema données par espèce (H = Hérisson, É = Écureuil, F = Fauvette, L = Lézard).

## 1. Table Cerema transcrite (valeurs par espèce de référence)

| Classe d'OS Cerema | Hérisson | Écureuil | Fauvette | Lézard |
|---|--:|--:|--:|--:|
| Boisements de feuillus | 1 | 1 | 2 | 4 |
| Boisements mixtes | 2 | 1 | 2 | 4 |
| Bois, arbres | 1 | 1 | 1 | 4 |
| Formation arbustive | 1 | 6 | 1 | 4 |
| Prairies permanentes | 2 | 4 | 7 | 1 |
| Prairies temporaires | 3 | 5 | 7 | 3 |
| Surfaces herbacées | 2 | 4 | 7 | 2 |
| Pelouses sèches | 6 | 6 | 7 | 1 |
| Grandes cultures | 7 | 8 | 8 | 6 |
| Chemins agricoles | 5 | 8 | 8 | 3 |
| Cultures florales/légumières | 7 | 7 | 7 | 5 |
| Potagers | 6 | 6 | 6 | 4 |
| Vignes | 7 | 7 | 4 | 5 |
| Vergers | 5 | 5 | 3 | 5 |
| Surfaces en eau | 9 | 9 | 7 | 8 |
| Bassin de rétention | 100 | 100 | 7 | 100 |
| Cours d'eau | 10 | 10 | 6 | 10 |
| Fossés & noues | 5 | 4 | 4 | 6 |
| Canaux de marais | 10 | 10 | 6 | 10 |
| Canaux principaux | 100 | 100 | 100 | 100 |
| Zones bâties et artificialisées | 100 | 100 | 100 | 100 |
| Zones bâties (bords de routes fréquentés, autre lecture BD) | 10 | 7-8 | 10 | 3 |
| Sols nus | 10 | 10 | 10 | 3 |
| Routes | 50 | 50 | 50 | 50 |
| Routes très fragmentantes | 100 | 100 | 100 | 100 |
| Voies ferrées | 10 | 9 | 7 | 3 |
| Ponts transparents | 4 | 4 | 4 | 4 |
| Passages cours d'eau | 4 | 4 | 4 | 4 |
| Passages à faune | 2 | 2 | 2 | 2 |

Note : les zones bâties apparaissent avec plusieurs lignes selon la BD source (OCS GE, BD Topo, CoSIA)
et selon qu'il s'agit du bâti strict (100) ou de l'inter-bâti fréquenté en bord de route (8-10). Les
« passages à faune » à 2 sont propres à La Rochelle.

## 2. Comparaison à l'Annexe A.3 du rapport (transposition WorldCover)

Verdict : **les valeurs de l'Annexe A.3 sont une transposition fidèle de la table Cerema**, presque
cellule pour cellule sur les classes directement mappables, avec trois écarts qui sont des **choix
assumés et documentés** dans `species_params.py`.

| Code WC (rapport) | Classe Cerema mappée | Cerema (H/É/F/L) | Annexe A.3 (H/É/F/L) | Correspondance |
|---|---|---|---|---|
| 10 Couvert arboré | Boisements feuillus / Bois-arbres | 1 / 1 / 2 / 4 | 1 / 1 / 2 / 4 | **exacte** |
| 20 Arbustes | Formation arbustive | 1 / 6 / 1 / 4 | 1 / 6 / 1 / 4 | **exacte** |
| 30 Prairies, herbacées | Surfaces herbacées / prairies perm. | 2 / 4 / 7 / 1-2 | 2 / 4 / 7 / 1 | **exacte** |
| 40 Cultures | moyenne cultures/vignes/vergers/potagers | ~6-7 / ~7 / ~6 / ~5 | 6 / 7 / 6 / 5 | **moyenne** |
| 54 Chemins | Chemins agricoles | 5 / 8 / 8 / 3 | 5 / 8 / 8 / 3 | **exacte** |
| 55 Voies ferrées | Voies ferrées | 10 / 9 / 7 / 3 | 10 / 9 / 7 / 3 | **exacte** |
| 60 Sols nus | Sols nus | 10 / 10 / 10 / 3 | 10 / 10 / 10 / 3 | **exacte** |
| 53 Routes secondaires | Routes | 50 / 50 / 50 / 50 | 50 / 50 / 50 / 50 | **exacte** |
| 52 Routes principales | Routes très fragmentantes | 100 / 100 / 100 / 100 | 100 / 100 / 100 / 100 | **exacte** |
| 80 Eaux permanentes | Surfaces en eau | 9 / 9 / 7 / 8 | ∞ / 9 / 7 / ∞ | écart assumé (eau = barrière pour terrestres, WorldCover 10 m ne capte que les grandes eaux ; É/F conservés) |
| 50 Urbain diffus + 51 Bâtiments | Zones bâties | 100 (ou 8-10) | 50→10 ; 51→∞ (F : 100) | écart assumé (bâti non valorisé, mis en barrière pour terrestres) |
| 90/95 Zones humides, mangroves | (pas de valeur mammifère directe) | — | 8 / 8 / 6 / 8 | inféré (moyenne classes aquatiques) |

## 3. Conséquences pour le sourcing

- **Les frictions ne sont donc pas « un agrégat de papiers non notés » : elles sont les valeurs
  Cerema La Rochelle, transposées.** L'agrégat sous-jacent est celui du Cerema lui-même (Balbi 2017 ;
  SRCE Aquitaine/Poitou-Charentes ; Cerema 2020/2022/2024 ; Sordello et al. 2011/2013 ; dires
  d'expert ; données FAUNA/LPO), documenté dans sa bibliographie (pp. 99-102).
- **Sourcing correct** : citer le Cerema La Rochelle (2025) comme source des valeurs, et remonter à
  Balbi (2017, thèse) et Sordello et al. (2011/2013) pour la provenance. Lumia et al. (2023) /
  Gelmi-Candusso et al. (2025) = **positionnement méthodologique et convergence éventuelle**, pas
  source.
- **Trois écarts à documenter comme choix** (eau, bâti, zones humides), ce que fait déjà l'encadré de
  §2.3 et le docstring de `species_params.py`.
- **d₀** : voir section 4 (fiches espèces), qui **résolvent** le sourcing des quatre d₀, hérisson
  compris.

## 4. Fiches espèces Cerema (pp. 89-94) — capacités de déplacement et sources

Lecture directe des images (transcription visuelle, 2026-08-03). Chaque fiche donne habitat, domaine
vital, capacité de déplacement, menaces, motif du choix, et ses **sources consultées**. Extrait pour
les quatre espèces de référence du rapport (les d₀ du rapport sont **tous couverts**, hérisson inclus) :

| Espèce (sous-trame) | Capacité de déplacement (fiche Cerema) | d₀ rapport | Verdict |
|---|---|--:|---|
| **Hérisson d'Europe** (mixte) | « 2 à 3 km par nuit ; en cas de nécessité 5 à 8 km, un **rayon de 4 km semble plus naturel** ; peut nager » | 3000 | **soutenu** (3 km au cœur de la fourchette) |
| **Écureuil roux** (arborée) | « 3 à 4 km/jour mais reste dans un rayon de 200 m ; **distance de dispersion ~3 km** ; nage » | 2000 | soutenu (≤ 3 km) |
| **Fauvette à tête noire** (arborée) | « à dire d'expert, **1 à 2 km/jour** selon saison/individu ; migratrice, populations sédentaires » | 1500 | soutenu (milieu de 1-2 km) |
| **Lézard des murailles** (herbacée) | « jeunes migrent ~300 m ; **distance max de dispersion ~1 km** » | 750 | soutenu (entre 300 m et 1 km) |

Le d₀ hérisson (3000 m) n'est donc **pas** hors-cadre : il est directement documenté par la fiche
Cerema. La fourchette « 1-2 km » citée ailleurs était le critère « distance au réservoir » (Tableau 4),
pas la capacité de déplacement.

**Sources citées par les fiches Cerema (= références adéquates pour les d₀, par espèce) :**
- Hérisson : Macdonald D.W. & Barrett P. (2005), *Guide complet des mammifères de France et d'Europe*,
  204 p. ; Quiblier / Fédération des PNR de France (2007) ; thèse HAL tel-01762455 ; actes
  Natureparif–SRCE milieu urbain (2016) ; missionherisson.org.
- Écureuil : Macdonald & Barrett (2005) ; écureuils.mnhn.fr ; thèse ENV Alfort n°3959 ; INPN.
- Fauvette : S. Guingand, *Recherche bibliographique sur la capacité de dispersion des oiseaux pour
  modéliser le paysage et sa connectivité par la théorie des graphes* ; Atlas des oiseaux nicheurs du
  Limousin (SEPOL, 1993) ; INPN ; LPO Tarn.
- Lézard : Pottier G. (2016), *Les reptiles des Pyrénées*, MNHN, 352 p. ; Vacher J.-P. & Geniez M.
  (2010), *Les reptiles de France, Belgique, Luxembourg et Suisse*, Biotope/MNHN, 544 p. ; LPO.

Donc le sourcing des d₀ passe par : **fiches espèces Cerema La Rochelle (2025)**, qui compilent ces
références par espèce. À citer ainsi, plutôt que de plaquer Berthoud/Morris/Avon/Wauters (dont les
valeurs exactes divergent, cf. mémo §14).

## 5. Convergence avec Lumia (2023) et Gelmi-Candusso (2025)

Objectif : les valeurs peuvent-elles être **corroborées** par ces tables publiées ? Limite d'accès :
Lumia (ScienceDirect) et Gelmi-Candusso (Wiley, pourtant open access) renvoient tous deux HTTP 403 au
fetch automatique → **valeurs cellule par cellule non récupérables** ici. Ce qui est vérifié :
- **Échelle** : les deux utilisent une résistance **0-100, relative, multi-espèces, dérivée de
  l'occupation du sol** (Gelmi : « resistance values 0-100, relative among taxa » ; Lumia : échelle
  0-100 pour dix mammifères terrestres). → **appui solide au positionnement méthodologique.**
- **Convergence ordinale** attendue et cohérente (habitat/forêt ≈ 1 ; matrice/cultures intermédiaire ;
  urbain/routes ≈ 100), commune à la table Cerema, à Lumia et à Gelmi.
- **Pas de convergence numérique cellule par cellule** à revendiquer : taxons différents (hérisson/
  écureuil/fauvette/lézard européens vs mammifères de Toronto) et nomenclatures d'OS différentes. Une
  égalité chiffrée serait un abus. Le bon usage = positionnement + pattern ordinal, pas équivalence.
