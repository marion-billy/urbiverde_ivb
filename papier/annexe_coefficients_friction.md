# Annexe A. Coefficients de friction par profil écologique

> Annexe méthodologique justifiant les coefficients de friction (résistance au déplacement)
> utilisés dans la modélisation des corridors écologiques. Les valeurs sont calibrées sur la
> méthode du Cerema (*Identification des continuités écologiques urbaines, Communauté
> d'Agglomération de La Rochelle*, juin 2025), adaptée à une occupation du sol issue de données
> ouvertes globales (ESA WorldCover 10 m et OpenStreetMap).

## 1. Principe

La perméabilité du paysage au déplacement de la faune est modélisée par une carte de friction :
chaque type d'occupation du sol reçoit un coefficient de résistance, propre à chaque profil écologique. Les corridors sont ensuite tracés comme des chemins de moindre coût sur cette
surface. Plus le coefficient est faible, plus le milieu est facile à traverser.

## 2. Échelle de friction

L'échelle, reprise du Cerema, s'étend de 1 à 100 et se décompose en grandes catégories :

| Coefficient | Signification |
|---|---|
| 1 | Milieu de vie (optimum écologique) |
| 2 - 3 | Milieu favorable |
| 4 - 5 | Déplacement fréquent (milieux de vie marginaux) |
| 6 - 7 | Limite d'aire de déplacement |
| 8 - 9 | Petits obstacles |
| 10 - 50 | Obstacles importants |
| 100 | Obstacle infranchissable |

Convention retenue : un milieu est considéré comme **habitat** d'un profil écologique lorsque son
coefficient est inférieur ou égal à 3 (milieu de vie ou favorable). Au-delà de 4, le milieu
relève du déplacement, non de l'habitat.

## 3. Profils écologiques et espèces de référence

Quatre profils écologiques sont définies, chacune nommée d'après une espèce de référence calibrée par le
Cerema, ubiquiste en France métropolitaine (donc présente sur l'ensemble des aires d'étude).

| Profil écologique | Espèce de référence | Distance de dispersion d0 (m) | Codes habitat |
|---|---|---:|---|
| ground_mammal | Hérisson d'Europe (*Erinaceus europaeus*) | 3000 | tree, shrub, grass |
| arboreal_mammal | Écureuil roux (*Sciurus vulgaris*) | 2000 | tree |
| forest_edge_bird | Fauvette à tête noire (*Sylvia atricapilla*) | 1500 | tree, shrub |
| ground_reptile | Lézard des murailles (*Podarcis muralis*) | 750 | grass, bare |

Deux espèces du tableau de friction du Cerema n'ont pas été retenues comme profils écologiques distincts :

- **Couleuvre verte et jaune** (seconde espèce du cortège mixte) : son syndrome fonctionnel
  (reptile rampant, faible dispersion) est déjà couvert par le lézard des murailles, et sa
  répartition méridionale ne couvre pas toutes les aires d'étude (absente du nord-est, Nancy).
- **Orthoptères** (seconde espèce du cortège herbacé) : après alignement, leur habitat se réduisait
  aux milieux ouverts (grass, bare), identique à celui du lézard, et leur comportement de
  fragmentation était redondant. Le Cerema lui-même fond lézard et orthoptères dans un unique
  cortège herbacé.

La distance d0 correspond à la distance de dispersion propre de l'espèce (synthèse bibliographique
des fiches espèces). Le coût maximal de déplacement d'un corridor fonctionnel vaut `d0 x 3` (coût en
friction x mètres), reprenant la formule du Cerema (distance de dispersion x coefficient favorable
moyen, fixé à 3).

Le **coefficient favorable moyen (3)** n'est pas la friction d'une classe précise : il représente la
friction moyenne attendue le long d'un corridor réaliste (mélange d'habitat à 1 et de matrice
favorable à 2-3), au sommet de la catégorie « favorable » de l'échelle. Il joue le rôle de **taux de
change distance vers coût** : parcourir d0 mètres en terrain favorable coûte `d0 x 3`. Un corridor
dont le coût dépasse `d0 x 3` a donc forcé l'animal à traverser du terrain pire que favorable sur une
longueur dépassant son budget de déplacement, et est jugé non fonctionnel.

## 4. Dérivation des coefficients

Les coefficients sont calibrés sur les valeurs par espèce du Cerema (annexe 5.4 du rapport cité).
L'occupation du sol mobilisée ici (WorldCover, 11 classes globales, complétées par les
infrastructures OpenStreetMap) est plus agrégée que celle du Cerema (une trentaine de classes
fines). Chaque classe utilisée regroupe donc plusieurs classes du Cerema : le coefficient retenu
est la **moyenne** des coefficients Cerema des classes correspondantes.

### Table d'agrégation

| Classe utilisée | Classes Cerema moyennées | Exclusions et justification |
|---|---|---|
| tree | Boisement de feuillus, boisement mixte, bois et arbres | Boisement artificiel (peupleraie) exclu, écarté par le Cerema lui-même pour faible naturalité |
| shrub | Formation arbustive | Classe unique |
| grass | Prairie permanente, prairie temporaire, surfaces herbacées | Pelouse sèche calcicole exclue (habitat de niche, non représentatif de la classe herbacée générale) |
| crop | Grandes cultures, cultures florales et légumières, potagers, vignes, vergers | Aucune |
| built | Zones bâties artificialisées (non dense) | Bâti dense exclu, déjà capté séparément par les empreintes de bâtiments OpenStreetMap |
| bare | Sols nus | Classe unique |
| path | Chemins agricoles | Classe unique |
| rail | Voies ferrées | Classe unique |
| wetland, mangrove | Surfaces en eau, cours d'eau, fossés et noues, canaux de marais | Bassins de rétention et canaux principaux exclus (valeur 100, obstacles majeurs non représentatifs d'un marais) |

