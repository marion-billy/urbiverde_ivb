# 5. Conclusion et perspectives

> Brouillon. Corps impersonnel. [FIGURE : …] = illustration ; [À COMPLÉTER] = à préciser.

## 5.1. Conclusion

Ce travail construit et teste une preuve de concept : une chaîne reproductible qui cartographie la
connectivité écologique urbaine à partir de la seule observation de la Terre et de données ouvertes,
en réponse au verrou identifié en introduction, celui d'outils de connectivité puissants mais experts
et peu transposables. Les cinq objectifs fixés en ont structuré la construction.

La chaîne conduit de bout en bout des données ouvertes, WorldCover et OpenStreetMap, jusqu'aux
composantes des continuités écologiques potentielles : noyaux de biodiversité, espaces relais,
liens fonctionnels, points de rupture et surfaces de dispersion. Elle a produit vingt-quatre jeux
de sorties normalisés, six territoires par quatre profils écologiques, tous directement exploitables en
système d'information géographique comme dans le tableau de bord.

Le raisonnement s'appuie sur des profils écologiques, dont les paramètres de friction et de dispersion proviennent de
l'étude du Cerema et des travaux qu'elle agrège, puis sont réinterprétés au niveau du syndrome de déplacement, plutôt que par une espèce
focale unique. Elle restitue ainsi quatre réseaux distincts pour un même territoire, là où une trame
verte indifférenciée laisserait invisibles des besoins de continuité propres à chaque capacité de
déplacement : la part d'habitat connecté s'échelonne de moins de 10 % pour le reptile à Toulouse à plus
de 80 % pour le petit mammifère terrestre à La Roche-sur-Yon.

Implémentée intégralement en Python, sans recours aux logiciels spécialisés existants, elle est
automatisable et déterministe, sans composante aléatoire : une même commande régénère l'ensemble des résultats d'un territoire, et sa reproduction à l'identique
ne requiert que les données publiques et un fichier de configuration.

Ses sorties sont restituées dans un tableau de bord interactif destiné à des aménageurs non
spécialistes, qui permet d'explorer le réseau d'un territoire, d'en superposer les couches et de
comparer l'effet de scénarios d'aménagement.

La chaîne a enfin été exécutée, sans aucun réglage local, sur six territoires aux contextes bioclimatiques
contrastés, de la façade atlantique à la Guyane équatoriale, premier test de sa transposabilité.

La contribution est ainsi opérationnelle plus que théorique : elle réside dans l'assemblage de briques établies en une chaîne
unique et accessible, prolongée jusqu'à une sortie directement exploitable et au test de scénarios. Ces résultats relèvent d'un modèle de connectivité
potentielle : ils signalent où la connectivité est vraisemblablement en jeu et permettent de simuler plusieurs
scénarios d'aménagement et de les comparer. Ils ont la portée d'un pré-diagnostic, rapide et peu coûteux,
à confirmer par des études de terrain avant toute décision.

## 5.2. Perspectives

Le principal prolongement porte sur la validation. Le faisceau de vérifications présenté au
chapitre 4 (sensibilité, comparaison à la méthode du Cerema Dter Sud-Ouest sur La Rochelle, occurrences GBIF, reproductibilité) gagnerait à être
complété par un protocole de terrain. Un plan d'échantillonnage stratifié opposerait des secteurs
témoins, éloignés de toute coupure, à des secteurs proches d'une infrastructure fragmentante, le
nombre de relevés par strate étant dimensionné à l'avance, par un calcul de puissance statistique, de
manière à pouvoir détecter un écart d'occupation donné. Les corridors modélisés seraient échantillonnés en priorité, afin de
tester s'ils sont effectivement empruntés. Plusieurs méthodes se combineraient selon le profil
écologique : relevés d'occurrence et pièges photographiques pour l'usage des passages, radio-pistage
ou génétique du paysage (Spear et al., 2010) pour le mouvement lui-même. Une telle validation reste
coûteuse et se heurte à la part non déterministe du déplacement animal, mais c'est elle qui ferait
passer l'outil d'une connectivité potentielle à une connectivité vérifiée.

L'enrichissement des données d'entrée ouvrirait ensuite de nouveaux usages, chacun comblant une limite
identifiée de la chaîne actuelle.

L'extension à la trame bleue, avec l'introduction d'un profil écologique amphibie, comblerait la
principale lacune de périmètre. Le réseau hydrographique (cours d'eau, plans d'eau, zones humides)
n'est aujourd'hui pas traité comme une sous-trame à part entière, alors que les amphibiens comptent
parmi les groupes les plus sensibles à la fragmentation (Cushman, 2006 ; Hamer & McDonnell, 2008) et à
la mortalité routière (Hels & Buchwald, 2001), et dépendent de continuités terre-eau qui leur sont propres.

Une donnée sur la nature du sol sous le couvert végétal lèverait une ambiguïté de l'occupation du sol
optique : vue du ciel, une canopée reçoit la même classe qu'elle surplombe un sol végétalisé ou une
surface imperméable, alors que la valeur écologique des deux diffère fortement, un arbre isolé
au-dessus d'un trottoir bitumé n'étant pas un habitat. Une couche d'imperméabilisation des sols
distinguerait ces deux cas ; un modèle de hauteur de végétation, de type LiDAR, y ajouterait la
séparation entre végétation basse et couvert arboré.

L'intensité du trafic routier permettrait de pondérer l'effet fragmentant des voies au-delà de leur
seule catégorie : à classe égale, une route très circulée forme une barrière plus forte qu'une route
peu fréquentée.

Enfin, l'adossement des franchissements à des ouvrages réels (passages à faune, buses et ponts
recensés) ferait passer les tracés de moindre coût là où un franchissement est physiquement possible,
plutôt qu'au seul point de moindre coût théorique. La base nationale SIPAF (Système d'information sur
les passages à faune) a été envisagée à cette fin, mais elle demeure incomplète et ne recense aucun
ouvrage dans les emprises étudiées.

Une dimension sensorielle reste enfin hors de ce périmètre purement structurel. Le déplacement de la
faune est aussi entravé par des barrières absentes d'une carte d'occupation du sol : la pollution
lumineuse, qui perturbe les espèces nocturnes (trame noire), et la pollution sonore, qui repousse les
espèces sensibles au bruit (trame blanche). Le groupe de travail du Cerema sur les différents types de
trames traite explicitement ces pressions dans le cadre d'UrbiVerde ; la chaîne pourrait les intégrer comme couches de résistance
supplémentaires, la pollution lumineuse étant par exemple cartographiable par la radiance nocturne du
capteur VIIRS (Visible Infrared Imaging Radiometer Suite), la pollution sonore par les cartes de bruit
stratégiques ou l'intensité du trafic.

La nature reproductible de la chaîne la destine enfin à un déploiement à plus grande échelle. Testée
sur six territoires, elle peut être appliquée à beaucoup d'autres pour un coût marginal quasi nul, et s'insérer
dans les processus de planification des gestionnaires d'infrastructures vertes, au sein de la
plateforme UrbiVerde à laquelle elle a vocation à fournir le service dédié aux continuités écologiques.
