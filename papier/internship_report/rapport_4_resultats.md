# 3. Résultats

> Brouillon. Corps impersonnel, factuel : ce chapitre décrit les sorties, l'interprétation est
> renvoyée au chapitre 4. Chiffres issus du re-run complet (6 villes, 4 profils écologiques).
> [FIGURE : …] = à insérer ; [À COMPLÉTER : …] = proposition ou chiffre à valider.

Ce chapitre présente, de façon descriptive, les sorties de la chaîne sur les six territoires : les couches produites (3.1),
les indicateurs de connectivité par profil écologique (3.2) et leur variation entre territoires (3.3),
la réponse des sorties aux variations de calibration (3.4), leur confrontation à des observations et à
une méthode de référence (3.5) et l'effet d'un scénario d'aménagement (3.6). L'interprétation de ces
résultats est développée au chapitre 4.

## 3.1. Un jeu de sorties normalisé pour chaque couple territoire-profil

Pour chaque couple (territoire, profil écologique), la chaîne produit le jeu de sorties normalisé
décrit au chapitre 2 (Figures 6 et 9) : rasters, couches vectorielles (noyaux de biodiversité, éléments
relais, liens fonctionnels, liens en échec, points de rupture) et tableau d'indicateurs. Sur les
six territoires et les quatre profils écologiques, vingt-quatre jeux de résultats ont été générés, tous
exprimés dans la projection métrique locale (UTM) et directement mobilisables en SIG comme dans le
tableau de bord (Figure 11).

[FIGURE : Sorties de la chaîne sur Perpignan pour deux profils écologiques contrastés : le petit
mammifère terrestre (à gauche, réseau connexe) et le reptile terrestre (à droite, réseau morcelé).
Noyaux de biodiversité, éléments relais, liens fonctionnels et liens en échec.]

À titre d'exemple, le profil écologique du petit mammifère terrestre sur Perpignan compte 525 noyaux de
biodiversité et 1 421 espaces relais, reliés par 1 075 liens fonctionnels. Perpignan sert
d'illustration parce qu'il offre, sur une emprise compacte, le contraste le plus lisible entre profils
écologiques (§3.3) : le réseau y passe d'un bloc unique et bien connecté pour le petit mammifère
terrestre à un réseau très morcelé pour le reptile.

## 3.2. Une part d'habitat connecté très variable selon le profil

L'indicateur retenu au premier plan est la part d'habitat fonctionnellement connecté (définie au
chapitre 2) : normalisée entre 0 et 100 %, elle reste comparable entre des territoires d'emprises
différentes, là où la surface connectée équivalente croît avec l'étendue. Le nombre de sous-réseaux, ou
composantes connexes (sous-ensembles de taches toutes accessibles les unes aux autres), la complète. Le Tableau 3 en donne la médiane et l'étendue
sur les six territoires, par profil écologique ; la tortuosité et les dénombrements (noyaux, relais,
corridors, ruptures) figurent dans les jeux de sorties et en annexe D.

[TABLEAU : Récapitulatif des indicateurs par profil écologique, sur les six territoires (étendue et médiane).]

| Profil écologique (espèce repère) | Sous-réseaux (méd. [min–max]) | Habitat connecté (méd. [min–max]) | Territoires à réseau connexe |
|---|---|---|---|
| Petit mammifère terrestre (hérisson) | 1 [1–2] | 67 % [40–83] | 5 / 6 |
| Mammifère arboricole (écureuil) | 1 [1–11] | 28 % [17–82] | 4 / 6 |
| Oiseau de lisière (fauvette) | 2 [1–28] | 24 % [15–69] | 3 / 6 |
| Reptile terrestre (lézard) | 7 [3–14] | 23 % [9–45] | 0 / 6 |

