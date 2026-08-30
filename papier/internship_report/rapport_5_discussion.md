# 4. Discussion

> Brouillon. Corps impersonnel. Les résultats chiffrés sont au chapitre 3 ; ce chapitre les interprète.
> [À COMPLÉTER : …] = proposition rédigée à valider ou compléter ; [réf à compléter] = référence à
> retrouver. Le retour sur les difficultés techniques est renvoyé au chapitre 6.

Ce chapitre interprète les résultats du chapitre 3 : ce que révèle une connectivité propre à chaque
profil écologique (4.1), ce que la forme urbaine explique des contrastes entre territoires (4.2), ce
que le scénario dit pour l'aménagement (4.3), la robustesse et la validité des sorties (4.4), l'apport
opérationnel de l'outil (4.5), enfin ses limites et sa portée (4.6).

En bref, le chapitre 3 fait apparaître une connectivité fortement dépendante du profil écologique (part
d'habitat connecté médiane d'environ 67 % pour le petit mammifère terrestre, 23 % pour le reptile), des
contrastes marqués entre territoires selon la forme urbaine, un effet d'aménagement sensible localement
mais négligeable à l'échelle du territoire, et des sorties qui résistent en relatif aux variations de
calibration tout en restant confortées, côté habitat, par les occurrences GBIF pour les profils boisés.
Les sections qui suivent en tirent les implications.

## 4.1. Une connectivité propre à chaque profil écologique

Modéliser la connectivité par profil écologique est un choix de conception, mais les résultats en
confirment la portée : la connectivité dépend du profil écologique retenu et diffère
nettement de l'un à l'autre. Restaurer la connectivité pour le petit mammifère terrestre, qui
dispose d'une large capacité de déplacement mais pour qui les cours d'eau font obstacle, n'a pas le
même sens que pour le reptile, dont l'habitat thermophile est dispersé et qui se déplace peu. En
restituant quatre réseaux distincts pour un même territoire, l'outil explicite cette multiplicité et
conduit à préciser pour quel profil écologique la connectivité est évaluée, là où la planification
française différencie surtout par grandes strates d'habitat (sous-trames boisée, ouverte, humide ;
Sordello, 2017), et non par capacité de déplacement des espèces. Ce constat conforte l'approche multi-espèces. Aucune espèce ne résume
les besoins d'une communauté (Roberge & Angelstam, 2004), et aucune ne sert de « parapluie de
connectivité » universel : même les espèces les plus souvent retenues ne conviennent que dans environ
60 % des régions (Dutta et al., 2023). Un jeu d'espèces aux traits contrastés vaut donc mieux
qu'un choix unique (Meurant et al., 2018), même si empiler des réseaux mono-profils laisse de côté les
interactions inter-espèces (Wood et al., 2022).

L'ordre observé entre profils (§3.2) suit leurs traits écologiques : la chaîne restitue des différences
attendues, ce qui en vérifie la cohérence interne sans valoir validation. Le meilleur classement du petit mammifère
terrestre tient autant à l'étendue de son habitat qu'à sa large distance de dispersion, tandis que la
fragmentation de l'oiseau de lisière, pourtant volant, s'explique par la rareté et le morcellement de
l'habitat boisé plus que par sa capacité de déplacement. Ce résultat rejoint les
observations, en contextes forestiers et agricoles, que les oiseaux forestiers hésitent à franchir les
trouées ouvertes au-delà de quelques dizaines de mètres (Bélisle et al., 2001 ; Robertson & Radford,
2009 ; Tremblay & St. Clair, 2011 ; Grafius et al., 2017), la mobilité ne garantissant pas à elle seule
la connectivité fonctionnelle des espèces volantes ; ces seuils restent toutefois dépendants de
l'espèce et du contexte et ne se transposent pas mécaniquement au tissu urbain. Le rôle facilitateur des
arbres épars comme relais (Robertson & Radford, 2009) conforte aussi l'importance des éléments
relais dans la chaîne. Ce rôle déterminant de la disponibilité et de
l'agencement de l'habitat rejoint le constat plus général du poids de la quantité d'habitat sur sa
seule configuration (Fahrig, 2003) et le rôle structurant de la surface des taches, que les indices de
disponibilité d'habitat intègrent explicitement (Pascual-Hortal & Saura, 2006) et que la méta-analyse
de Beninde et al. (2015) désigne, avec la présence de corridors, comme déterminant majeur de la
biodiversité intra-urbaine. Cette cohérence ne remplace pas pour autant une confrontation au mouvement réel, rarement disponible
(Sawyer et al., 2011).

