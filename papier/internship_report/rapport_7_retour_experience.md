# 6. Retour d'expérience

> Brouillon. Partie rédigée à la première personne (retour d'expérience du stage), à la différence du
> corps scientifique. [À COMPLÉTER] / [À ADAPTER] = éléments propres au déroulé que moi seule peux
> renseigner ; [À CONFIRMER] = à valider ; [FIGURE : …] = illustration.

## 6.1. Conduite de projet

En début de stage, une phase d'appropriation du domaine a précédé la conception : j'ai suivi
le MOOC « Trame verte et bleue » de l'Office français de la biodiversité pour m'approprier le cadre
réglementaire et les enjeux de continuité écologique avant d'entrer dans la partie technique. En cours
de stage, j'ai également assisté au webinaire « MitiConnect : retours d'expérience » de l'OFB, le
5 juin 2026, consacré aux usages de cet outil de modélisation de la trame verte, proche de la
démarche développée ici.

Les pistes envisagées en début de stage décrivaient un outil au périmètre étendu :
une occupation du sol produite par apprentissage profond sur séries temporelles Sentinel-2 et plusieurs
capteurs complémentaires, des profils écologiques, une modélisation combinant graphe, moindre coût
et théorie des circuits, des cartes de consensus entre profils écologiques, un ensemble d'indicateurs agrégés par
zone administrative, une suggestion d'élargissement des réservoirs et l'estimation de co-bénéfices
climatiques. Compte tenu du temps d'un stage et de l'exigence de reproductibilité sur des biomes
contrastés, ce périmètre a été délibérément resserré vers une première version fonctionnelle, cohérente
et transférable.

Ce recentrage est un choix d'ingénierie : livrer un socle qui fonctionne de bout en bout, à
limites connues, plutôt qu'un ensemble plus large mais inabouti. Les éléments mis de côté
(classification d'occupation du sol sur mesure, théorie des circuits, métriques d'importance,
co-bénéfices, scores par zone) sont repris comme perspectives au chapitre 5 ; les choix internes à ce périmètre sont détaillés à la section suivante.

Une fois obtenus les résultats sur les quatre villes pilotes, Toulouse a été ajoutée comme cas de
contrôle. Je connais bien ce territoire, ce qui m'a permis de vérifier visuellement que les composantes
produites, infrastructures fragmentantes, passages de biodiversité et habitats, y correspondaient à la
réalité de terrain. La chaîne s'étant révélée simple à étendre à un nouveau territoire, La Rochelle a
ensuite été ajoutée lorsque la découverte de la méthode du Cerema, auprès de Vanessa Rauel, en a fait
un territoire de comparaison.

Le rapprochement du planning prévisionnel et du planning réalisé (Figure 20) fait apparaître un
décalage entre le prévu et le réalisé. Les simplifications de méthode ont allégé le début du
stage : renoncer à une classification d'occupation du sol sur mesure au profit de WorldCover complété
par OpenStreetMap a raccourci la phase technique et servi l'objectif de reproductibilité. Le temps
ainsi dégagé a été absorbé par la fiabilisation et l'optimisation de la chaîne, plus longues que
prévu : la stabilisation du pipeline, de la désynchronisation des identifiants de nœuds au graphe
construit sur des géométries invalides, en passant par les points de rupture et le lissage des nœuds
ramené de plusieurs heures à quelques secondes, s'est étendue sur le mois de juin, au-delà du jalon de
finalisation initialement fixé à la mi-juin. L'analyse de sensibilité, modeste au prévisionnel, est
devenue une campagne de calcul à part entière en juillet. La rédaction des résultats et de la
discussion, prévue au printemps, s'est en conséquence concentrée sur la fin du stage, une fois les
sorties figées, la production des figures et des cartes intervenant en dernier.

[FIGURE : Diagramme de Gantt comparant le planning prévisionnel et le planning réalisé.]

Le suivi s'est appuyé sur un point hebdomadaire avec mon tuteur, le lundi matin, consacré à
l'avancement, aux réorientations et au guidage du travail. À l'échelle de l'entreprise, une réunion
mensuelle réunissait les trois pôles (commercial ; ingénierie recherche et projets, mon pôle ;
ingénierie visualisation et infrastructure), où je présentais régulièrement l'avancée de mon sujet.
L'équipe R&D tenait aussi une réunion hebdomadaire, le mercredi matin, dédiée à la veille, au
partage de données, de méthodes et d'articles, et à la présentation par l'un de ses membres d'un sujet
exploré, selon un format structuré (contexte, acquis, pratiques actuelles, perspectives, positionnement
de l'équipe) suivi d'un court quiz ; j'y ai présenté la connectivité écologique urbaine.

Le stage s'est aussi inséré dans le consortium du projet UrbiVerde, aux côtés de CS Group et
du Cerema. J'ai participé à des réunions techniques réunissant ces partenaires, consacrées à un état
des lieux des connaissances et des indicateurs déjà développés par chacun et à leur articulation : il
s'agissait de situer l'indicateur de connectivité parmi les briques existantes de la future plateforme
et d'éviter les redondances. J'ai également pris part à un groupe de travail sur les trames animé par
des experts du Cerema, qui a nourri l'alignement du vocabulaire et de la méthode sur le cadre de la
Trame verte et bleue (chapitre 1). En parallèle, le Cerema a conduit des ateliers avec les villes
pilotes pour recueillir leurs besoins et leurs attentes vis-à-vis de la plateforme et dresser l'état de
ce qu'elles utilisent déjà : Nancy et La Roche-sur-Yon à distance, Perpignan sur site au Cerema de
Toulouse.

Ces retours ont directement infléchi la conception. Le tableau de bord a été simplifié pour rester
lisible par des utilisateurs qui ne sont pas écologues : une entrée par territoire et par profil
écologique, un vocabulaire accessible et un affichage épuré des couches. Les gestionnaires se sont
surtout montrés intéressés par la simulation d'aménagements, pour en chiffrer l'effet sur la
connectivité et arbitrer entre projets, et par la sensibilisation aux enjeux qu'elle permet, davantage
que par le détail méthodologique. Ce constat a orienté la restitution vers l'usage prospectif de
l'outil (§3.6, §4.3) plutôt que vers la seule cartographie de l'état existant.

## 6.2. Choix de méthode : essais et alignement

Les choix de méthode se sont arrêtés progressivement en cours de stage, chacun consigné dans le journal de décisions (le decision_log, registre daté où chaque choix, incident ou test est reporté). L'alignement méthodologique avec le Cerema, conduit à partir de son rapport et lors de
discussions avec ses chercheurs (J.-F. Bretaud, V. Rauel, D. Crozier), y a joué un rôle déterminant.
Les choix eux-mêmes et leurs
justifications techniques sont exposés au chapitre 2 ; je retrace ici la manière dont ils se sont
imposés, plutôt que de les ré-argumenter.

Le principe de différenciation a été fixé en premier : partie d'une table de résistance unique, j'y
ai renoncé au profit de profils écologiques, seuls porteurs d'une information fonctionnelle plutôt que
d'une simple mesure de structure. Restait ensuite à choisir comment différencier : les sous-trames du Cerema
supposant une occupation du sol plus fine que WorldCover, j'ai défini les profils par syndrome de
déplacement ; et l'occupation du sol a été prise toute faite plutôt que produite sur mesure (chapitre 2).
Le périmètre s'est enfin réduit de cinq à quatre profils au fil de l'alignement des frictions avec
le Cerema (détaillé au chapitre 2).

Deux simplifications ont été assumées faute de temps. La qualité des noyaux, d'abord pensée
multicritère, a été ramenée à un critère morphologique, ce que je reprends comme limite au chapitre 4.
Les métriques d'importance par flux (dPC, intermédiarité), qui hiérarchisent les liens selon le
flux qu'ils portent et leur position dans le réseau, ont été désactivées : présenter un lien comme
moins important qu'un autre, sur la foi d'un classement non validé, pourrait orienter à tort des
décisions d'aménagement lourdes ; la restitution vise donc à montrer où agir plutôt qu'à hiérarchiser
les liens, mais leur implémentation reste conservée et réactivable.

## 6.3. Débogage et fiabilisation

Une part substantielle du travail a porté sur le débogage et la fiabilisation de la chaîne, en
particulier sur la construction du graphe. Plusieurs liens apparaissaient à tort coupés ou en échec
pour des raisons de traitement, et non écologiques : un index de nœuds désynchronisé par l'étape de
lissage, ou un chemin de moindre coût réduit à un seul pixel. Le lissage des tracés ne joue qu'un rôle
d'affichage, mais un défaut à cette étape suffisait à fausser le diagnostic de fonctionnalité.

Au-delà de ces anomalies de traitement, j'ai cherché à savoir jusqu'où la chaîne reste robuste et où elle atteint ses limites.
J'ai traité des cas limites, comme une tache d'habitat de très grande taille qui faisait diverger
l'étape de lissage des géométries et a nécessité un garde-fou, et j'ai contrôlé la robustesse de la
chaîne sur des emprises à faible couverture OpenStreetMap et sur de grandes étendues.

Ces anomalies ont été repérées en comparant systématiquement les sorties aux cartes attendues, en
particulier sur Toulouse dont je connais le terrain, puis résolues en combinant plusieurs ressources :
l'agent de programmation pour explorer les pistes et réécrire le code, les échanges avec le tuteur pour
trancher les cas ambigus, et la documentation des bibliothèques. Chaque correctif a été validé en
confrontant les sorties avant et après correction.

## 6.4. Performance et passage à l'échelle

Le passage à l'échelle des grandes villes a constitué un enjeu technique en soi : le graphe de
Toulouse compte environ 9 400 nœuds (taches d'habitat et espaces relais), et le calcul de l'indice de
connectivité sur toutes leurs paires, de coût quadratique, devient trop lourd pour une implémentation
directe. Les étapes les plus coûteuses en calcul ont été identifiées puis optimisées en
remplaçant les opérations en cause, comme la comparaison de toutes les paires de nœuds ou de chaque
corridor à la fusion de tous les habitats, par des calculs vectorisés ou accélérés par un index
spatial.

Le calcul de l'indice de connectivité, d'abord, passait par une double boucle Python sur toutes les
paires de nœuds ; réécrit avec un plus court chemin matriciel (scipy) et une somme vectorisée (numpy),
il gagne un facteur d'environ 29 sur Perpignan (de 28,5 s à 0,98 s) et davantage sur Toulouse (de plus
de deux heures à une trentaine de secondes), pour un résultat validé identique à l'original. Le
découpage en segments de corridor, ensuite, dominait le temps de calcul sur Toulouse (environ
77 minutes, concentrées dans deux opérations portant sur la fusion de toutes les taches d'habitat en une seule géométrie, longue à intersecter) ; en ne
traitant chaque corridor que contre les habitats qu'il intersecte réellement et en préparant la
géométrie de test une seule fois, il descend à quelques minutes, pour des sorties géométriquement
identiques. Le lissage des nœuds, enfin, est passé d'une douzaine d'heures à une dizaine de secondes
en remplaçant un appel par nœud par un unique appel groupé (Tableau 4).

[TABLEAU : Optimisations des étapes coûteuses (temps avant/après, sur le territoire concerné).]

| Étape optimisée | Avant | Après | Levier |
|---|--:|--:|---|
| Indice de connectivité (PC), Toulouse | plus de 2 h | environ 30 s | plus court chemin matriciel (scipy) + somme vectorisée (numpy) |
| Indice de connectivité (PC), Perpignan | 28,5 s | 0,98 s | idem (facteur d'environ 29) |
| Découpage en segments de corridor, Toulouse | environ 77 min | quelques minutes | intersection ciblée + géométrie de test préparée une seule fois |
| Lissage des nœuds | une douzaine d'heures | une dizaine de secondes | appel groupé unique au lieu d'un appel par nœud |

Dans les trois cas, les sorties après optimisation ont été validées identiques (indice) ou
géométriquement identiques (segments) à celles d'avant.

Ces gains s'appuient sur des bibliothèques générales matures (scikit-image, scipy, geopandas,
networkx). Le coût par profil écologique reste ensuite dominé par deux étapes intrinsèquement exigeantes, la
construction du graphe et le tracé des moindres coûts.

Le re-run complet donne l'ordre de grandeur du coût par territoire, des plus petites emprises aux plus
grandes :

| Territoire | Temps total (4 profils écologiques) |
|---|---|
| Kourou | 8 min |
| Perpignan | 17 min |
| Nancy | 23 min |
| La Rochelle | 35 min |
| La Roche-sur-Yon | 116 min |
| Toulouse | 156 min |

Le coût se concentre sur les grandes emprises et sur deux étapes : pour le profil écologique le plus lourd
(Toulouse, petit mammifère terrestre, 86 minutes), le tracé des moindres coûts (environ 50 minutes) et la
construction du graphe de Gabriel (environ 26 minutes) représentent à eux seuls près de neuf dixièmes
du temps, toutes les autres étapes (segmentation, indice de connectivité, dispersion, segments)
restant de l'ordre de quelques minutes au plus.

L'optimisation m'a appris à profiler avant d'optimiser, le goulot
d'étranglement n'étant pas toujours là où on l'imagine, et à privilégier des leviers structurels
(vectorisation, index spatial, appel groupé unique) plutôt que des micro-optimisations au jugé.

## 6.5. Environnement de travail et assistance par IA

Le développement a été mené dans l'éditeur VSCode connecté à une machine virtuelle distante hébergée
chez OVH (350 Go de mémoire vive, 24 cœurs, GPU Nvidia H100), dimensionnée pour traiter de grandes
emprises. J'ai également conduit l'alignement méthodologique avec le Cerema jusqu'à la mise en place
d'une comparaison des deux méthodes sur La Rochelle (§3.5, §4.4). Cette collaboration a évolué au cours du
stage : le projet a démarré en commun, mais l'indicateur de connectivité a ensuite avancé de mon côté,
les contraintes de temps différant, un stage de six mois m'ayant conduite à prendre seule plusieurs
décisions méthodologiques. Mon travail est transmis au Cerema, qui s'en servira pour construire une
version consolidée destinée à la plateforme, appuyée le cas échéant sur des données françaises et sur
le produit Green Urban Sat pour l'occupation du sol, dont la couche différerait alors de celle retenue
ici ; une réunion en septembre doit permettre de converger sur une méthode commune. Le
travail s'est également inscrit dans la vie de l'équipe R&D, dont les réunions régulières portaient sur
la veille technique, les difficultés rencontrées et la présentation aux autres membres des sujets en
cours, appuyée sur des supports et des quiz.

Le code a été produit avec l'assistance d'un agent de programmation (Claude Code), encadré par une
convention de travail écrite interne à l'équipe R&D de Murmuration. Cette convention fonde la fiabilité de la
démarche, et mérite d'être décrite pour un lecteur non familier de ces outils. L'assistant y est
sceptique par défaut : il lui est demandé de chercher d'abord le point faible d'une idée avant de la
valider, et les formules de complaisance lui sont proscrites. Tout
énoncé qu'il ne peut pas vérifier doit être signalé comme tel, et chaque affirmation porte un marqueur
de confiance. La règle centrale est que sa production n'est jamais auto-validante : l'ingénieur la
relit, la teste, la valide et la signe ; le recours à une IA ne dégage en rien de la responsabilité des erreurs d'un livrable. Le
code n'est écrit que sur demande explicite ; chaque décision, incident ou test est consigné dans un
journal daté ; et aucun résultat n'est déclaré terminé sans passer une série de contrôles
systématiques (complétude des sorties, projection et bornes géographiques, plausibilité physique des
valeurs). Le temps de développement s'est ainsi déplacé de l'écriture du code vers sa relecture et son
contrôle, pour un code souvent mieux optimisé, la responsabilité du résultat restant entière à
l'ingénieur.

## 6.6. Organisation, reproductibilité et passation

Le travail a été conduit de façon itérative et traçable : une convention de projet, un nettoyage non
destructif conservant les essais, le passage à des formats standard (.geojson, .csv) et la tenue
continue du journal de décisions. Le fichier de configuration des profils écologiques, qui isole les paramètres
métier du code, est un choix de conception délibéré : il permet de modifier un profil sans
intervenir sur le reste de la chaîne.

L'objectif est que l'équipe puisse relancer la chaîne sans moi. La passation repose sur trois éléments
laissés à l'équipe : le code, versionné dans un dépôt Git ; les paramètres métier, isolés dans le
fichier de configuration des profils écologiques et modifiables sans toucher à la chaîne ; et la
documentation de suivi (journal de décisions, vue d'ensemble des notebooks, structure et arborescence
des données). Deux compléments renforceraient la reprise et restent à produire : un fichier README
d'entrée décrivant l'installation et le lancement de bout en bout, et le dossier d'industrialisation
prévu par la convention de l'équipe (instantané du code, notebook de lancement, tables des entrées et
des transformations), qui rassemblerait en un seul point ce qui est nécessaire au passage en
production. [À CONFIRMER : emplacement du dépôt et documentation effectivement laissée à la fin du
stage.] Ces deux compléments seront produits lors de l'industrialisation de la chaîne dans UrbiVerde,
que l'équipe poursuit.

Ces choix inscrivent la chaîne dans les principes FAIR de gestion des données de recherche (Wilkinson
et al., 2016) : ses sorties se veulent *trouvables* (arborescence normalisée, nommage systématique,
inventaire des sources en annexe A), *accessibles* (données d'entrée entièrement ouvertes, code
versionné), *interopérables* (formats standard .geojson, .tif et .csv, projection déclarée, nomenclature
d'occupation du sol explicite) et *réutilisables* (paramètres métier isolés et documentés, provenance
tracée, journal de décisions). Deux dettes limitent toutefois encore la reprise et restent à lever pour
l'industrialisation : la chaîne importe certains modules par des chemins relatifs vers d'autres espaces
de travail, ce qui la lie à une arborescence précise et l'empêche de tourner telle quelle ailleurs (à
corriger en empaquetant proprement ces dépendances) ; et elle dépend d'Earth Engine (authentification,
quotas, disponibilité de l'API), dépendance externe à déclarer et à encapsuler.

## 6.7. Apports personnels

Sur le plan technique, ce stage m'a permis de consolider la programmation géospatiale en Python
(xarray et rioxarray pour le raster, geopandas et shapely pour le vecteur, networkx pour les graphes,
scikit-image pour la morphologie mathématique) dans un cas pratique suivi de bout en bout : disposer
d'un fil rouge, d'un cas d'étude unique, aide à en comprendre le détail bien plus qu'un exercice isolé.
La théorie des graphes appliquée à l'écologie du paysage était nouvelle pour moi : l'écologie m'était
familière depuis ma licence, mais je ne l'avais jamais abordée avec une modélisation aussi poussée, et
la question de savoir comment traduire ces concepts en calcul m'a particulièrement intéressée. La
chaîne d'observation de la Terre (Google Earth Engine, OpenStreetMap), entrevue pendant le master et le
projet collectif d'atelier géomatique, a été mise en pratique à plus grande échelle. Enfin,
l'optimisation et le passage à l'échelle (profilage, vectorisation, index spatial) étaient nouveaux et
constituent un acquis transférable.

Au-delà de la technique, travailler dans une entreprise privée était nouveau pour moi, qui avais
jusque-là évolué en laboratoire de recherche. L'attention portée à l'utilité et au rendement s'est
révélée stimulante : un travail orienté vers un usage concret avance plus vite et se décide plus
facilement, l'objectif final aidant à trancher les choix intermédiaires et à hiérarchiser l'effort.

La principale compétence que j'en retire est la traduction d'un modèle écologique en une chaîne
reproductible, puis en couches directement actionnables par des non-spécialistes : faire passer un
raisonnement d'écologue à un outil que d'autres peuvent exécuter, comprendre et mobiliser pour décider.

Le travail en consortium et le dialogue avec des utilisateurs non spécialistes constituent une
compétence à part entière. J'ai constaté que les détails techniques, sur lesquels portait pourtant
l'essentiel de mon travail, n'intéressaient qu'une faible part des interlocuteurs, ce qui oblige à
prendre du recul et à traduire son travail dans les termes de l'usage. Gérer un périmètre mouvant m'a
appris l'importance de points réguliers pour resserrer et prioriser : le périmètre n'est jamais acquis,
il se réajuste en continu. La rigueur et la traçabilité (journal de décisions, convention de travail,
contrôles automatisés des sorties) sont devenues une pratique naturelle, d'autant qu'elles sont
courantes dans l'équipe.

Avec du recul, ce que je referais différemment est d'entrer plus tôt en contact avec les experts
extérieurs et de moins hésiter à solliciter leur expertise, qu'il s'agisse du Cerema ou d'autres
bureaux d'études : ces échanges, quand ils ont eu lieu, ont été parmi les plus utiles. La limite que
j'assume le plus lucidement, au-delà des limites techniques du chapitre 4, est d'avoir avancé seule sur
l'indicateur, sous la contrainte de six mois, sans la co-construction plus poussée avec le Cerema ni la
validation de terrain qu'un temps plus long auraient permises.

Enfin, ce stage a précisé mon projet professionnel. Je poursuis dans l'équipe sur des sujets
d'environnement appuyés sur l'observation de la Terre. Il m'a permis d'associer une dimension de
recherche, que j'avais appréciée lors d'une précédente expérience en océanographie, à un projet concret
dont les résultats sont destinés à être réellement utilisés : là où la recherche peut donner le
sentiment de s'adresser surtout à d'autres chercheurs, je trouve ici un travail taillé pour des
utilisateurs finaux. Il relie aussi l'écologie et l'environnement aux compétences techniques de la géomatique et de la
télédétection, dans la continuité de mon parcours.
