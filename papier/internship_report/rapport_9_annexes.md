# Annexes

> Brouillon. Les annexes regroupent les éléments détaillés écartés du corps du rapport ; chacune est
> appelée depuis le corps, dans l'ordre de leur première citation. Corps impersonnel, sobre.

## Annexe A. Données d'entrée : sources, codes d'occupation du sol et coefficients de friction

### A.1. Sources de données

| Source | Produit / version | Rôle dans la chaîne | Accès | Licence |
|---|---|---|---|---|
| ESA WorldCover | version 200 (millésime 2021, résolution 10 m) | couche d'occupation du sol de base | Google Earth Engine (xee) | CC-BY 4.0 |
| OpenStreetMap | export daté au traitement | bâti, routes, voies ferrées et grandes emprises (codes 51 à 55) brûlés sur WorldCover | Overpass / OSMnx | ODbL |
| GBIF | occurrences téléchargées au traitement | validation par occurrences (chapitre 4) | API GBIF (pygbif) | CC0 / CC-BY selon le jeu |
| Cerema Dter Sud-Ouest | étude La Rochelle, 2025 | référence de calibration des frictions et des distances d₀, territoire de comparaison | rapport publié | référence méthodologique |
| Limites administratives | emprises des territoires | définition des aires d'étude | OpenStreetMap | ODbL |

### A.2. Correspondance des codes d'occupation du sol

Les codes 10 à 95 proviennent de WorldCover ; les codes 51 à 55 sont ajoutés à partir
d'OpenStreetMap et brûlés par-dessus WorldCover selon un ordre de priorité (50, 80, 51, 52, 53, 55,
54) : le bâti et l'eau servent de fond, puis les infrastructures OpenStreetMap sont posées par emprise
et fiabilité décroissantes, les chemins et sentiers (54) en dernier, ceux-ci ne recouvrant un pixel que
s'il n'est pas déjà un habitat du profil.

| Code | Occupation du sol | Source |
|---|---|---|
| 10 | Couvert arboré | WorldCover |
| 20 | Arbustes | WorldCover |
| 30 | Prairies et végétation herbacée | WorldCover |
| 40 | Cultures | WorldCover |
| 50 | Bâti (WorldCover) | WorldCover |
| 60 | Sols nus, végétation clairsemée | WorldCover |
| 80 | Eaux permanentes | WorldCover |
| 90 | Zones humides herbacées | WorldCover |
| 95 | Mangroves | WorldCover |
| 51 | Bâtiments | OpenStreetMap |
| 52 | Routes principales (autoroute, nationale) | OpenStreetMap |
| 53 | Routes secondaires et voirie | OpenStreetMap |
| 54 | Chemins et sentiers | OpenStreetMap |
| 55 | Voies ferrées | OpenStreetMap |

La rastérisation retient une seule classe par pixel selon la règle du centre : une emprise
OpenStreetMap, bien que géométriquement précise, ne code un pixel de dix mètres que si le centre de
celui-ci tombe à l'intérieur de l'emprise, sans pondération de surface ni règle de majorité. Les routes
et voies ferrées, tamponnées avant d'être brûlées selon une largeur fixée par catégorie (de 10 à
30 mètres), couvrent le plus souvent les centres de pixels et sont donc mieux restituées que les
bâtiments. Les bâtiments,
en revanche, ne sont pas tamponnés : un bâtiment qui n'occupe qu'une partie d'un pixel sans en couvrir
le centre laisse ce pixel dans sa classe WorldCover, généralement perméable, et un bâtiment plus petit
que dix mètres ou réparti sur plusieurs pixels peut n'en coder aucun ; à l'inverse, une emprise couvrant
le centre bascule le pixel entier en bâti. Cette limite de résolution, discutée au chapitre 4 (§4.6),
explique que le tracé des corridors doive être lu à l'échelle du tissu urbain et non au mètre près.

Deux traitements en aval accentuent ce caractère indicatif. Le chemin de moindre coût est calculé sur
une grille à huit directions (algorithme MCP_Geometric) : les pas diagonaux y sont correctement
pondérés par la distance géométrique, mais en zone de faible contraste de résistance plusieurs tracés
ont exactement le même coût, et la solution retenue regroupe les pas diagonaux, d'où des segments
à 45 degrés. Les lignes sont ensuite simplifiées (Douglas-Peucker, tolérance 3 mètres) puis lissées par
arrondi des angles, leurs extrémités étant réancrées sur les nœuds : le tracé affiché peut alors
s'écarter de quelques mètres des pixels de moindre coût et couper un angle que le chemin brut
contournait. Aucun de ces traitements ne modifie les liens du réseau ni leur coût cumulé ; ils
n'affectent que le rendu géométrique du corridor.