Les infrastructures OpenStreetMap reçoivent directement la valeur Cerema correspondante :
empreintes de bâtiments (bâti dense, 100 ou infranchissable), autoroutes et 2x2 voies (routes très
fragmentantes, 100), routes secondaires (routes, 50).

### Codes OpenStreetMap ajoutés et ordre de priorité du burn

Les infrastructures OpenStreetMap sont rastérisées et brûlées par-dessus le WorldCover avec des codes
propres : 51 (bâtiments), 52 (autoroutes et grands axes), 53 (routes secondaires), 54 (chemins) et 55
(voies ferrées). En cas de superposition de deux couches sur un même pixel, la priorité, du moins
prioritaire au plus prioritaire, est :

> surfaces artificialisées gérées, brûlées comme bâti (50) < eau (80) < bâtiments (51) < autoroutes et
> grands axes (52) < routes secondaires (53) < voies ferrées (55) < chemins (54).

Les chemins (54) ne recouvrent en outre que les pixels qui ne sont pas de l'habitat du profil écologique, afin
de ne pas fragmenter artificiellement l'habitat par un sentier.

## 5. Écarts assumés par rapport au Cerema

Quatre écarts méthodologiques, justifiés par les données mobilisées et par la finalité d'aide à la
décision en milieu urbain :

1. **Obstacles infranchissables plutôt qu'échelle finie, pour le bâti et les grandes rivières.** Les
   empreintes de bâtiments sont traitées en obstacle infranchissable : un chemin de déplacement à
   travers un volume bâti n'a pas de réalité physique. Les surfaces en eau le sont également pour
   les profils écologiques strictement terrestres (hérisson, lézard) : la donnée OpenStreetMap ne capte que les
   cours d'eau larges (de l'ordre de 30 m), réellement infranchissables, et non les petits ruisseaux
   du Cerema. Les routes, en revanche, conservent une valeur finie (50 ou 100) : un corridor peut
   les franchir à coût élevé, ce qui permet de localiser les points de conflit (points noirs) où un
   aménagement serait pertinent.

2. **Bâti non valorisé comme habitat.** Le Cerema attribue au lézard un coefficient de 3 sur le
   bâti (les murs et cimetières lui sont favorables). Pour un outil destiné à orienter la
   dé-fragmentation urbaine, signaler le bâti comme favorable serait contre-productif. Le bâti reste
   donc un obstacle (coefficient 10). De même, l'écureuil garde un coefficient de 10 sur le bâti :
   la classe utilisée correspond à l'imperméable inter-bâtiment (sans canopée), peu favorable à une
   espèce arboricole.

3. **Retrait de l'arbustif de l'habitat du reptile.** Le coefficient moyen du Cerema pour la
   formation arbustive (4 pour le lézard) dépasse le seuil d'habitat (3). L'arbustif est donc traité
   comme milieu de déplacement, non comme habitat.

4. **Zones humides et mangroves inférées.** La sous-trame humide du Cerema a été traitée par
   dilatation-érosion, sans carte de friction ni espèce cible : aucun coefficient par espèce n'est
   disponible pour ces milieux. Leur friction est donc inférée par analogie avec les classes
   aquatiques (voir table d'agrégation). Ces milieux restent passables (valeur finie), contrairement
   aux grandes rivières mises en obstacle infranchissable.

## 6. Table finale des coefficients de friction

Valeurs par profil écologique et par classe (infranchissable = coût infini). Les codes habitat de chaque profil écologique
sont en gras.

| Classe | ground_mammal | arboreal_mammal | forest_edge_bird | ground_reptile |
|---|--:|--:|--:|--:|
| tree | **1** | **1** | **2** | 4 |
| shrub | **1** | 6 | **1** | 4 |
| grass | **2** | 4 | 7 | **1** |
| crop | 6 | 7 | 6 | 5 |
| built (matrice inter-bâtiment) | 10 | 10 | 10 | 10 |
| bare | 10 | 10 | 10 | **3** |
| water (grandes rivières) | infranchissable | 9 | 7 | infranchissable |
| wetland | 8 | 8 | 6 | 8 |
| mangrove | 8 | 8 | 6 | 8 |
| bâtiments (OSM) | infranchissable | infranchissable | 100 | infranchissable |
| autoroute / 2x2 (OSM) | 100 | 100 | 100 | 100 |
| route secondaire (OSM) | 50 | 50 | 50 | 50 |
| chemin (OSM) | 5 | 8 | 8 | 3 |
| voie ferrée (OSM) | 10 | 9 | 7 | 3 |

Le lézard conserve un optimum (grass = 1) : sa prairie ouverte est son milieu de vie, le sol nu un
milieu favorable (3). L'arbustif et la forêt fermée (4) relèvent du déplacement.

## 7. Limites

- Les coefficients des routes sont identiques pour toutes les espèces : la fragmentation routière
  est dominée par les propriétés de la route (largeur, trafic), peu de données existent par espèce.
  Cette uniformité est discutable pour une espèce volante.
- Le déplacement à l'intérieur d'un patch d'habitat est considéré comme libre, ce qui peut
  surestimer la connectivité des grands patchs.
- Les coefficients ne sont pas calibrés sur des données locales d'occurrence ou de mortalité : ils
  constituent des valeurs d'expert, reprises du Cerema.