Les valeurs se distribuent entre deux extrêmes. Le petit mammifère terrestre est partout le profil le mieux
connecté : son réseau reste connexe dans cinq territoires sur six et sa part d'habitat
connecté est la plus élevée (médiane 67 %). Le reptile terrestre est à l'opposé : son réseau
n'est jamais connexe (3 à 14 sous-réseaux) et sa part d'habitat connecté est la plus basse
(médiane 23 %). Le mammifère arboricole et l'oiseau de lisière sont intermédiaires, avec une forte
variabilité entre territoires (l'oiseau de lisière reste connexe à Nancy, à La
Roche-sur-Yon et à Kourou, mais se fragmente en vingt-huit sous-réseaux à La Rochelle). L'écart entre
profils peut être marqué sur un même territoire : à Perpignan, le reptile terrestre connecte 23 % de
son habitat en quatorze sous-réseaux, quand le petit mammifère terrestre en connecte 64 % en un seul
réseau connexe ; les points de rupture des profils terrestres s'y concentrent sur les axes routiers.

Les surfaces de dispersion rendent ce contraste visible (Figure 12) : celle du petit mammifère terrestre
couvre le territoire d'un vert quasi continu, tandis que celle du reptile vire à l'orange et au rouge
au contact du tissu urbain.

[FIGURE : Surfaces de dispersion comparées de deux profils écologiques contrastés sur un même
territoire. Le petit mammifère terrestre couvre la quasi-totalité de la zone en restant loin de son budget
de dispersion (vert) ; le reptile atteint vite sa limite de portée (orange à rouge), surtout au
contact du tissu urbain.]

## 3.3. Contrastes entre territoires : un test de transposabilité

Appliquée à l'identique aux six territoires, sans aucun réglage propre à chaque site, la chaîne produit
sur chacun un jeu de sorties complet, des façades atlantique et continentale au climat méditerranéen et
équatorial. C'est le résultat direct de l'objectif de transposabilité (objectif 5) : une même commande
tourne de bout en bout sur des contextes bioclimatiques très différents. Les niveaux de connectivité
obtenus varient fortement d'un territoire à l'autre. Pour le petit mammifère terrestre, la part
d'habitat connecté s'échelonne de 83 % à La Roche-sur-Yon à 40 % à La Rochelle, en passant par Nancy
(71 %), Perpignan (64 %) et Toulouse (52 %) ; Kourou se distingue par des parts élevées sur tous les
profils écologiques (45 à 82 %). Le détail par territoire et par profil figure en annexe D.

Cette variation touche tous les profils, avec une amplitude croissante des plus mobiles aux moins
mobiles : le mammifère arboricole et l'oiseau de lisière passent d'un réseau connexe (Nancy, Kourou) à
une forte fragmentation à La Rochelle (onze et vingt-huit sous-réseaux), tandis que le reptile n'est
connexe sur aucun territoire, son nombre de sous-réseaux s'étageant de trois à quatorze. Surtout, le
classement des territoires n'est pas le même selon le profil : un territoire favorable au petit
mammifère terrestre ne l'est pas nécessairement pour les profils boisés ou thermophiles (Figure 19).
Ces écarts sont ici décrits ; leur interprétation au regard de la forme urbaine relève de la discussion
(§4.2).

## 3.4. Sensibilité des indicateurs au paramétrage de la calibration

Les coefficients de friction et les distances de dispersion sont fixés à partir de la littérature et
de la méthode du Cerema Dter Sud-Ouest (2025) plutôt que mesurés sur le terrain : ce sont les entrées
les moins contraintes de la chaîne, où se concentre l'essentiel de son incertitude (§1.5.1). Avant
d'accorder une portée à un résultat, il faut donc savoir s'il tient à un choix de paramétrage ou s'il
résiste à une variation plausible de ces valeurs. C'est l'objet de l'analyse de sensibilité : délimiter jusqu'où ses conclusions restent stables, non
confirmer que le modèle dit vrai.

