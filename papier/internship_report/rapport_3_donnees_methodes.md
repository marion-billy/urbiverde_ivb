# 2. Données et méthodes

> Brouillon. Corps impersonnel et sourcé : chaque choix de méthode est justifié sur place
> (alternative écartée, référence, limite assumée). La réflexion d'ingénieur en première personne
> (récit des choix, alignement, débogage) est portée par le chapitre 6 (retour d'expérience), non par
> des encadrés. [À VÉRIFIER] / [À COMPLÉTER] = à confirmer ; [À VALIDER : …] = proposition à valider.

Ce chapitre décrit la chaîne de traitement de bout en bout : les territoires d'étude (§2.1), les données
ouvertes qui l'alimentent (§2.2), les profils écologiques et leur calibration (§2.3), les étapes de
calcul des continuités (§2.4), l'implémentation logicielle et le contrôle automatisé des sorties (§2.5)
et leur restitution dans un tableau de bord (§2.6).

## 2.1. Territoires d'étude

La chaîne a été appliquée à des territoires aux contextes bioclimatiques volontairement contrastés
(Figure 4). Quatre villes pilotes du projet UrbiVerde ont servi de terrains de développement : La
Roche-sur-Yon (agglomération, façade atlantique), Nancy (métropole du Grand Nancy, climat continental
du nord-est), Perpignan (commune, climat méditerranéen) et Kourou, en Guyane (climat équatorial). Deux
territoires supplémentaires ont servi à contrôler et valider les sorties : Toulouse (métropole), retenue
comme cas de contrôle visuel, en raison d'une bonne connaissance de terrain, et l'agglomération de La Rochelle,
territoire de la méthode Cerema Dter Sud-Ouest à laquelle ce travail se compare et dont il emprunte une
partie de la calibration (détaillée en §2.3).

[FIGURE : Localisation des six territoires d'étude. (fond de carte OpenStreetMap, 2026)]

Pour chaque territoire, la zone d'étude est définie à partir de ses limites administratives, Kourou
faisant exception avec une emprise rectangulaire, sa limite communale étant trop restreinte pour
englober les espaces périurbains pertinents. Elle est ensuite élargie par un tampon égal à
deux fois la plus grande distance de dispersion considérée (soit 6 km).
Ce tampon corrige l'effet de bord, une frontière de carte artificielle se comportant comme une
barrière qui sous-estime la connectivité des taches périphériques (Koen et al., 2010, 2014) : un
corridor peut s'appuyer sur une tache d'habitat située juste
en dehors de la limite administrative, qui serait ignorée si l'analyse s'arrêtait à cette limite.
Les habitats du tampon servent ainsi de relais au calcul, mais seules les composantes situées dans la
zone d'étude stricte sont comptabilisées dans les résultats.

La superficie de la zone d'étude, tampon compris, varie fortement d'un territoire à l'autre, de 68 km²
à Perpignan à 502 km² à La Roche-sur-Yon (Tableau 1). Cette différence d'emprise tient à la
taille des limites administratives retenues ; il faut en tenir compte pour lire en valeur absolue les
surfaces d'habitat et la surface connectée équivalente (définies en §2.4), qui croissent mécaniquement
avec l'étendue du territoire. La part d'habitat connecté, normalisée, reste elle comparable d'un site à l'autre.

[TABLEAU : Les six territoires d'étude, leur statut et la superficie de la zone d'étude (tampon de 6 km inclus).]

| Territoire | Statut | Contexte bioclimatique | Zone d'étude (km², tampon inclus) |
|---|---|---|---|
| La Roche-sur-Yon | pilote | atlantique | 502 |
| Nancy | pilote | continental (nord-est) | 143 |
| Perpignan | pilote | méditerranéen | 68 |
| Kourou (Guyane) | pilote | équatorial | 123 |
| Toulouse | contrôle visuel | océanique à influence méditerranéenne | 461 |
| La Rochelle | validation (comparaison Cerema) | atlantique | 331 |

Kourou occupe un statut à part. C'est un territoire pilote d'UrbiVerde, mais la connectivité écologique
n'y est pas l'enjeu le plus pertinent, d'autres indicateurs de la plateforme y faisant davantage sens ;
et les profils écologiques, calibrés sur des espèces de métropole, n'y représentent pas la faune locale.
Il sert donc ici de test de transposabilité de la chaîne à un biome très différent, non de diagnostic
écologique directement exploitable (réserve développée en section 4.2).


## 2.2. Données et acquisition

La chaîne part d'une couche d'occupation du sol, qui attribue à chaque pixel une classe de milieu
(arbres, prairies, bâti, eau…) : c'est d'elle que sont dérivés l'habitat propre à chaque profil
écologique et la résistance de la matrice au déplacement. Cette couche repose sur le produit mondial
ESA WorldCover (version 200, résolution
10 m ; Zanaga et al., 2021), dérivé des imageries Sentinel-1 et Sentinel-2 et récupéré via Google
Earth Engine sur l'emprise tamponnée. WorldCover distingue onze classes, parmi lesquelles les arbres (code 10), les
arbustes (20), les prairies (30), les cultures (40), les surfaces bâties et imperméabilisées (50), les sols nus (60),
l'eau (80), les zones humides (90) et les mangroves (95).

Ce produit ne représente toutefois pas les infrastructures fragmentantes (routes, voies ferrées) avec
la finesse requise, alors qu'elles constituent les principales barrières au déplacement terrestre.
Celles-ci sont donc ajoutées à partir des données ouvertes d'OpenStreetMap, dont la complétude du
réseau routier est bonne en milieu urbain (Barrington-Leigh & Millard-Ball, 2017) : réseaux routiers,
voies ferrées, emprises bâties et surfaces en eau, ainsi que certaines surfaces artificialisées gérées
(aéroports, stades). Ces éléments sont rastérisés et brûlés par-dessus le WorldCover selon un ordre
de priorité fixe (détaillé en annexe A), ce qui ajoute aux codes WorldCover des codes spécifiques
d'occupation artificialisée : emprises bâties (51), routes principales et autoroutes (52), routes
secondaires (53), chemins (54) et voies ferrées (55) ; l'occupation du sol enrichie est illustrée Figure 5 pour Toulouse. Toutes les analyses sont menées dans la projection métrique locale (UTM)
propre à chaque territoire, les distances et surfaces étant exprimées en mètres, mètres carrés et
hectares.

[FIGURE : Occupation du sol enrichie de Toulouse. (d'après ESA WorldCover et OpenStreetMap, 2026)]

Le recours à des données ouvertes et mondiales (WorldCover, OpenStreetMap) plutôt qu'aux référentiels
nationaux plus fins disponibles en France (OCS GE, CoSIA) répond à l'objectif de reproductibilité de
l'outil et rejoint la priorité « réutiliser l'existant » fixée par l'ESA : une donnée mondiale,
gratuite et homogène garantit une chaîne identique et comparable d'un territoire à l'autre, là où un
référentiel national, même de meilleure qualité, reste limité à la France et interdit une transposition
mondiale. La contrepartie, assumée, est une perte de détail : la résolution de 10 m est grossière pour
les éléments linéaires fins et ne capte que les grandes surfaces d'eau (Radoux et al., 2016). Une
itération future sur un territoire français exigeant plus de précision pourrait réalimenter la chaîne
avec un produit comme Green Urban Sat (GUS, Cerema), qui cartographie les strates de végétation urbaine
à partir d'imagerie Pléiades [à sourcer : documentation GUS, Cerema], au prix d'une adaptation des classes d'occupation du sol. Ce compromis
précision/reproductibilité est discuté au chapitre 4.

Une correction de qualité est appliquée en amont de la chaîne : WorldCover classe la pelouse rase des
aérodromes et des stades en prairie, que les profils écologiques de milieux ouverts compteraient à tort
comme habitat ; ces emprises, repérées par leurs tags OpenStreetMap, sont gravées en surface
imperméable pour les exclure.

## 2.3. Profils écologiques et calibration

La chaîne repose sur deux choix liés : raisonner par profils écologiques plutôt que par une espèce
focale unique, et calibrer leurs paramètres sur une méthode de référence, celle du Cerema, direction
territoriale Sud-Ouest (Dter Sud-Ouest), sur les continuités écologiques urbaines de la Communauté
d'agglomération de La Rochelle (Cerema Dter Sud-Ouest, 2025).

Raisonner par profil restitue les besoins de continuité propres à chaque capacité de déplacement,
qu'une entrée par espèce focale unique laisserait invisibles. L'outil s'inscrit dans la lignée des
approches par espèces focales génériques et par groupes fonctionnels (Lambeck, 1997 ; Watts et al.,
2010 ; Meurant et al., 2018 ; Kirk et al., 2023 ; Albert & Chaurant, 2018) : chaque profil écologique (écoprofil) est un syndrome
écologique nommé d'après une espèce repère ubiquiste en France métropolitaine, et défini par ses codes
d'habitat, sa distance caractéristique de dispersion d₀ et ses coefficients de friction par classe
d'occupation du sol ; ces traits sont documentés pour les espèces repères retenues (Morris, 1988 ;
Huijser & Bergers, 2000 ; Avon et al., 2014 ; Tarabon et al., 2019) et rassemblés en vue de leur
application aux corridors (Quiblier, 2007). La notion d'écoprofil remonte à Vos et al. (2001), qui
définissent un profil par ses exigences d'habitat et sa capacité de déplacement ; ces deux critères
sont repris ici, mais non le troisième qu'ils y ajoutent, une surface minimale d'habitat. Quatre
profils écologiques sont retenus (Tableau 2).

[TABLEAU : Caractéristiques des quatre profils écologiques (espèce repère, distance de
dispersion, habitat, obstacles infranchissables). (d'après Cerema Dter Sud-Ouest, 2025)]

| Profil écologique | Espèce repère | d₀ (m) | Habitat | Obstacles infranchissables |
|---|---|--:|---|---|
| Petit mammifère terrestre | Hérisson d'Europe (*Erinaceus europaeus*) | 3000 | arbres, arbustes, prairies | bâtiments, grandes rivières |
| Mammifère arboricole | Écureuil roux (*Sciurus vulgaris*) | 2000 | arbres | bâtiments |
| Oiseau de lisière boisée | Fauvette à tête noire (*Sylvia atricapilla*) | 1500 | arbres, arbustes | aucune |
| Reptile thermophile de milieux ouverts | Lézard des murailles (*Podarcis muralis*) | 750 | prairies, sols nus | bâtiments, grandes rivières |

Ces paramètres sont calibrés sur la méthode du Cerema Dter Sud-Ouest, dont le travail reprend la logique
(décrite dans l'état de l'art, §1.5) et les valeurs de calibration, sans l'appliquer pour autant à
l'identique.

D'abord, cette référence agrège elle-même plusieurs sources. Les coefficients de friction sont empruntés à sa
table (2025, pp. 96-98), pris pour l'espèce repère de chaque profil ;
mais cette table est elle-même une compilation documentée de la littérature et de dires d'expert, dont
la sensibilité est un point établi du champ (Zeller et al., 2012 ; Beier et al., 2008 ; Stevenson-Holt
et al., 2014). Ces valeurs sont ensuite réinterprétées au niveau du syndrome écologique du profil,
transposées à la nomenclature agrégée de WorldCover, et ajustées par des règles propres à la chaîne
(seuil d'habitat, barrières infranchissables, échelle finie des routes, traitement de l'eau), détaillées
plus bas. Ensuite, l'entrée diffère : le travail raisonne par profil écologique, chacun porté par une
seule espèce repère, là où le Cerema moyenne les frictions de plusieurs espèces réunies dans un
même cortège par sous-trame, ce qui suppose une occupation du sol plus fine que WorldCover. Enfin, il
mobilise des données ouvertes mondiales plutôt que l'occupation du sol nationale (OCS GE,
CoSIA, BD TOPO, RPG de l'IGN). Cette référence est ainsi autant un socle de calibration qu'un
territoire de comparaison (§3.5, §4.4).

Les coefficients de friction de chaque profil écologique, sur une échelle de 1 (milieu optimal) à 100
(obstacle), sont obtenus en transposant ces valeurs à la nomenclature, plus agrégée, de WorldCover : chaque classe WorldCover regroupant plusieurs classes d'origine, le coefficient retenu est la moyenne des valeurs correspondantes. Une classe d'occupation du sol est
considérée comme habitat du profil écologique lorsque sa friction est inférieure ou égale à 3 : dans cette
table, les milieux qui constituent l'habitat de chaque espèce repère reçoivent un coût de 1 à
3, tandis que la matrice seulement traversée reçoit 4 ou davantage ; le seuil de 3 sépare donc l'habitat
du profil des milieux qu'il franchit sans s'y installer. Le détail de cette correspondance et des
coefficients figure en annexe A. Comme dans la littérature sur les surfaces de résistance, ces coûts
traduisent l'écologie de l'espèce repère (préférences d'habitat, capacité et mode de déplacement) plus
que la seule occupation du sol (Zeller et al., 2012 ; Beier et al., 2008), base écologique héritée de
cette table plutôt que recalibrée. Le choix d'une table d'expert et de littérature, plutôt que de coûts
dérivés d'un modèle d'occurrence, tient à ce que la sélection d'habitat ne recouvre pas le déplacement,
les deux ne répondant pas aux mêmes motivations (Van Dyck & Baguette, 2005). Ce qui structure le résultat est moins le niveau absolu de
ces coefficients que le contraste entre classes : c'est l'écart de résistance entre l'habitat et la
matrice, plus que la valeur retenue pour chacun, qui oriente le tracé des corridors (Bowman et al.,
2020) ; les estimations de connectivité restent d'ailleurs assez robustes à l'incertitude sur les valeurs de
friction retenues (Simpkins et al., 2017), ce que confirme l'analyse de sensibilité (§3.4).

Les distances caractéristiques de dispersion d₀ (tableau ci-dessus) sont reprises des fiches espèces du
Cerema Dter Sud-Ouest (2025), qui documentent et sourcent la capacité de déplacement de chaque espèce repère : le hérisson d'Europe parcourt 2 à 3 km par nuit dans un rayon d'environ 4 km et l'écureuil
roux disperse sur environ 3 km (Macdonald & Barrett, 2005), la fauvette à tête noire couvre 1 à 2 km,
et le lézard des murailles atteint au plus environ 1 km (Pottier, 2016 ; Vacher & Geniez, 2010). Les
valeurs retenues (3000, 2000, 1500 et 750 m) se situent dans ces plages.

L'adaptation de cette référence à un outil reproductible sur données ouvertes conduit à quatre choix
explicites, distincts d'une reprise à l'identique. Le nombre de profils écologiques est ramené de cinq à
quatre : le profil « insecte des milieux herbacés » initialement prévu se réduit, après alignement, au
même habitat que le reptile (milieux ouverts) et en devient redondant, le Cerema réunissant lui-même
lézard et orthoptères dans un unique cortège herbacé. Les routes conservent une échelle de friction
finie (autoroute 100, route secondaire 50) plutôt qu'un statut strictement infranchissable, afin qu'un
lien puisse les franchir à coût élevé et que les points de rupture ressortent comme points de conflit ;
le statut infranchissable est réservé au bâti et aux grandes rivières. Le bâti n'est pas valorisé comme
habitat : là où le Cerema attribue au lézard un coût faible sur les murs, un coût d'obstacle est
maintenu, car le signaler comme favorable contredirait l'objectif de dé-fragmentation urbaine de
l'outil. Enfin, la trame bleue et les milieux humides sont écartés, le Cerema lui-même ne les traitant
pas par moindre coût faute de méthode et de données adaptées (limite assumée, chapitre 4).

## 2.4. Chaîne de traitement

La chaîne de traitement conduit, pour chaque couple (territoire, profil écologique), du produit
d'occupation du sol aux indicateurs de connectivité. Elle produit successivement les noyaux de
biodiversité, le graphe de connectivité, les tracés de moindre coût, les points de rupture et les
cartes de dispersion. Ces étapes sont synthétisées Figure 6.

[FIGURE : Schéma synoptique de la chaîne de traitement, des données d'entrée
(WorldCover, OSM) aux sorties (noyaux, tracés de moindre coût, ruptures, dispersion, indicateurs).]

La première étape prépare la
couche d'occupation du sol : le WorldCover est découpé sur l'emprise élargie par le tampon, puis les
infrastructures OpenStreetMap y sont brûlées par-dessus (section 2.2). Une couche d'habitat binaire en est extraite, ne retenant que les classes d'habitat du
profil écologique, puis soumise à une analyse morphologique de type MSPA (morphological spatial
pattern analysis ; Vogt et al., 2007 ; Soille & Vogt, 2009), implémentée sous scikit-image : une
érosion suivie d'une dilatation isole les noyaux de biodiversité, taches dont le coeur compact dépasse
un hectare, des
espaces relais plus petits (de 0,1 à 1 hectare) qui jouent le rôle de pas japonais (Figure 7).

Les seuils de surface retenus (noyau ≥ 1 ha, relais 0,1 à 1 ha) sont un choix de la chaîne, non une
valeur imposée par la méthode : la segmentation morphologique classe les pixels selon la largeur de
bord et ne fixe aucun seuil de surface canonique (Ostapowicz et al., 2008 ; Vogt & Riitters, 2017). Le
seuil de 1 ha est retenu comme surface minimale plausible d'un habitat fonctionnel en ville et pour la
lisibilité de la restitution ; il rejoint directement la référence de calibration, le Cerema Dter Sud-Ouest
(2025) retenant, par la même méthode de cœurs compacts (érosion −10 m puis dilatation +10 m), un seuil
de 1 ha pour les sous-trames arborée, arbustive et mixte (et 5 000 m² pour l'herbacée). Adopter un
seuil unique de 1 ha est ici une simplification assumée.

[FIGURE : Exemple de segmentation morphologique (MSPA) : noyaux de biodiversité
(coeur ≥ 1 ha) et espaces relais (0,1 à 1 ha), profil du petit mammifère terrestre de lisière, sur un
secteur de Perpignan.]

Ces taches deviennent les noeuds d'un graphe de Gabriel (networkx) construit sur les distances de
bord à bord : deux taches sont reliées lorsque aucune autre tache ne s'intercale dans le cercle dont
le segment les joignant constitue le diamètre (graphe de Gabriel ; Gabriel & Sokal, 1969 ; Figure 8), dans la limite d'une distance de recherche fixée à
deux fois la distance de dispersion du profil écologique. À chaque lien est associée une probabilité de
déplacement qui décroît avec la distance selon un noyau négatif-exponentiel, forme standard des graphes
paysagers pour sa parcimonie (Foltête et al., 2012) :

[EQUATION 1: p_{ij} = \exp(-d_{ij}/d_0)]

où dᵢⱼ est la distance de bord à bord entre les taches i et j, et d₀ la distance caractéristique de
dispersion du profil écologique (§2.3) : la distance à laquelle la probabilité de déplacement retombe à
environ 37 % (soit 1/e). Sur ce graphe est d'abord calculée la Probability of Connectivity (PC ; Saura
& Pascual-Hortal, 2007), qui mesure la connectivité potentielle à vol d'oiseau, indépendamment de la
résistance du paysage :

[EQUATION 2: \mathrm{PC} = \frac{\sum_i \sum_j a_i\,a_j\,p_{ij}}{A^2}]

où aᵢ et aⱼ sont les surfaces des taches i et j, pᵢⱼ la probabilité de déplacement de l'équation (1)
entre elles, et A la surface totale de la zone d'étude. La PC s'interprète
comme la probabilité que deux points tirés au hasard dans la zone tombent dans des taches mutuellement
accessibles ; elle est comprise entre 0 et 1.

Le choix du graphe de Gabriel parmi les graphes de proximité conditionne les connexions retenues.
Trois variantes ont été implémentées et comparées avant de trancher. Les plus parcimonieuses (arbre
couvrant minimal, graphe de voisinage relatif) ne conservent qu'un unique chemin entre taches et
effacent la redondance des passages, tandis que les k plus proches voisins reposent sur un paramètre
arbitraire qui tend à sur-connecter le réseau. Dans la hiérarchie
d'inclusion de ces graphes de proximité (Toussaint, 1980), le graphe de Gabriel offre un compromis : il
conserve des chemins alternatifs, plus réalistes écologiquement (un animal dispose rarement d'un
itinéraire unique), sans relier deux taches qu'une troisième sépare, et fait ainsi ressortir plusieurs
options de passage utiles à l'aide à la décision. Le niveau d'élagage du graphe influençant le résultat
de connectivité (Minor & Urban, 2008 ; Galpern et al., 2011), ce choix constitue un paramètre
méthodologique assumé.

[FIGURE : Construction du graphe de Gabriel : taches reliées selon le critère du cercle diamétral.]

La résistance du paysage est ensuite introduite : jusque-là les liens ne dépendaient que de la distance
à vol d'oiseau, alors que le déplacement réel dépend aussi de la nature des milieux traversés, plus ou
moins coûteux à franchir. Une surface de friction est dérivée de l'occupation
du sol selon les coefficients de friction du profil écologique (détaillés en annexe A), puis chaque lien du graphe est tracé comme
un chemin de moindre coût (Adriaensen et al., 2003) sur cette surface (algorithme MCP géométrique de
scikit-image). Un tel tracé est un trait de largeur nulle : le chemin optimal en coût n'indique pas
l'emprise d'un corridor à aménager mais l'endroit où un lien est le plus probable (Pinto & Keitt, 2009 ;
Shirabe, 2018), ce qui justifie de parler de « lien » ou de « tracé de moindre coût » plutôt que de
« corridor » pour ces sorties. Le coût accumulé d'un lien, exprimé en friction par mètre parcouru, est
comparé à un budget de déplacement, égal à la distance de dispersion du profil multipliée par un
coefficient favorable moyen de 3 :

[EQUATION 3: \mathrm{budget} = 3 \times d_0]

Ce facteur 3, convention de conversion d'une distance en coût reprise du Cerema, fixe le seuil de
fonctionnalité : en deçà, le lien est jugé fonctionnel ; au-delà, ou s'il rencontre un obstacle
infranchissable (bâti, grande rivière), il est marqué en échec. Les liens fonctionnels, les liens en échec et les points de rupture constituent les sorties
cartographiques. Un point de rupture est l'intersection d'un lien bloqué avec une infrastructure ; il
localise un lieu de conflit où un aménagement, par exemple un passage à faune, serait pertinent. Une carte de dispersion,
surface de coût cumulé propagé depuis l'ensemble des taches sources (Adriaensen et al., 2003) et bornée
au budget de déplacement, complète ce dispositif : elle représente l'étendue qu'un profil peut
atteindre depuis son habitat dans les limites de sa capacité de déplacement.

Le pré-filtre géométrique du graphe et le seuil de coût se cumulent. Le graphe de Gabriel ne relie
deux taches que si leur distance euclidienne est inférieure à deux fois la distance de dispersion, et
le coût du lien retenu est ensuite comparé au budget d₀ × 3, le critère de coût étant déterminant. Ce
plafond de distance est volontairement large : un corridor réellement fonctionnel reste bien plus
court que cette limite, de sorte que le pré-filtre géométrique n'écarte en pratique aucun corridor que
le seul critère de coût aurait retenu.

Plusieurs indicateurs caractérisent enfin l'état du réseau. La Probability of Connectivity réelle est
recalculée sur le réseau effectivement franchissable, en substituant à la distance à vol d'oiseau de
l'équation (2) le coût de déplacement sur la surface de résistance. La surface équivalente connectée
(Equivalent Connected Area ; Saura et al., 2011) la traduit en unité de surface :

[EQUATION 4: \mathrm{EC} = \sqrt{\mathrm{PC}} \times A]

où A est la surface de la zone d'étude. L'EC s'interprète comme la taille d'un unique bloc d'habitat
parfaitement connecté qui aurait la même PC que le réseau réel. Exprimée en hectares, elle et la part
d'habitat connectée qui en découle (EC rapportée à la surface d'habitat) sont plus explicites pour un
aménageur qu'une perte relative. Deux indicateurs complètent la lecture. Le nombre de
sous-réseaux correspond au nombre de composantes connexes du réseau réel, sur les seules taches de la
zone d'étude : un réseau connexe forme un seul ensemble relié (un seul sous-réseau), tandis que
plusieurs sous-réseaux traduisent un réseau fragmenté en parties non reliées entre elles. La tortuosité
des corridors rapporte leur longueur réelle à la distance à vol d'oiseau :
proche de 1, le corridor est quasi rectiligne et peu contraint ; élevée, il contourne des obstacles par
de longs détours, signe d'une matrice résistante et d'une connexion coûteuse.
Les corridors sont aussi découpés en segments de tracé, c'est-à-dire les portions situées
hors des taches d'habitat, qui localisent les espaces sur lesquels une action est possible.

## 2.5. Implémentation et reproductibilité

L'ensemble de la chaîne est implémenté en Python, sans recours à un logiciel de SIG externe ni à un
outil de connectivité existant (Graphab, Conefor, Circuitscape, extension Biodispersal sous QGIS). Ce
choix de ré-implémentation ne vise pas la nouveauté : les indices mobilisés sont ceux de la littérature
(§1.5), et la contribution réside dans leur assemblage en une chaîne unique.
Passer par ces logiciels, conçus pour un usage interactif au cas par cas, aurait interdit
l'automatisation de bout en bout, la reproductibilité sur des contextes contrastés et l'actualisation
dans le temps visées ici (objectif 3) ; les ré-implémenter donne le contrôle et la transparence du
calcul, au prix d'un effort de développement et de la charge de vérifier que chaque étape reproduit la
méthode de référence (§4.4). Les traitements raster reposent sur xarray et rioxarray, les
traitements vectoriels sur geopandas et shapely, la rastérisation sur rasterio, le graphe sur
networkx, et les calculs de moindre coût comme de morphologie sur scikit-image (versions précises en
annexe A.4) ; le calcul de la Probability of Connectivity est optimisé : plutôt que de
parcourir une à une toutes les paires de taches, il s'appuie sur un unique parcours de plus court
chemin et un produit matriciel, beaucoup plus rapides. Le produit d'occupation du sol WorldCover est récupéré via
Google Earth Engine (xee).

L'architecture sépare la configuration du code. Les paramètres de chaque profil écologique (habitat, distance de
dispersion, frictions) sont isolés dans un fichier de configuration dédié, et les chemins de sortie
sont centralisés. Un script unique pilote l'exécution, par territoire et, au besoin, par profil écologique, et
produit pour chaque couple une arborescence de sorties normalisée (Figure 9) : rasters d'occupation du sol,
d'habitat, de friction et de dispersion ; couches vectorielles des noeuds, tracés de moindre coût, liens en échec et
segments de tracé ; tableau d'indicateurs. Cette organisation rend la chaîne automatisable et
reproductible, une même commande régénérant l'intégralité des résultats d'un territoire. Le code est
versionné dans un dépôt Git [À COMPLÉTER : lien du dépôt], organisé autour du fichier de configuration,
du script d'exécution et des modules de traitement (préparation des données, connectivité, restitution).

[FIGURE : Arborescence normalisée des sorties, par territoire et par profil écologique.]

La chaîne intègre enfin un contrôle automatisé de ses sorties (`output_check.py`), exécuté à la fin de chaque
production : conformité de la projection (métrique, UTM), présence et non-vacuité des couches attendues
(noyaux, corridors), présence des indicateurs de tête, et plausibilité physique des valeurs (frictions
comprises entre 1 et 100 avec obstacles en coût infini, coûts de dispersion bornés au budget de
déplacement 3 × d₀). Il signale toute anomalie avant exploitation ; les
vingt-quatre jeux des six territoires l'ont passé sans anomalie. La robustesse des sorties aux choix de
calibration et leur confrontation à des sources externes relèvent en revanche de la discussion
(chapitre 4).

## 2.6. Restitution : le tableau de bord

Les sorties cartographiques ne deviennent un outil d'aide à la décision que si elles sont rendues
lisibles pour des aménageurs non spécialistes. Cette restitution prend la forme d'un tableau de bord
interactif, accessible en ligne, qui présente pour chaque territoire et chaque profil écologique les différentes
couches produites (noyaux de biodiversité, tracés de moindre coût, points de rupture, surface de dispersion) que
l'utilisateur peut afficher et superposer, ainsi que les indicateurs de connectivité associés. Le
tableau de bord permet d'explorer visuellement le réseau écologique d'un territoire et de comparer
des scénarios d'aménagement (Figure 10). Les sorties du pipeline sont d'abord converties en couches
légères : les géométries (aire d'étude, taches d'habitat, tracés de moindre coût, barrières, points de
rupture) au format GeoJSON, les indicateurs au format CSV, et le raster de dispersion en GeoTIFF. Le
tableau de bord est une application web développée en Python avec Plotly Dash, intégrée à
l'environnement de tableaux de bord de Murmuration ; la cartographie s'appuie sur Leaflet. L'utilisateur
affiche et superpose les couches, dessinées directement dans le navigateur ; le raster de dispersion,
plus lourd, est servi sous forme de tuiles dans la version en ligne, tandis que la version locale le
charge directement. L'accès est réservé aux utilisateurs authentifiés de Murmuration. À ce stade, le
tableau de bord constitue une brique autonome, bâtie sur les gabarits de Murmuration, et son intégration
à la plateforme UrbiVerde n'est pas encore réalisée.

[FIGURE : Capture d'écran du tableau de bord interactif (sélection d'un territoire et d'un profil écologique,
couches superposables, indicateurs).]