### A.3. Coefficients de friction par profil écologique

Coût de déplacement attribué à chaque code, sur une échelle de 1 (milieu le plus favorable) à 100.
Les valeurs sont transposées de la méthode du Cerema Dter Sud-Ouest (2025) vers la nomenclature agrégée
de WorldCover, chaque code WorldCover regroupant plusieurs classes du Cerema (moyenne des valeurs
correspondantes). Un code est considéré comme habitat du profil lorsque sa friction est inférieure
ou égale à 3. La mention ∞ désigne une classe infranchissable (friction infinie, non traversée par
le chemin de moindre coût). La distance caractéristique de dispersion d₀ est rappelée en tête de
colonne.

| Code | Occupation du sol | Hérisson (d₀ 3000 m) | Écureuil (d₀ 2000 m) | Fauvette (d₀ 1500 m) | Lézard (d₀ 750 m) |
|---|---|---|---|---|---|
| 10 | Couvert arboré | 1 | 1 | 2 | 4 |
| 20 | Arbustes | 1 | 6 | 1 | 4 |
| 30 | Prairies, herbacées | 2 | 4 | 7 | 1 |
| 40 | Cultures | 6 | 7 | 6 | 5 |
| 50 | Bâti (WorldCover) | 10 | 10 | 10 | 10 |
| 60 | Sols nus | 10 | 10 | 10 | 3 |
| 80 | Eaux permanentes | ∞ | 9 | 7 | ∞ |
| 90 | Zones humides herbacées | 8 | 8 | 6 | 8 |
| 95 | Mangroves | 8 | 8 | 6 | 8 |
| 51 | Bâtiments | ∞ | ∞ | 100 | ∞ |
| 52 | Routes principales | 100 | 100 | 100 | 100 |
| 53 | Routes secondaires, voirie | 50 | 50 | 50 | 50 |
| 54 | Chemins et sentiers | 5 | 8 | 8 | 3 |
| 55 | Voies ferrées | 10 | 9 | 7 | 3 |

### A.4. Environnement logiciel

La chaîne est exécutée sous Python 3.11 avec les versions suivantes des bibliothèques principales :
xarray 2026.4, rioxarray 0.19, geopandas 1.1, shapely 2.1, rasterio 1.4, networkx 3.6,
scikit-image 0.26, numpy 2.4, pandas 3.0. Ces versions sont fixées pour garantir la reproductibilité
des résultats (principe FAIR, chapitre 6).

## Annexe B. Ratios de sélection GBIF, détail par territoire

Le Tableau 5 donne les effectifs d'occurrences focales retenus (après filtrage et
sous-échantillonnage) par profil et par territoire. Sur les vingt couples, huit seulement atteignent le
seuil de trente occurrences ; Toulouse est la seule ville à le franchir pour les quatre profils, ce qui
explique que les ratios agrégés reflètent surtout ce territoire (67 à 76 % des occurrences selon le
profil). Les effectifs inférieurs à trente sont marqués d'un astérisque.

[TABLEAU : Effectifs d'occurrences focales GBIF par profil écologique et par territoire. (d'après les données GBIF, 2026)]

| Profil écologique (espèce repère) | Perpignan | Toulouse | Nancy | La Roche-sur-Yon | La Rochelle | Total |
|---|--:|--:|--:|--:|--:|--:|
| Petit mammifère terrestre (hérisson) | 4* | 64 | 3* | 9* | 9* | 89 |
| Mammifère arboricole (écureuil) | 15* | 129 | 39 | 6* | 4* | 193 |
| Oiseau de lisière (fauvette) | 126 | 710 | 29* | 40 | 89 | 994 |
| Reptile terrestre (lézard) | 1* | 222 | 19* | 26* | 23* | 291 |

* effectif inférieur à trente, couple non interprétable isolément.

Chaque profil écologique est représenté par un groupe de quatre espèces ubiquistes en France
métropolitaine : le mammifère arboricole par l'écureuil roux (*Sciurus vulgaris*), le loir gris
(*Glis glis*), le muscardin (*Muscardinus avellanarius*) et le lérot (*Eliomys quercinus*) ; l'oiseau
de lisière par la fauvette à tête noire (*Sylvia atricapilla*), le rougegorge familier (*Erithacus
rubecula*), la fauvette grisette (*Sylvia communis*) et la grive musicienne (*Turdus philomelos*) ; le
petit mammifère terrestre par le hérisson d'Europe (*Erinaceus europaeus*), la musaraigne pygmée (*Sorex
minutus*), le mulot sylvestre (*Apodemus sylvaticus*) et la belette d'Europe (*Mustela nivalis*) ; le
reptile terrestre par le lézard des murailles (*Podarcis muralis*), l'orvet fragile (*Anguis
fragilis*), la couleuvre d'Esculape (*Zamenis longissimus*) et le lézard à deux raies (*Lacerta
bilineata*).