Deux paramètres sont balayés un à la fois, sur une plage large : la distance de dispersion d₀, de 50 à 120 % de sa
valeur de référence, qui commande la portée ; et le contraste de friction, c'est-à-dire l'écart de coût
de déplacement entre l'habitat et la matrice, de 0 (matrice homogène, aucun écart) à 200 % (écart
doublé), qui module la résistance différenciée de la matrice. Cette approche, dite OAT (un facteur à la
fois), relève de l'analyse de sensibilité locale (Saltelli et al., 2008).
Plutôt que de fixer a priori une amplitude de perturbation, on trace la courbe de réponse de chaque
territoire et l'on y lit deux choses : la sensibilité au voisinage des valeurs de référence, et la marge, c'est-à-dire
la distance entre le paramétrage de référence et un changement de régime (gain ou perte de connexité). Deux indicateurs
sont suivis, la part d'habitat connecté (continue) et le nombre de sous-réseaux (compte gradué de la
fragmentation). La synthèse par territoire et par profil écologique figure en annexe E.

Sur les plages testées, le contraste de friction produit les variations les plus larges. À contraste nul, la matrice n'oppose plus
de résistance différenciée et la part connectée bondit vers un réseau quasi connexe pour tous les
profils (à Perpignan, de 64 à 96 % pour le petit mammifère terrestre, de 23 à 50 % pour le reptile),
puis décroît à mesure que le contraste se renforce. Cette amplitude, du même ordre ou supérieure à
celle de d₀, désigne l'écart de résistance entre classes d'occupation du sol, plus que le niveau absolu
des coûts, comme le principal levier sur la plage explorée (Bowman et al., 2020).

La distance de dispersion agit de façon plus graduée et monotone, et sa marge dépend du profil
écologique et du territoire. Le petit mammifère terrestre est robuste : son réseau ne se scinde qu'aux
plus faibles portées, en deçà d'environ 60 à 70 % de d₀ selon le territoire (il reste connexe sur toute
la plage testée à Nancy), de sorte qu'il faudrait une erreur importante sur sa portée pour changer le
diagnostic. Le reptile est à l'opposé : jamais connexe sur toute la plage, déjà au-delà du seuil au
paramétrage de référence, il ne se distingue que par son degré de fragmentation, qui s'étage fortement (à
Perpignan, de vingt-cinq sous-réseaux à d₀ réduit de moitié à quatorze au paramétrage de référence ; à La Rochelle,
jusqu'à près de cent aux plus faibles portées). Le mammifère arboricole et l'oiseau de lisière sont
intermédiaires, connexes au voisinage des valeurs de référence et fragmentés aux faibles portées.

Kourou fait exception sur l'axe de la dispersion : la part connectée du petit mammifère terrestre y
reste plate (69 à 70 % de 50 à 120 % de d₀), sa matrice forestière équatoriale étant si perméable que
la portée n'y change presque rien ; le contraste, lui, y agit comme ailleurs (97 % à contraste nul). La
sensibilité dépend donc du territoire : le même écart de paramètre est inerte à Kourou et sensible dans
les tissus fragmentés, ce qui est en soi un résultat (Figures 13 et 14).

Au total, l'analyse conforte l'usage comparatif de l'outil : l'ordre entre profils écologiques et entre
territoires, et le fait qu'un réseau soit ou non connexe, se maintiennent sur la plage testée, tandis
que les valeurs absolues se déplacent. Elle borne aussi ce qui peut en être conclu, comme le précisent
les deux réserves suivantes.

Trois réserves encadrent cette lecture. La perturbation ne fait varier qu'un paramètre à la fois : une
bascule par combinaison de la dispersion et du contraste n'est pas capturée, la marge étant mesurée le
long d'un seul axe. Les amplitudes se lisent en outre facteur par facteur et ne constituent pas une
répartition de variance : les deux plages de perturbation n'ont pas la même largeur, et aucun indice de
premier ordre ou total, au sens des méthodes fondées sur la variance (Sobol, 2001), n'a été estimé ; le
contraste demeure donc le paramètre le plus influent sur la plage explorée, sans que sa prééminence soit
chiffrée. Enfin, l'analyse teste la robustesse au choix des paramètres, non l'accord des sorties avec le
terrain, qui relève de la validation (§4.4). Une analyse de sensibilité globale, faisant varier les
facteurs simultanément par un plan de Morris ou des indices de Sobol, lèverait ces limites au prix d'un
nombre d'exécutions bien supérieur (Saltelli et al., 2008 ; Lamboni, 2009).