Cette concordance ne vaut cependant pas preuve : la chaîne reproduit fidèlement ce qu'elle a été
paramétrée pour modéliser, et un résultat conforme aux hypothèses de calibration n'est pas, en soi, une
connectivité observée. Ces sorties relèvent d'un modèle de connectivité potentielle. La part d'habitat
connecté (0 à 100 %) et la surface connectée équivalente s'interprètent en absolu, mais elles ne fixent
pas de seuil écologique et ne valent pas mesure de terrain : leur usage le plus fiable est la
comparaison entre profils écologiques, territoires et états d'un scénario. La surface équivalente
croissant avec la taille du territoire, c'est la part connectée, normalisée, qui est privilégiée pour
comparer des territoires d'emprises différentes.

## 4.2. Des contrastes entre territoires qui reflètent la forme urbaine

Les écarts de connectivité entre territoires (§3.3), obtenus par une méthode identique partout,
reflètent surtout la structure du paysage (la couverture d'OpenStreetMap, variable d'une ville à
l'autre (Barrington-Leigh & Millard-Ball, 2017), restant un facteur de confusion résiduel), ce qui fait de l'outil un instrument de comparaison
des territoires eux-mêmes (Figure 19). Une trame urbaine compacte et fortement imperméabilisée fragmente nettement les profils
écologiques terrestres : les noyaux y sont petits et séparés par une matrice hostile, et les ruptures
se multiplient sur le réseau routier. Cet effet de l'imperméabilisation est documenté en
ville, avec une relation non linéaire (bascule de l'activité vers 60 % de bâti chez la chauve-souris,
atténuée par des réseaux arborés connectés ; Hale et al., 2012) ; il apparaît toutefois surtout au-delà
d'un seuil, une ville peu dense (imperméabilisation inférieure à environ 42 %) pouvant ne montrer aucun
effet net (Larson & Sander, 2024), ce qui invite à ne pas généraliser le lien compacité-fragmentation
hors des tissus les plus denses. Là où la ville conserve de grandes continuités végétalisées,
coulées vertes, ceinture boisée, vallée, le réseau reste mieux structuré et les corridors s'appuient
sur ces armatures. Ce rôle des armatures végétalisées rejoint les travaux montrant que des
corridors boisés structurent les communautés jusque dans les villes (Vergnes et al., 2012 ; Braaker
et al., 2014). Un cours d'eau traversant joue un rôle ambivalent : support de continuité pour les
profils écologiques qui le franchissent, coupure pour ceux dont il est un obstacle. À
Calgary, les rivières se sont même révélées moins perméables que les routes ou les voies ferrées pour
les passereaux forestiers, même en deçà de 50 m de large (Tremblay & St. Clair, 2009), ce qui rappelle
qu'un cours d'eau n'est un corridor que pour les profils qui le franchissent réellement.

Ce lien entre forme
urbaine et connectivité se lit directement dans les indicateurs, la part d'habitat du territoire en
ordonnant les résultats. La Rochelle, la moins végétalisée (environ 20 % de couverture d'habitat), est
la plus fragmentée pour les profils boisés : l'oiseau de lisière s'y morcelle en vingt-huit
sous-réseaux, le mammifère arboricole en onze. Toulouse (environ 32 %), métropole dense, connecte encore
bien le petit mammifère terrestre (52 %) mais effondre le reptile (9 %, huit sous-réseaux). Perpignan,
compacte et méditerranéenne (environ 39 %), fragmente surtout le reptile (quatorze sous-réseaux). À
l'inverse, Nancy et La Roche-sur-Yon, plus végétalisées (environ 48 à 50 %), conservent un réseau connexe
pour le petit mammifère terrestre (71 et 83 %). Un point mérite toutefois nuance : une forte couverture
végétale totale ne garantit pas la connectivité de chaque profil. La Roche-sur-Yon, verte à 50 %,
connecte 83 % de l'habitat du petit mammifère terrestre mais seulement 28 % de celui de l'arboricole et
19 % de celui de l'oiseau de lisière, l'habitat boisé y étant dispersé dans une matrice agricole ; c'est
donc l'agencement de l'habitat propre à chaque profil, plus que la seule quantité de vert, qui commande
la connectivité.

[FIGURE : Part d'habitat connecté par territoire et par profil écologique, territoires classés par
couverture végétale croissante. La connectivité croît globalement
avec le couvert, mais l'écart entre profils au sein d'un même territoire, marqué à La Roche-sur-Yon,
montre que l'agencement de l'habitat compte autant que sa quantité.]

La nature du couvert, et pas seulement son étendue, distingue les territoires. La Rochelle,
littorale, est presque dépourvue de boisement (forêt sur 4,5 % de l'emprise seulement), ce qui explique
l'effondrement des profils boisés. Toulouse, métropole dense, conserve un couvert arboré modéré (20 %)
mais très peu de milieux ouverts (11 %), d'où la fragmentation du reptile. Perpignan, méditerranéenne et
compacte, combine peu de forêt (11 %) et une matrice arbustive. Nancy est le plus forestier des
territoires tempérés (33 % de forêt), ce qui soutient la bonne connectivité du mammifère arboricole et
de l'oiseau de lisière. La Roche-sur-Yon, la plus végétalisée (50 %), l'est surtout en milieux herbacés
et agricoles (forêt sur 20 % seulement), d'où le contraste déjà noté entre un petit mammifère terrestre
bien connecté et des profils boisés dispersés. Kourou, enfin, s'insère dans un couvert forestier
équatorial (37 % de forêt).

Kourou demande une lecture prudente. Ses parts connectées élevées sur tous les profils (de 45 % pour le
reptile à 82 % pour l'arboricole, pour une couverture d'habitat d'environ 53 %) sont cohérentes avec une
petite ville insérée dans un couvert forestier quasi continu ; mais les profils écologiques tempérés y
sont peu représentatifs et le besoin opérationnel y est moindre. Ce cas illustre surtout la
transposabilité de la chaîne à un biome très différent, plus qu'un diagnostic écologique directement
exploitable.

Cette comparaison a une valeur opérationnelle directe : elle montre qu'un même geste d'aménagement n'a
pas le même effet selon le tissu urbain, et que la priorité, renforcer les espaces relais
dans certains territoires, rétablir une continuité interrompue dans d'autres, dépend de la structure
propre à chaque territoire.

## 4.3. Un aménagement qui agit localement, invisible dans les indicateurs agrégés

Un aménagement d'échelle urbaine courante agit localement, en créant un noyau que l'étape de moindre
coût raccorde au réseau, sans déplacer les indicateurs agrégés, qui diluent un projet de quelques
hectares sur l'ensemble de l'emprise : sur le cas de Toulouse (§3.6), le site gagne des liens de
raccordement alors que la part d'habitat connecté et le nombre de sous-réseaux du territoire restent
inchangés. Pour de tels projets, c'est donc l'échelle locale qui renseigne la décision : l'indicateur global ne se
déplace que pour un projet bien plus vaste, ou situé précisément sur un point de rupture du réseau dont
le rétablissement reconnecte de grands ensembles. L'indicateur
agrégé n'est donc pas adapté à l'évaluation de petits aménagements, ce qui oriente la lecture du tableau
de bord vers le voisinage du site plutôt que vers la valeur globale de connectivité.

Cette lecture locale a une valeur opérationnelle directe : elle chiffre ce qu'un projet précis change
dans son voisinage et permet d'arbitrer entre des gestes concurrents, renforcer un espace relais à un
endroit, rétablir une continuité interrompue à un autre. Elle invite surtout à distinguer deux usages
de l'outil : le diagnostic comparatif, à l'échelle du territoire et entre profils écologiques, et
l'évaluation d'un projet, à l'échelle du site et de son voisinage immédiat, chacun appelant un
indicateur et une échelle de lecture différents.

## 4.4. Validité : vérification, validation interne, externe et de terrain

La validité d'un modèle de connectivité s'apprécie sur plusieurs niveaux complémentaires. La démarche
retenue ici en distingue quatre et situe le travail sur chacun, plutôt que de le déclarer globalement
valide ou non. La vérification porte sur l'implémentation, à savoir si le code
calcule correctement les indices annoncés : les formules retenues sont celles de la littérature
(équations (1) à (4)) et le contrôle automatisé des sorties (chapitre 2) écarte les erreurs grossières,
mais un étalonnage formel contre un logiciel de référence (Graphab, Conefor) reste à mener et serait
peu coûteux sur un cas test. La validation interne examine la sensibilité au paramétrage (§3.4). La
validation externe confronte les sorties à une méthode indépendante, celle du Cerema Dter Sud-Ouest
appliquée à La Rochelle (2025), et à des observations d'espèces (GBIF, §3.5). La validation de terrain,
enfin, une confrontation à des données de mouvement ou d'occurrence suivies, sort du périmètre du
stage ; les coefficients de friction et les distances de dispersion sont toutefois empruntés à des
études elles-mêmes validées sur le terrain (Balbi et al., 2019, 2021), de sorte que des paramètres
validés ailleurs sont ici transférés, au prix d'une hypothèse à assumer : que le comportement mesuré à
Rennes ou Zurich vaille dans les villes étudiées. Les paragraphes suivants précisent où en est le
travail sur chacun de ces niveaux.

La robustesse aux choix de calibration (§3.4) indique que les conclusions comparatives, entre profils
et entre territoires, résistent à une variation plausible des frictions et des distances de dispersion,
tandis que les valeurs absolues (part connectée, surface équivalente) en dépendent directement. Cette robustesse reste toutefois
conditionnelle, la sensibilité des graphes de moindre coût aux valeurs relatives de coût étant maximale
précisément dans les paysages fragmentés à matrice intermédiaire (Rayfield et al., 2010), configuration
proche de plusieurs des territoires étudiés. Le reptile, peu mobile et à l'habitat rare, se
tient près d'un point de bascule au-delà duquel son réseau se scinde en plusieurs sous-réseaux, quand le généraliste en reste
loin ; un territoire déjà morcelé rapproche d'autant chaque profil de ce basculement. La connectivité tient au contraste entre frictions plus qu'à leur niveau
absolu, ce qui désigne l'écart de résistance entre classes d'occupation du sol comme le paramètre
déterminant, en cohérence avec l'observation, faite en théorie des circuits, que le rang des
résistances importe davantage que leur amplitude absolue (Bowman et al., 2020).

La convergence avec la méthode du Cerema Dter Sud-Ouest sur La Rochelle (2025, §3.5), obtenue indépendamment à partir de
données et d'outils différents, constitue une validation croisée partielle : deux démarches
construites séparément aboutissent au même diagnostic là où elles se recouvrent. Cette
prudence est justifiée, car des méthodes structurelles distinctes peuvent converger entre elles tout en
s'écartant fortement de la connectivité fonctionnelle observée (recouvrement d'environ 21 % avec des
trajets GPS dans Rezvani et al., 2024) ; la validation empirique reste d'ailleurs rarement réalisée en
cartographie de connectivité (Laliberté & St-Laurent, 2020).

La concordance avec les occurrences GBIF (§3.5) valide la couche d'habitat pour les espèces d'habitat
boisé, nettement sur-représentées dans les noyaux ; elle reste indicative pour le petit mammifère terrestre,
généraliste tolérant à la matrice, dont la distribution urbaine est mieux captée par les éléments
relais que par les grands noyaux, et non concluante pour le reptile, faute d'occurrences suffisantes.
Ces données renseignent la présence, non le flux : elles confirment l'habitat, non la
connectivité elle-même, la distinction entre connectivité structurelle et fonctionnelle restant le
verrou central du champ (LaPoint et al., 2015 ; Habrich & Fahrig, 2025) ; la favorabilité d'habitat
est du reste un mauvais indicateur de la connectivité au moment de la dispersion, des milieux peu
favorables pouvant porter des routes de déplacement réelles (Keeley et al., 2017). La reproductibilité, enfin, tient au caractère déterministe de la chaîne et à
son appui sur les seules données ouvertes, un tiers pouvant la rejouer de bout en bout.

Une validation de terrain reste nécessaire pour passer d'une connectivité potentielle à une
connectivité vérifiée ; sa forme possible et ses limites sont exposées en perspective (chapitre 5). À la différence des rares travaux ayant confronté des tracés de moindre coût à des
mouvements réels, par translocation et recapture (Balbi et al., 2019, 2021), ou la résistance
paysagère au flux de gènes (Beninde et al., 2016 ; Braaker et al., 2017), la présente chaîne repose sur
des données ouvertes sans relevé de terrain ; sa validation demeure donc indirecte, ce qui situe sa
portée sans l'invalider.

## 4.5. Un apport opérationnel : l'assemblage de briques établies

La contribution de ce travail est opérationnelle. Les briques employées, segmentation morphologique,
graphes de connectivité, Probability of Connectivity, chemins de moindre coût, sont établies et
documentées (chapitre 1) ; l'apport vient de leur assemblage. La chaîne les réunit en un enchaînement
unique, fondé sur les seules données ouvertes, décliné par profil écologique et transposable sans
calibration locale, dont les sorties sont restituées à des aménageurs non spécialistes par un tableau
de bord. Sa valeur tient à la reproductibilité et à l'accessibilité de l'ensemble. L'outil passe ainsi d'un diagnostic à un instrument d'aide à la décision : le test de scénarios
permet d'évaluer un projet avant de le décider.

L'outil privilégie la portabilité et le faible coût à la finesse écologique : des profils génériques,
l'absence de calibration de terrain et des données mondiales sont à la fois ce qui le rend applicable
partout et ce qui en limite la précision écologique. Une étude locale calibrée sur des données
d'occurrence et un dire d'expert serait plus juste, mais ni généralisable ni rejouable à faible coût. L'outil occupe délibérément la place d'un
pré-diagnostic généralisable plutôt que d'une expertise locale, répondant à une demande opérationnelle,
de nombreuses villes à traiter avec des moyens limités, plutôt qu'à une exigence académique de précision
sur un site unique. Ce positionnement répond au constat récurrent d'un déficit d'outils opérationnels
et validés en connectivité urbaine (LaPoint et al., 2015 ; Habrich & Fahrig, 2025) et rejoint les
démarches récentes d'aide à la planification par groupes d'espèces (Kirk et al., 2023), les chaînes
reproductibles sur données d'observation de la Terre déployées à l'échelle de nombreuses villes (Borghi
et al., 2026, sur vingt-huit capitales européennes) et les systèmes d'aide à la décision conçus pour
des planificateurs non spécialistes (Losada-Iglesias et al., 2024).

La restitution conditionne enfin la réception opérationnelle. Le tableau de bord n'affiche pas toutes
les couches produites : les liens jugés non fonctionnels ne sont pas représentés, pour ne pas
suggérer des connexions qui n'existent pas ; les points de rupture sur l'eau, à l'inverse, sont
conservés, car ils signalent des coupures sur lesquelles un aménageur peut agir. Ces choix d'affichage
orientent en partie les priorités d'action ; ils sont donc explicités et justifiés dans ce rapport.
Une carte de connectivité signale
où la continuité est en jeu, mais elle n'est pas un acte de planification : la traduire en décision
suppose un arbitrage avec d'autres enjeux urbains, que l'outil ne remplace pas.

## 4.6. Limites et portée des résultats

Les limites présentées ici n'ont pas pu être levées dans les six mois du stage. Celles qui ouvrent une
suite possible sont reprises comme perspectives au chapitre 5, plutôt que listées comme des manques.
Chacune est examinée sous deux angles : le sens du biais qu'elle introduit, et le fait qu'elle pèse
surtout sur la valeur absolue de l'indicateur, moins sur son usage comparatif.

Plusieurs limites conduisent à surestimer la connectivité. La couche d'occupation du sol décrit un
couvert vu du ciel, sans hauteur : une canopée surplombant une surface imperméable est lue comme un
habitat arboré au sol, ce qui crée des habitats fictifs, surtout dans les centres denses, et fait voir
des continuités qui n'existent pas pour les profils écologiques terrestres. Une occupation
du sol sans hauteur surestime effectivement la connectivité du vert urbain, le biais étant maximal pour
les faibles capacités de dispersion, car toutes les strates verticales y sont traitées comme connectées
(Casalegno et al., 2017). Dans le même sens, les
obstacles fins du tissu urbain (clôtures, murs, glissières) ne figurent dans aucune donnée ouverte
exploitable et ne sont pas modélisés, alors qu'ils coupent réellement les déplacements au sol : leur
absence laisse passer des liens qui, sur le terrain, seraient rompus. De fait, aucun
inventaire géospatial systématique des clôtures n'existe (Poor et al., 2014), ce qui rend ce biais
structurellement difficile à corriger à partir de données ouvertes.

L'incidence de la résolution est plus ambiguë. À 10 m, les éléments fins du paysage (haies étroites,
alignements d'arbres, petits jardins) passent sous le seuil de détectabilité de Sentinel-2 (Radoux et
al., 2016) et disparaissent, ce qui fait perdre des relais et tend à sous-estimer la connectivité ; mais à la même résolution, une coupure étroite (route
ou bande bâtie plus fine que le pixel) peut être absorbée dans une classe végétalisée dominante et
souder artificiellement deux taches, ce qui surestime au contraire la continuité. La perte de ces
petits éléments n'est en outre pas seulement un défaut : elle écarte aussi les micro-taches trop petites
pour constituer un habitat fonctionnel, tel un arbre isolé, qui seraient sinon comptées à tort comme
noyaux ou relais. La direction du biais lié à la résolution n'est donc pas tranchée et dépend de la
configuration locale.

Ces biais jouent en sens contraires, et parfois indéterminés ; ils ne se compensent pas de façon
prévisible, et leur effet net sur une valeur absolue de connectivité reste inconnu. C'est pourquoi
l'indicateur n'est exploité qu'en relatif : tant que les mêmes biais s'appliquent à tous les profils
écologiques, à tous les territoires et aux deux états d'un scénario, la comparaison les neutralise en
grande partie, quand la valeur absolue, elle, demeure peu fiable. Cette lecture relative a toutefois sa
propre limite : elle suppose que les biais s'appliquent uniformément, or certains ne le sont pas, la
confusion de la canopée sur surface imperméable étant par exemple plus fréquente dans les centres
denses qu'en périphérie ; une comparaison entre deux secteurs très contrastés d'un même territoire peut
donc rester affectée.

À ces biais s'ajoute une dépendance à la calibration. Les valeurs de friction et les distances de
dispersion proviennent de la table du Cerema Dter Sud-Ouest, elle-même construite à partir de plusieurs
sources (littérature, dires d'expert, données locales), puis sont réinterprétées et ajustées ici
(chapitre 2) ; l'analyse de sensibilité (§3.4) montre que les classements entre profils et entre
territoires restent stables lorsqu'on fait varier ces paramètres dans une plage plausible, quand les
valeurs absolues, elles, varient, ce qui renforce le statut d'indice relatif des sorties. Chaque profil écologique est en outre défini par les paramètres
d'une espèce repère, et les quatre profils retenus ne couvrent qu'imparfaitement la diversité
fonctionnelle : le profil des insectes, un temps envisagé, a été écarté faute d'une occupation du sol
assez fine à 10 m pour distinguer leurs micro-habitats, et les pollinisateurs comme les petits
invertébrés ne sont pas représentés. Les réseaux produits valent pour les profils de
déplacement retenus, non pour l'ensemble de la faune urbaine.

D'autres limites n'affectent pas tant la valeur que son interprétation. La qualité estimée des noyaux
est structurelle, fondée sur la taille et la compacité, et non écologique : les pressions diffuses
(pollution lumineuse, Gaston et al., 2013 ; pollution sonore, Francis & Barber, 2013 ; prédation par
le chat domestique, Loss et al., 2013 ; dérangement, gestion des espaces) ne sont pas captées, si bien
qu'un grand noyau compact peut recouvrir un habitat dégradé. L'intensité du trafic
n'est pas davantage prise en compte, une route pesant par sa classe et non par son flux. Ces mêmes
pressions sensorielles, éclairage et bruit, agissent en outre comme des barrières au déplacement
qu'une carte d'occupation du sol ne capte pas : le modèle les ignore et surestime d'autant la
perméabilité du tissu urbain. Le tracé des chemins de moindre coût est aussi approximatif pour tous les
profils et tous les territoires. L'occupation du sol, qui fusionne WorldCover et OpenStreetMap, est
ramenée à une grille de dix mètres attribuant une seule classe par pixel, alors qu'un pixel de dix
mètres est souvent mixte sur le terrain. Un pixel classé perméable peut ainsi contenir un bâtiment que
sa classe n'indique pas, franchi sans le voir par un chemin de moindre coût, tandis qu'un pixel
réellement classé comme bâti reste, lui, correctement infranchissable. Le calcul sur une grille à huit
directions, puis le lissage cartographique appliqué aux lignes, accentuent ce caractère : la géométrie
précise d'un corridor doit donc être lue comme indicative, à l'échelle du tissu urbain, et non au mètre
près, sans que cela change les liens du réseau ni leur coût. Un lien peut ainsi sembler traverser
un bâtiment, soit que celui-ci occupe un pixel non codé comme bâti, soit que le lissage ait rogné un
angle : le tracé vaut indication et non itinéraire de terrain, et appelle une vérification locale avant
tout usage fin. Les sorties
décrivent enfin des potentialités à une date donnée, celle de l'imagerie, sans dynamique saisonnière ni
temporelle, alors que la connectivité fonctionnelle est souvent intermittente, s'ouvrant par fenêtres
selon les conditions de la matrice (Zeigler & Fagan, 2014). Cette limite est en partie tempérée par le
caractère rejouable de la chaîne : construite sur des données ouvertes régulièrement mises à jour, elle
peut être relancée sur les millésimes ultérieurs d'occupation du sol pour suivre l'évolution dans le temps.

La limite la plus structurante reste l'absence de validation de terrain : faute de données d'occurrence
ou de suivi, les sorties demeurent des potentialités et non une connectivité observée, ce qui marque la
frontière de ce qu'une approche fondée sur des données ouvertes et sans relevé de terrain peut affirmer.
À cette limite pratique s'ajoute une limite de principe : le déplacement animal comporte une part
aléatoire qu'un modèle déterministe à chemin unique ne restitue pas ; le mouvement réel se situe en
fait entre l'optimum du moindre coût et la marche aléatoire de la théorie des circuits (Panzacchi et
al., 2016), de sorte que la connectivité modélisée décrit une potentialité et non un comportement
certain.
Le périmètre reste volontairement limité à la trame verte : la trame bleue et la connectivité
aquatique en sont exclues, d'où l'absence de profil écologique amphibie, alors même que les amphibiens
comptent parmi les groupes les plus menacés par la fragmentation et l'urbanisation (Cushman, 2006 ;
Hamer & McDonnell, 2008) ; ce manque est repris comme perspective au chapitre 5.

Ces limites dessinent deux directions d'erreur symétriques, qu'aucune donnée de terrain ne permet ici
de chiffrer. Le modèle peut surestimer la connectivité (faux positifs) en traçant un corridor là où le
déplacement n'a pas lieu, faute d'avoir vu une pression sensorielle ou un trafic intense. Il peut à
l'inverse la sous-estimer (faux négatifs) en annonçant une rupture là où un passage à faune non
recensé, ou une haie et des jardins sous la résolution de dix mètres, assurent en réalité la
continuité.

Ces limites ne rendent pas l'outil inutilisable : elles en circonscrivent l'usage. C'est un instrument
reproductible et peu coûteux de pré-diagnostic comparatif, qui signale où la connectivité est
vraisemblablement en jeu et permet de simuler plusieurs scénarios d'aménagement et de les comparer, et non
un substitut à une étude écologique de terrain là où les enjeux sont forts.