[FIGURE : Ratios de sélection GBIF par territoire et agrégés, par profil et par classe, avec
intervalle de confiance à 95 %. (d'après les données GBIF, 2026)]

Au-delà des ratios par classe, un test global du khi-deux à trois degrés de liberté vérifie, pour
chaque profil, si les occurrences se répartissent entre les quatre classes différemment du fond
d'observation. Le test compare, classe par classe, les effectifs observés de l'espèce focale à ceux
qui seraient attendus si elle suivait exactement la répartition du fond d'observation (soit une absence
de sélection) ; un écart trop grand pour être dû au hasard signale une sélection. La table de
contingence a deux lignes (les effectifs de l'espèce focale et ceux du fond
d'observation) et quatre colonnes (noyau, relais, corridor, matrice). La sélection est hautement
significative pour l'oiseau de lisière, le mammifère arboricole et le petit mammifère terrestre, et non
significative pour le reptile, pour lequel aucune sélection n'est détectée. Ces valeurs restent
optimistes, le sous-échantillonnage spatial ne supprimant pas toute dépendance entre occurrences
voisines (Legendre, 1993).

| Profil | Occurrences | khi-deux (3 ddl) | p | Sélection |
|---|---|---|---|---|
| Fauvette à tête noire | 994 | 166,2 | inférieur à 0,001 | significative |
| Écureuil roux | 193 | 44,1 | inférieur à 0,001 | significative |
| Hérisson d'Europe | 89 | 29,5 | inférieur à 0,001 | significative |
| Lézard des murailles | 291 | 4,5 | 0,21 | non significative |

## Annexe C. Occurrences GBIF superposées aux noyaux, espaces relais et tracés de moindre coût, par profil

[FIGURE : Cartes d'occurrences du profil des oiseaux de lisière (fauvette), un panneau par
territoire. (d'après les données GBIF, 2026)]

[FIGURE : Cartes d'occurrences du profil des mammifères arboricoles (écureuil), un panneau par
territoire. (d'après les données GBIF, 2026)]

[FIGURE : Cartes d'occurrences du profil des petits mammifères terrestres (hérisson), un panneau par
territoire. (d'après les données GBIF, 2026)]

[FIGURE : Cartes d'occurrences du profil des reptiles terrestres (lézard), un panneau par
territoire. (d'après les données GBIF, 2026)]

## Annexe D. Indicateurs de connectivité par territoire et par profil écologique

La couverture d'habitat de la zone d'étude (proxy de
végétalisation du territoire) est de 50 % à La Roche-sur-Yon, 49 % à Nancy, 39 % à Perpignan, 53 % à
Kourou, 32 % à Toulouse et 20 % à La Rochelle. « Habitat connecté » = part d'habitat fonctionnellement
connecté ; « sous-réseaux » = nombre de composantes connexes du réseau réel dans la zone d'étude ;
« EC » = surface connectée équivalente.

| Territoire | Profil écologique | Habitat connecté | Sous-réseaux | EC (ha) |
|---|---|--:|--:|--:|
| La Roche-sur-Yon | Petit mammifère terrestre | 83 % | 1 | 20 864 |
|  | Mammifère arboricole | 28 % | 1 | 2 747 |
|  | Oiseau de lisière | 19 % | 1 | 1 932 |
|  | Reptile terrestre | 16 % | 3 | 2 321 |
| Nancy | Petit mammifère terrestre | 71 % | 1 | 4 916 |
|  | Mammifère arboricole | 56 % | 1 | 2 676 |
|  | Oiseau de lisière | 52 % | 1 | 2 468 |
|  | Reptile terrestre | 23 % | 7 | 479 |
| Perpignan | Petit mammifère terrestre | 64 % | 1 | 1 707 |
|  | Mammifère arboricole | 28 % | 3 | 209 |
|  | Oiseau de lisière | 27 % | 5 | 389 |
|  | Reptile terrestre | 23 % | 14 | 270 |
| Kourou | Petit mammifère terrestre | 70 % | 2 | 4 516 |
|  | Mammifère arboricole | 82 % | 1 | 3 733 |
|  | Oiseau de lisière | 69 % | 1 | 3 134 |
|  | Reptile terrestre | 45 % | 4 | 852 |
| Toulouse | Petit mammifère terrestre | 52 % | 1 | 7 674 |
|  | Mammifère arboricole | 27 % | 1 | 2 445 |
|  | Oiseau de lisière | 21 % | 3 | 1 965 |
|  | Reptile terrestre | 9 % | 8 | 442 |
| La Rochelle | Petit mammifère terrestre | 40 % | 1 | 2 632 |
|  | Mammifère arboricole | 17 % | 11 | 253 |
|  | Oiseau de lisière | 15 % | 28 | 223 |
|  | Reptile terrestre | 34 % | 14 | 1 627 |

## Annexe E. Analyse de sensibilité : synthèse par territoire et par profil écologique

> Couverture : vingt-quatre couples, soit les six territoires par les quatre profils écologiques.

[TABLEAU : Synthèse de sensibilité par territoire et par profil écologique : valeur de référence, plage sur le balayage de d₀ (50 à 120 % de la référence) et plage sur le balayage du contraste de friction (0 à 200 %).]

| Territoire | Profil écologique | Connecté réf. | Connecté (d₀) | Connecté (contraste) | Sous-rés. réf. | Sous-rés. (d₀) | Sous-rés. (contraste) |
|---|---|--:|--:|--:|--:|--:|--:|
| Kourou | Petit mammifère terrestre | 70 % | 69–70 % | 70–97 % | 2 | 2–3 | 1–2 |
| Kourou | Mammifère arboricole | 82 % | 60–84 % | 73–98 % | 1 | 1 | 1 |
| Kourou | Oiseau de lisière | 69 % | 51–75 % | 57–96 % | 1 | 1–2 | 1 |
| Kourou | Reptile terrestre | 45 % | 42–47 % | 43–61 % | 4 | 3–8 | 1–7 |
| Perpignan | Petit mammifère terrestre | 64 % | 52–68 % | 54–96 % | 1 | 1–3 | 1–2 |
| Perpignan | Mammifère arboricole | 28 % | 20–30 % | 21–74 % | 3 | 1–12 | 1–10 |
| Perpignan | Oiseau de lisière | 27 % | 21–30 % | 21–77 % | 5 | 3–22 | 1–18 |
| Perpignan | Reptile terrestre | 23 % | 18–26 % | 19–50 % | 14 | 14–25 | 1–22 |
| Nancy | Petit mammifère terrestre | 71 % | 55–74 % | 60–96 % | 1 | 1 | 1 |
| Nancy | Mammifère arboricole | 56 % | 50–59 % | 51–90 % | 1 | 1–3 | 1 |
| Nancy | Oiseau de lisière | 52 % | 46–54 % | 47–88 % | 1 | 1–5 | 1–4 |
| Nancy | Reptile terrestre | 23 % | 19–25 % | 20–51 % | 7 | 2–26 | 1–22 |
| La Rochelle | Petit mammifère terrestre | 40 % | 34–42 % | 35–81 % | 1 | 1–3 | 1–2 |
| La Rochelle | Mammifère arboricole | 17 % | 15–18 % | 15–38 % | 11 | 7–47 | 1–42 |
| La Rochelle | Oiseau de lisière | 15 % | 13–16 % | 14–32 % | 28 | 19–74 | 1–72 |
| La Rochelle | Reptile terrestre | 34 % | 29–35 % | 30–53 % | 14 | 7–96 | 1–80 |
| La Roche-sur-Yon | Petit mammifère terrestre | 83 % | 72–85 % | 75–98 % | 1 | 1 | 1 |
| La Roche-sur-Yon | Mammifère arboricole | 28 % | 18–31 % | 20–74 % | 1 | 1–3 | 1–2 |
| La Roche-sur-Yon | Oiseau de lisière | 19 % | 14–22 % | 14–68 % | 1 | 1–14 | 1–10 |
| La Roche-sur-Yon | Reptile terrestre | 16 % | 11–18 % | 12–51 % | 3 | 3–13 | 1–11 |
| Toulouse | Petit mammifère terrestre | 52 % | 38–55 % | 41–91 % | 1 | 1 | 1 |
| Toulouse | Mammifère arboricole | 27 % | 20–28 % | 21–72 % | 1 | 1–5 | 1–4 |
| Toulouse | Oiseau de lisière | 21 % | 17–23 % | 17–66 % | 3 | 2–23 | 1–19 |
| Toulouse | Reptile terrestre | 9 % | 7–9 % | 7–22 % | 8 | 5–122 | 1–84 |