[FIGURE : Courbes de réponse à la distance de dispersion (50 à 120 % de la référence). Part d'habitat
connecté (en haut) et nombre de sous-réseaux (en bas), un panneau par territoire (colonnes), une
couleur par profil écologique ; ligne pointillée = référence.]

[FIGURE : Courbes de réponse au contraste de friction (0 à 200 %).]

## 3.5. Confrontation aux observations GBIF et à la méthode du Cerema

Deux confrontations externes ont été menées, dont la portée est discutée en section 4.4.

La première, aux occurrences GBIF, teste le côté habitat du modèle, c'est-à-dire si les espèces d'un
profil se trouvent là où le modèle place leur habitat, et non le flux le long des corridors. Les couches
modélisées ont été confrontées aux occurrences GBIF d'un groupe de quatre espèces par profil
écologique (liste en annexe B), sur les cinq territoires métropolitains. Les occurrences GBIF
reflétant autant la répartition des observateurs que celle des espèces (biais d'échantillonnage,
§1.5.3), deux précautions précèdent l'analyse. Les relevés sont d'abord filtrés : seules sont retenues
les observations de terrain dont l'incertitude de localisation annoncée est inférieure à 100 m et
postérieures à 2016. Ce seuil de 100 m est courant pour le nettoyage des occurrences (Zizka et al.,
2019) ; il correspond aussi à la taille d'une maille de noyau (1 ha, soit 100 m de côté), c'est-à-dire
à la finesse avec laquelle chaque occurrence peut être rattachée à une couche du modèle sans ambiguïté. La borne de 2016 conserve les relevés contemporains du millésime
d'occupation du sol utilisé et limite les décalages liés aux changements d'usage. Les relevés sont
ensuite sous-échantillonnés à une occurrence par cellule, ce qui efface les grappes d'observations
répétées au même endroit.
Chaque occurrence est ensuite affectée à la couche modélisée qui la contient (noyau, relais, corridor
ou matrice). Pour isoler la sélection réelle de l'effort d'observation, biais spatial, temporel et taxonomique bien
documenté des données d'occurrence (Boakes et al., 2010 ; El-Gabbas, 2026 ; Melis et al., 2025), un ratio de sélection (usage
rapporté à la disponibilité ; Johnson, 1980 ; Manly et al., 2002) compare la part des occurrences de
l'espèce dans une classe à celle d'un fond d'observation constitué de toutes les espèces de sa classe
taxonomique (mammifères, oiseaux ou reptiles) relevées sur le même territoire. Ce fond subit
exactement le même biais d'observation que l'espèce cible, si bien que le ratio se lit directement :
proche de un, la classe est fréquentée comme le prédit le seul effort d'observation ; nettement
supérieur à un, elle est sélectionnée ; inférieur à un, elle est évitée. Un intervalle de confiance à
95 % par bootstrap accompagne chaque ratio et tranche lorsqu'il exclut un. Sur les ratios agrégés (Figure 15),
les espèces d'habitat boisé sont sur-représentées dans les noyaux : l'oiseau de lisière y affiche un
ratio de 1,80 (intervalle 1,65 à 1,95) et un ratio de 0,69 dans la matrice, le mammifère arboricole un
ratio de 1,68 dans les noyaux et de 0,50 dans la matrice. Le petit mammifère terrestre présente un profil
différent : il évite les grands noyaux (0,39) et se trouve davantage dans les relais (1,92), les
corridors (1,74) et la matrice (1,45). Le reptile terrestre ne produit pas de signal d'ensemble
exploitable : son test global n'est pas significatif (p = 0,21, voir ci-dessous) et aucune sélection de
classe ne s'en dégage nettement, le très faible nombre d'occurrences hors de Toulouse limitant de toute
façon l'interprétation. Un test du khi-deux, qui compare les effectifs observés par
classe aux effectifs attendus sous l'hypothèse d'absence de sélection, confirme une sélection hautement
significative pour l'oiseau de lisière, le mammifère arboricole et le petit mammifère terrestre
(p < 0,001) et non significative pour le reptile (p = 0,21).

La couverture est toutefois très inégale selon le profil et le territoire : seul l'oiseau de lisière
atteint un effectif suffisant sur plusieurs villes, et les ratios agrégés restent dominés par Toulouse
(67 à 76 % des occurrences selon le profil), seule ville à réunir assez d'observations pour les quatre
profils. Le détail par territoire, effectifs compris, figure en annexe B ; les couples de moins de
trente occurrences y sont signalés comme non interprétables isolément. La répartition spatiale des
occurrences est cartographiée pour l'oiseau de lisière à Toulouse (Figure 16).

[FIGURE : Ratios de sélection des occurrences GBIF par profil et par classe (noyau, relais, corridor,
matrice), agrégés sur les cinq territoires tempérés. (d'après les données GBIF, 2026)]

[FIGURE : Occurrences GBIF de l'oiseau de lisière à Toulouse superposées aux noyaux, espaces relais
et corridors modélisés. (d'après les données GBIF, 2026)]

La seconde, la comparaison à la méthode du Cerema Dter Sud-Ouest (2025), porte sur La Rochelle, territoire commun aux deux
démarches : les noyaux et tracés de moindre coût produits ici ont été superposés à ceux du Cerema Dter Sud-Ouest (Figure 17). [À COMPLÉTER :
quantifier le recouvrement observé (part de tracés/noyaux concordants) plutôt que de le dire
qualitativement ; sinon décrire précisément les zones de coïncidence et de divergence.]

[FIGURE : Comparaison sur le secteur de Salles-sur-Mer, à La Rochelle (sous-trame herbacée) : méthode
proposée et carte du Cerema Dter Sud-Ouest sur le même secteur. (d'après Cerema Dter Sud-Ouest, 2025)]

## 3.6. Effet local d'un scénario de végétalisation à Toulouse

Au-delà du diagnostic de l'état existant, la chaîne sert aussi d'outil prospectif : elle estime l'effet
attendu d'un projet d'aménagement sur la connectivité, avant sa réalisation. C'est cette simulation
avant/après qui la rapproche d'un outil d'aide à la décision, en permettant de comparer des scénarios
plutôt que de seulement constater un état. Le principe est simple : le projet est intégré à
l'occupation du sol comme une modification locale, puis toute la chaîne est relancée sur l'état modifié
et ses sorties sont comparées à celles de l'état initial.

Ce mécanisme est illustré ici par une végétalisation de près de cinq hectares à Toulouse, le long des
allées Jean-Jaurès et des ramblas : le projet est ajouté à l'occupation du sol, puis l'état avant et
l'état après sont comparés à indicateurs identiques.

À l'échelle locale, la surface végétalisée devient un nouveau noyau de biodiversité que l'étape de
moindre coût rattache au réseau : pour le profil de petit mammifère terrestre illustré (Figure 18), le site
passe de un à sept liens de raccordement. À l'échelle du territoire, en revanche, les indicateurs agrégés (calculés sur l'ensemble de l'emprise)
sont quasiment inchangés : ils varient de moins de 0,1 % pour les quatre profils écologiques. La surface
connectée équivalente du petit mammifère terrestre passe par exemple de 7 674,2 à 7 674,6 hectares, et
le nombre de sous-réseaux reste identique avant et après pour les quatre profils.

[FIGURE : Scénario de végétalisation des ramblas des allées Jean-Jaurès à Toulouse, comparaison
avant/après sur le profil écologique de petit mammifère terrestre.]
