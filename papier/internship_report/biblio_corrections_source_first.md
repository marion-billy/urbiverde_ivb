# Corrections source-first : ce que la littérature établit vs ce que le rapport lui fait dire

> Document de travail (à retirer du rendu). Objectif : appliquer le bon sens de production.
> On part de **ce que chaque papier établit réellement** (lu à la source, workflow de vérification
> bibliographique), puis on **contraint l'affirmation** du rapport par ça. Chaque point signale
> l'écart éventuel entre « ce que le rapport dit / risque de dire » et « ce que la source porte »,
> et propose une reformulation défendable devant un jury SIGMA qui ouvrirait le papier.
>
> Statut des références citées ici : vérifiées existantes via source autoritaire (76 réfs,
> `biblio_master.json`). Les réfs d'histoire de vie des espèces (d₀ hérisson, écureuil…) sont en
> cours de vérification séparée (workflow `wf_c9db2401-4b5`) et ne sont pas encore intégrées.

---

## Principe directeur (à garder en tête pour toute la révision)

Une référence réelle attachée à une affirmation qu'elle n'établit pas est **plus dangereuse** qu'un
DOI inventé : elle passe la relecture superficielle et se retourne contre l'autrice si un membre du
jury ouvre le papier. Donc, pour chaque affirmation du corps :

1. citer seulement ce qui est réellement établi par la source ;
2. quand le rapport va plus loin que la source (choix d'implémentation, seuil, convention), le dire
   comme **un choix assumé de la démarche**, pas comme un fait attribué à la littérature ;
3. distinguer systématiquement *connectivité structurelle/potentielle* (ce que le modèle produit)
   de *connectivité fonctionnelle validée* (ce que la littérature dit rarement atteignable sans
   données de mouvement).

---

## 1. MSPA : le seuil de 1 ha n'est PAS dans la littérature (écart fort)

**Ce que les sources établissent réellement.**
- La MSPA (Vogt et al., 2007 ; Soille & Vogt, 2009) est une segmentation morphologique d'une carte
  binaire en classes (cœur/*core*, îlot, pont, boucle, bord, perforation, branche) par
  érosion/dilatation. Le paramètre déterminant documenté est la **largeur de bord** (*edge width*),
  fixée par l'utilisateur : elle conditionne ce qui compte comme cœur.
- Ostapowicz et al. (2008) établissent que les proportions de classes sont **sensibles à l'échelle**
  (taille de pixel P et paramètre S) : il n'existe pas de paramétrage objectif universel.
- Vogt & Riitters (2017, GuidosToolbox) : les paramètres clés (edgewidth, connectivité, taille
  minimale d'objet) sont des **choix d'utilisateur documentés**, pas des valeurs canoniques.

**Écart avec le rapport.** Le rapport fixe des seuils de surface (noyaux ≥ 1 ha, relais 0,1–1 ha).
**Aucune source consultée ne fixe un seuil de 1 ha propre à la MSPA.** Le présenter comme
« la MSPA définit des noyaux ≥ 1 ha » serait une sur-attribution.

**Reformulation défendable.** « La MSPA segmente la carte d'habitat en classes morphologiques
(Vogt et al., 2007 ; Soille & Vogt, 2009) ; parce que la quantification dépend de l'échelle et du
paramétrage (Ostapowicz et al., 2008 ; Vogt & Riitters, 2017), le seuil de surface distinguant
noyaux et relais (1 ha ; 0,1–1 ha) est **un choix de la présente chaîne**, justifié par [surface
minimale d'un habitat fonctionnel en contexte urbain / lisibilité pour l'aménageur], et non une
valeur imposée par la méthode. » → à consigner comme choix dans §2.4 et à rappeler en limite (§4.4).

Réfs porteuses : `vogt2007`, `soille2009`, `ostapowicz2008`, `vogt2017` ; contexte urbain +
sensibilité au grain : `wang2021`, `etude2024` (Xiongan).

---

## 2. Moindre coût → « corridor » : abus de langage documenté (écart fort)

**Ce que les sources établissent réellement.**
- Adriaensen et al. (2003) fondent la modélisation par moindre coût (surface de résistance,
  distance effective) ; ils soulignent que le résultat dépend **entièrement de la subjectivité des
  coûts** attribués.
- Sawyer et al. (2011) : forte sensibilité des tracés à la spécification (souvent arbitraire) des
  coûts ; **rareté des validations empiriques** contre le mouvement réel.
- Etherington (2016) : le **chemin unique** ne restitue pas la largeur ni les trajets alternatifs.
- Pinto & Keitt (2009) : le LCP classique n'identifie qu'un chemin alors que des trajets de coût
  comparable existent (redondance ignorée).
- Shirabe (2018), résultat le plus tranchant : **un LCP, même mis en tampon ou empilé, n'est pas un
  corridor de moindre coût** ; l'optimum d'un chemin (largeur nulle) ne se translate pas en optimum
  d'emprise. Un LCP est mathématiquement un trait de largeur nulle.

**Écart avec le rapport.** Appeler les sorties de moindre coût des « corridors » (au sens d'emprises
optimales) est un abus de langage que la littérature identifie explicitement. Cela recoupe une
remarque déjà faite : les « segments d'aménagement » ne sont qu'un artefact d'affichage (clip sur
les habitats, anti-recouvrement), **pas** un objet écologique optimisé.

**Reformulation défendable.** Parler de **« liens »** ou **« tracés de moindre coût »** (least-cost
paths), pas de corridors optimaux. Ajouter une phrase : « Un tracé de moindre coût est un trait de
largeur nulle et le chemin optimal en coût n'est pas l'emprise optimale (Shirabe, 2018 ; Pinto &
Keitt, 2009) ; ces tracés indiquent *où* un lien est le plus probable, non la forme ni la largeur du
corridor à aménager. » → naturel en §2.4 (méthode) et en §4.4/4.6 (limites).

Réfs porteuses : `adriaensen2003`, `sawyer2011`, `etherington2016`, `pinto2009`, `shirabe2018` ;
validation urbaine indirecte : `balbi2021`.

---

## 3. Noyau de dispersion exponentiel : caveat des queues épaisses (écart modéré)

**Ce que les sources établissent réellement.**
- Le noyau négatif-exponentiel p = exp(−d/d₀) est la forme la plus répandue dans les graphes
  paysagers, parce qu'il ne dépend que d'un paramètre d₀ calibrable par un couple (distance,
  probabilité) — Foltête et al. (2012, Graphab) ; Saura & Pascual-Hortal (2007).
- **Mais** Clark et al. (1999) et la revue de Nathan et al. (2012) établissent que l'exponentielle
  **sous-estime la dispersion à longue distance** (queues épaisses / *fat tails* mieux ajustées par
  des noyaux type 2Dt ou puissance). Urban & Keitt (2001) : les résultats sont **très sensibles au
  seuil de distance**, dont la valeur écologique est difficile à fixer.

**Écart avec le rapport.** Le choix de l'exponentielle est légitime et standard, mais le rapport doit
l'assumer comme un choix de parcimonie **avec sa limite connue**, pas comme la forme « naturelle ».

**Reformulation défendable.** « La probabilité de franchissement décroît selon un noyau
négatif-exponentiel de paramètre d₀, forme standard des graphes paysagers pour sa parcimonie
(Foltête et al., 2012 ; Saura & Pascual-Hortal, 2007). Cette forme sous-estime les événements de
dispersion à longue distance (Clark et al., 1999 ; Nathan et al., 2012), limite assumée ici au
regard des données disponibles. » → §2.3/2.4, rappel en §4.4.

Réfs porteuses : `foltête2012`, `saura2007`, `clark1999`, `nathan2012`, `urban2001` ;
opérationnalisation Cerema/TETIS : `chailloux` (BioDispersal).

---

## 4. Frictions et profils : corriger le CADRAGE « Cerema », pas la provenance (écart fort, factuel)

> **Rectificatif important.** Une version antérieure de ce mémo affirmait que les frictions étaient
> « un agrégat de Lumia 2023 / Gelmi-Candusso 2025 + traits ». **C'est faux** et non soutenu par le
> code : c'est la même faute que la remarque dénonce (attribuer une provenance non vérifiée), en sens
> inverse. La source de vérité est `utils/species_params.py`.

**Ce que le CODE établit (source de vérité, `utils/species_params.py`).**
- Les **valeurs de friction** sont *« empruntées au Tableau CEREMA La Rochelle (2025, pp. 96-98)
  pour l'espèce de référence de chaque profil »*, puis **réinterprétées au niveau du syndrome**
  (pas de l'individu de l'espèce nommée) et **transposées à WorldCover** par moyenne des classes
  CEREMA regroupées sous un code.
- Les **distances d₀** sont ancrées sur le *« Tableau 8 p44 CEREMA »* mais **ajustées** : le code
  note lui-même arboricole 1500→2000 et reptile 500→750 ; ce ne sont donc pas des lectures verbatim.
- Le code s'écarte explicitement de CEREMA par des **règles propres** : seuil habitat ≤ 3, barrières
  encodées en NaN (≠ 100), échelle finie pour les routes, eau (code 80) traitée en barrière vu la
  grossièreté de WorldCover 10 m, bâti non valorisé pour le reptile. Et il refuse l'**approche
  cortège-par-sous-trame** du CEREMA (faute d'occupation du sol assez fine).
- Le champ `refs` de chaque profil liste **plusieurs références** (hérisson : Cerema 2025,
  Berthoud 1978, Morris 1984, Huijser & Bergers 2000, Braaker 2017, Tarabon 2019, Balbi 2019) : elles
  justifient le **syndrome, les espèces représentatives et l'ordre de grandeur du d₀**, pas les
  valeurs de friction (qui, elles, viennent de CEREMA).

**Ce que dit Marion (commentaire 567, sa correction, à appliquer).** *« On ne s'appuie pas sur une
seule méthode de référence pour les profils écologiques et les frictions. Cerema Dter SO utilise une
méthode similaire, donc intéressant de citer pour justifier nos choix, mais c'est surtout la
référence du territoire La Rochelle calibrée localement où on compare nos résultats. »*

**Écart avec le rapport.** Le rapport écrit « espèce de référence **calibrée par le Cerema** » et
« coefficients **transposés du Cerema** » comme si l'on **appliquait** la méthode CEREMA. Or (i) les
*valeurs* viennent bien de CEREMA, mais (ii) l'*approche* et les *ajustements* sont propres, et (iii)
CEREMA est surtout le **territoire de comparaison**. Le problème est donc de **cadrage**, pas de
provenance : ne pas nier que les valeurs viennent de CEREMA, mais ne pas présenter le travail comme
une simple application de sa méthode.

**Reformulation défendable (fidèle au code + au commentaire 567).**
« Les valeurs de friction sont **ancrées sur la table du Cerema La Rochelle** (2025, pp. 96-98),
prises pour l'espèce de référence de chaque profil, puis **réinterprétées au niveau du syndrome
écologique** et transposées à la nomenclature agrégée de WorldCover. Elles sont **ajustées par des
règles propres à la chaîne** (seuil d'habitat, barrières, échelle des routes, traitement de l'eau).
L'**approche** — profils/syndromes de déplacement, espèces chimères, données ouvertes mondiales — se
distingue délibérément de la méthode cortège-par-sous-trame du Cerema, qui suppose une occupation du
sol plus fine. Le Cerema La Rochelle constitue **avant tout le territoire de comparaison** calibré
localement (§3.5, §4.4). La littérature situe ce type de paramétrage expert et en souligne la
sensibilité (Zeller et al., 2012 ; Beier et al., 2008 ; Stevenson-Holt et al., 2014) ; d'autres
tables réutilisables en contexte (péri)urbain existent (Lumia et al., 2023 ; Gelmi-Candusso et al.,
2025), **citées ici pour positionner la démarche, non comme source des valeurs**. »

→ à appliquer §2.3, Annexe A.1/A.3, et partout où « Cerema » est présenté comme source/méthode unique
(commentaires 141/148/152/159/296/304/567). **Vérifier** que la lecture pp. 96-98 / Tab. 8 p44 est
exacte en ouvrant `Rapport_continuite_eco_CDA_2025.pdf`.

Réfs porteuses : Cerema La Rochelle (2025) comme ancrage + comparaison ; `zeller2012`, `beier2008`,
`stevensonholt2014` pour la sensibilité ; `lumia2023`, `gelmicandusso2025` **en positionnement
seulement** (pas source des valeurs).

---

## 5. Choix des profils écologiques (espèces chimères) : bien sourcé, à valoriser

**Ce que les sources établissent réellement.**
- Lambeck (1997) fonde l'approche par **suite d'espèces focales** (pas une seule parapluie).
- Watts et al. (2010) formalisent l'**espèce focale générique** (profil composite/virtuel construit
  par traits) — c'est exactement la notion d'« espèce chimère » / profil écologique du rapport.
- Meurant et al. (2018) : un jeu de **5 à 7 espèces à traits contrastés** est optimal ; mieux qu'un
  choix par taxon ou parapluie.
- Wood et al. (2022) structurent le champ (surrogate unique / focales multiples / générique) et
  pointent le verrou : aucune approche n'intègre les interactions inter-espèces.
- Kirk et al. (2023) : méthode urbaine opérationnelle par **groupes/guildes** partageant capacité
  de dispersion et exigences d'habitat.

**Usage.** Ce socle justifie solidement le choix « profils écologiques » plutôt qu'« espèce focale
unique ». Il permet aussi de **cadrer honnêtement** : le profil générique lisse la variabilité
inter-espèces et ne vaut que si les espèces regroupées partagent réellement des traits (Watts et
al., 2010) — à mettre en limite. Le passage de 5 à 4 profils doit être présenté comme un choix, pas
comme un optimum (Meurant et al. suggèrent 5–7).

Réfs porteuses : `lambeck1997`, `watts2010`, `meurant2018`, `wood2022`, `kirk2023`.

---

## 6. PC / EC / part d'habitat connecté : indicateurs relatifs et potentiels (cadrage)

**Ce que les sources établissent réellement.**
- Pascual-Hortal & Saura (2006) puis Saura & Pascual-Hortal (2007) : IIC puis **PC** intègrent
  connectivité intra- et inter-patch ; le résultat **dépend fortement du paramétrage** (distance/
  probabilité de dispersion), fixé par l'utilisateur.
- Saura et al. (2011) définissent l'**ECA/EC = √PC × aire** : taille d'un patch unique maximalement
  connecté donnant le même PC — c'est une **connectivité structurelle potentielle**, dépendante de
  la carte d'habitat et du seuil de distance.
- Saura & Rubio (2010) : décomposition dPC (intra/flux/connector) ; la fraction « connector » est
  souvent faible et sensible à la topologie.

**Écart / cadrage.** L'EC et la part d'habitat connecté sont des **indicateurs relatifs et
potentiels**, pas des mesures absolues de flux réel. La réponse à ta question antérieure
(« est-ce vrai que ce sont des indicateurs relatifs ? ») est **oui**, et c'est explicitement porté
par les sources (dépendance au paramétrage, connectivité structurelle). C'est aussi ce qui justifie
d'insister partout sur « connectivité **potentielle** » / « modèle de connectivité potentielle ».

Réfs porteuses : `pascualhortal2006`, `saura2007`, `saura2011`, `saura2010`, `saura2009` (Conefor) ;
application urbaine : `aliabad2024`.

---

## 7. Graphe de Gabriel : géométrie, pas écologie (nuance)

**Ce que les sources établissent réellement.**
- Gabriel & Sokal (1969) : définition **purement géométrique** (analyse de variation géographique),
  pas conçue pour la dispersion écologique.
- Toussaint (1980) : hiérarchie d'inclusion MST ⊆ RNG ⊆ Gabriel ⊆ Delaunay, **cadre euclidien**.
- Minor & Urban (2008), Galpern et al. (2011) : le niveau d'élagage (Delaunay → Gabriel → MST)
  change la topologie et le résultat de conservation ; **pas de consensus** ni de validation
  biologique indépendante. Urban & Keitt (2001), Fall et al. (2007) : cadre des graphes spatiaux.

**Usage.** Justifier le choix de Gabriel comme **compromis** (conserve des chemins alternatifs sans
la lourdeur de Delaunay), en assumant qu'il est **géométrique** et non écologiquement validé (limite).

Réfs porteuses : `gabriel1969`, `toussaint1980`, `minor2008`, `galpern2011`, `urban2001`, `fall2007`.

---

## 8. Données d'occupation du sol : le « built-up » agrégé (bien sourcé)

**Ce que les sources établissent réellement.**
- WorldCover 10 m (Zanaga et al., 2021) et Dynamic World (Brown et al., 2022) : nomenclature
  grossière (11 / 9 classes FAO), **classe *built-up* agrégée** (bâti + routes + surfaces
  artificielles), précision globale ~65–75 % (Venter et al., 2022 ; Xu et al., 2024 ; PUM WorldCover
  2021). Radoux et al. (2016) : détectabilité d'objets fins limitée par Sentinel-2 (haies,
  alignements souvent sous le seuil).
- Complétude OSM ~83 % mondiale, hétérogène (Barrington-Leigh & Millard-Ball, 2017) → justifie le
  recours à OSM pour réintroduire routes/objets fins absents du raster.

**Usage.** Sourcer la limite de WorldCover (built-up agrégé, objets fins manquants) et le complément
OSM. Remplace avantageusement les réfs anciennes/floues (Herold 2004, Audebert 2018, Vallet 2010) là
où elles étaient citées faute de mieux — à réévaluer selon le workflow de vérification en cours.

Réfs porteuses : `zanaga2021`, `brown2022`, `venter2022`, `xu2024`, `radoux2016`, `esa2021`,
`barringtonleigh2017`.

---

## 9. Connectivité urbaine : champ jeune, peu validé (à assumer en discussion)

**Ce que les sources établissent réellement.**
- Beninde et al. (2015, méta-analyse 75 études) : **surface des patches et corridors** sont les
  deux déterminants les plus forts de la biodiversité intra-urbaine.
- LaPoint et al. (2015) : la plupart des travaux urbains restent **structurels**, très peu relient
  structure et fonction → verrou opérationnel.
- Habrich & Fahrig (2025), carte systématique : en milieu urbain, **plus de 70 % des estimations de
  connectivité par graphe ne sont pas validées** par des données biologiques. (réf à pertinence
  « faible » sur le tampon, mais **forte** ici pour cadrer le déficit de validation.)

**Usage.** C'est le meilleur appui pour (i) motiver le sujet (Beninde : corridors = levier majeur),
(ii) **assumer honnêtement** en discussion que la sortie est une connectivité potentielle non
validée sur le terrain — ce qui est la norme du champ, pas une faiblesse propre au stage.

Réfs porteuses : `beninde2015`, `lapoint2015`, `habrich2025` ; fragmentation : `fahrig2003`.

---

## 10. Pressions diffuses (amphibiens/faune urbaine) : ne pas sur-attribuer

**Ce que les sources établissent réellement.**
- Mortalité routière / fragmentation : Fahrig et al. (1995), Hels & Buchwald (2001, probabilité
  d'être tué en traversant 0,34–0,61 selon l'espèce), Cushman (2006, revue amphibiens), Hamer &
  McDonnell (2008, > 1/3 des espèces d'amphibiens menacées par l'urbanisation).
- Pressions diffuses : Gaston et al. (2013, pollution lumineuse) et Loss et al. (2013, prédation par
  le chat) sont **réels mais à pertinence faible** pour un modèle **structurel** de connectivité :
  Gaston = revue mécaniste (peu de dose-réponse in situ) ; Loss = oiseaux/mammifères aux États-Unis,
  pas amphibiens.

**Usage.** Utiliser Fahrig 1995 / Hels 2001 / Cushman 2006 / Hamer 2008 pour justifier les frictions
routières et l'enjeu de connectivité. Citer Gaston/Loss **seulement** pour rappeler, en limite, que
des pressions diffuses non spatialisées échappent au modèle — sans leur faire porter plus.

Réfs porteuses : `fahrig1995`, `hels2001`, `cushman2006`, `hamer2008` ; limites : `gaston2013`
(faible), `loss2013` (faible).

---

## 11. Biais GBIF : cadre usage vs disponibilité (Annexe B)

**Ce que les sources établissent réellement.**
- Occurrences opportunistes structurellement biaisées (spatial/temporel/taxonomique) : Boakes et al.
  (2010), Isaac et al. (2014), Melis et al. (2025) ; correction par background à biais apparié
  (Phillips et al., 2009) ou rasters d'effort (El-Gabbas, 2026).
- Le cadre **usage vs disponibilité** (ratio de sélection wᵢ = oᵢ/pᵢ, test du khi-deux) est fondé
  par Johnson (1980) et formalisé par Manly et al. (2002) — **vérifiés exacts** mais classés
  « pertinence faible » car ce sont les fondations statistiques, pas des réfs sur la connectivité.

**Usage.** Annexe B (ratios de sélection + khi-deux) doit citer **Johnson 1980 + Manly 2002** pour la
méthode, et Boakes/Isaac/Phillips/Melis/El-Gabbas pour justifier qu'on raisonne en usage-vs-
disponibilité **plutôt qu'en occurrences brutes** (correction du biais d'effort). C'est exactement
la bonne parade méthodologique, bien étayée.

Réfs porteuses : `johnson1980`, `manly2002`, `boakes2010`, `isaac2014`, `phillips2009`, `melis2025`,
`elgabbas2026`.

---

## 12. Effet de bord / tampon : convention, pas optimum (nuance)

**Ce que les sources établissent réellement.**
- Koen et al. (2010) : une frontière de carte artificielle se comporte comme une **barrière** et
  sur-estime la résistance. Koen et al. (2014) : parade = tampon ajouté puis retiré après calcul ;
  le **~20 % est une convention pratique, non un optimum démontré**.
- Saura et al. (2014, stepping stones) et Saura et al. (2011, ECA) sont réels mais **à pertinence
  faible** pour le dimensionnement du tampon (ce sont des briques connexes, pas des réfs sur le bord).

**Usage.** Si le rapport applique un tampon, le présenter comme correction d'effet de bord (Koen et
al., 2010, 2014) et dire que la largeur est **une convention calée au cas par cas**, pas un optimum.

Réfs porteuses : `koen2010`, `koen2014` ; à ne pas sur-solliciter : `saura2014`, `saura2011`.

---

## 13. Théorie des circuits : écartée, mais à positionner correctement

**Ce que les sources établissent réellement.**
- McRae et al. (2008), McRae & Beier (2007, prédit le flux de gènes mieux que la distance
  euclidienne/moindre coût) : la théorie des circuits intègre **toutes** les trajectoires (marche
  aléatoire) et produit une carte continue de densité de courant. Dickson et al. (2019, ~459 études)
  la posent comme **complémentaire** au moindre coût, pas remplaçante ; Kwon et al. (2021, urbain) :
  LCP = tracés précis localisés, circuits = gradient diffus. Bowman et al. (2020) : la densité de
  courant est **peu sensible aux valeurs absolues** des coûts tant que leur **rang** est correct.

**Usage.** Le rapport écarte la théorie des circuits (hors périmètre). La positionner honnêtement en
perspective (§5.2) : complémentaire, produit un gradient de perméabilité, robuste au rang des coûts —
et non « inférieure ». Attention : ces agents (`circuits`, `tampon_bord`) ont tourné avec le
classifieur de sûreté indisponible ; **revérifier McRae 2008/Dickson 2019 avant publication finale.**

Réfs porteuses : `mcrae2008`, `mcrae2007`, `dickson2019`, `kwon2021`, `koen2014`, `bowman2020`.

---

## 14. Distances caractéristiques d₀ et réfs d'espèces : les d₀ viennent du CALAGE, pas des papiers (écart fort, factuel)

Résultat de la vérification source-first des 17 réfs ouvertes (`wf_c9db2401-4b5`, 17/17 réelles,
mais plusieurs **mal attribuées** — exactement le cas que la remarque redoutait). Toutes ces réfs
d'histoire de vie **ne portent qu'un ordre de grandeur des déplacements** ; **aucune n'établit la
valeur de d₀ retenue**. Les d₀ (hérisson 3000 m, écureuil 2000 m, etc.) sont un **choix de calage**
(référence Cerema La Rochelle + arbitrage), pas un résultat de Berthoud/Avon/Wauters. Ne jamais
écrire « d₀ = 3000 m (Berthoud, 1978) » comme si le papier fixait cette valeur.

| Réf | Ce que le papier établit réellement | Correction dans le corps |
|---|---|---|
| **Berthoud (1978)** | Déplacements nocturnes hérisson 500 m–1,5 km (♀), ~3 km (♂) ; domaine vital 3–10 ha ; lâchers d'orientation (homing forcé) 5–7 km. Seul l'intro est en ligne (Persée) → confiance moyenne. | Le **~4000 m** n'y figure pas. Ne pas confondre le homing (5–7 km) avec une dispersion naturelle. Citer comme *ordre de grandeur* des déplacements, pas comme source du d₀. |
| **Morris (1984)** | **Poids minimal d'hibernation** (~450 g). Rien sur domaine vital/déplacements. | Remplacer par **Morris (1988)**, *J. Zool.* 214:433–449 (domaine vital ~12–40 ha, ~1,6 km/nuit ♂) partout où il s'agit d'écologie spatiale. Le hérisson n'est pas une espèce à dispersion « longue distance ». |
| **Avon et al. (2014)** | Synthèse méthodo (graphes paysagers, *Sciences Eaux & Territoires*) ; écureuil roux : 200 m (journalier), 700 m (médiane dispersion), jusqu'à 6000 m (max) en **coût-distance**. | Le **~5000 m** n'y figure pas. Citer les vraies valeurs (700 m médiane / 6000 m max) et préciser « coût-distance », pas euclidien. |
| **Wauters et al. (2010)** | Dispersion natale écureuil roux : moyenne ~1014 ± 925 m, jusqu'à ~4110 m ; ~75 % émigrent. | Le **d₀ = 2000 m** n'est pas un résultat du papier. Citer ~1000 m (moyenne) comme appui, pas 2000 m. |
| **Tarabon et al. (2019)** | Maxent + Graphab, 3 mammifères terrestres (écureuil, blaireau, hérisson), milieu urbain, *J. Environ. Manage.* 243:340–349. | OK pour l'approche multi-espèces urbaine ; **ne pas lui prêter** les d₀ du rapport. Vérifier que ce n'est pas l'autre Tarabon 2019. |
| **Balbi et al. (2019)** | Validation de la pertinence écologique du moindre coût (30 hérissons translocés, Rennes), *J. Environ. Manage.* 244:61–68. | OK ; distinct de Balbi 2021 (papillons/oiseaux). Pas de distance absolue de dispersion (comparaison relative). |
| **Huijser & Bergers (2000)** | Mortalité routière hérisson : ~30 % de densité en moins en bord de route, **marginalement non significatif**. | OK pour justifier la friction routière ; ne pas présenter comme effet démographique statistiquement démontré. |
| **Beninde et al. (2016)** | Génétique du paysage du lézard des murailles (Trèves) ; dispersion max ~1 km, moyenne < 200 m. | OK qualitatif (résistance, voies ferrées/canopée) ; vérifier que « voies ferrées = corridors / canopée = barrière » est bien dans CE papier. |
| **Braaker et al. (2017)** | Hérisson Zurich, mouvement + génétique → surfaces de résistance. | OK pour le calage empirique de résistance. |
| **Merkens et al. (2023)** | **Preprint bioRxiv** ; merle noir Munich, calage data-driven. | OK mais **signaler « preprint »**. |
| **Mimet et al. (2020)** | Jardins privés (~36 % des espaces verts) → ~48 % de la disponibilité d'habitat, pipistrelle commune, Paris. | OK, directement conforme. |
| **Ossola et al. (2019)** | *Yards increase forest connectivity* (Boston) : les jardins augmentent la connectivité de la canopée. | Reformuler l'usage : c'est la **connectivité** par les jardins, pas « structure de végétation / biodiversité ». |
| **Grafius et al. (2017)** | Théorie des circuits pour la connectivité des oiseaux urbains ; seuil « 50 % réticents à > 45 m ». | Si le corps visait « services écosystémiques / groupes fonctionnels », c'est **Grafius 2018**, pas 2017. |
| **Tremblay & St. Clair (2011)** | Perméabilité de la matrice, passereaux forestiers, Calgary ; effet de largeur de trouée. | OK, usage conceptuel conforme. |
| **Liu (2022)** | MSPA + graphes + moindre coût, Pékin ; distance de diffusion optimale 20–25 km (paramètre de graphe). | Corriger **« Liu, Z. » → « Liu, Y. »** ; « 20–25 km » = distance de diffusion testée, pas une dispersion d'espèce. |
| **Spanowicz & Jaeger (2019)** | Comparaison ciblée CONNECT vs *meff*, connectivité intra-patch. | **Pas une « revue »** des métriques ; reformuler. |
| **Vallet et al. (2010)** | **Botanique** : végétation de sous-bois de petits boisements (NO France). Rien sur la résolution des produits d'OCS. | **Mauvaise attribution** : retirer cette citation pour « limites de résolution » et la remplacer par **Radoux et al. (2016)** (détectabilité sub-pixel Sentinel-2). |

**Conséquence transversale.** Reformuler §2.3 / Annexe A / §4 pour dire : « les d₀ sont calés
(référence Cerema La Rochelle) et **cohérents avec** les ordres de grandeur publiés (Morris 1988 ;
Wauters et al. 2010 ; Avon et al. 2014 ; Beninde et al. 2016) », et non « d₀ tiré de [tel papier] ».

---

## 15. Ce que le PDF Cerema La Rochelle établit vraiment (lecture directe) + pool de retro-sourcing

Lecture source du `Rapport_continuite_eco_CDA_2025.pdf` (107 p., couche texte via pypdf ; les
tables de friction pp. 96-98 et les fiches espèces pp. 89-94 sont des **images**, non extractibles en
texte). Cela **règle en grande partie** la question de Marion (« species_params.py est un agrégat non
noté, retrouver des références ») : la source de calage est le Cerema, qui **documente lui-même son
agrégat**.

**La méthode du rapport reproduit celle du Cerema La Rochelle :**
- Noyaux par **« cœurs compacts »** = érosion −10 m puis dilatation +10 m (épaisseur min. 20 m, faible
  effet de lisière). C'est exactement l'ouverture morphologique de la chaîne.
- **Seuil de surface de noyau : ≥ 1 ha pour les sous-trames arborée/arbustive et mixte**, ≥ 5 000 m²
  pour la sous-trame herbacée ; en-dessous → « espace relai ». **→ Le seuil de 1 ha du rapport est
  directement documenté par le Cerema La Rochelle** (référence écrite déjà en main), sans recourir à
  l'oral de Lille (4 500 m², trame *sonore*, non documenté).
- **Budget d₀ × 3** (coefficient favorable moyen = 3, résolution 1 m) : formule Cerema (p. 44).
- **Moindre coût** : corridors primaires (1 chemin) + secondaires (alternatifs) ; le Cerema
  **reconnaît lui-même** l'hypothèse d'omniscience/chemin unique (Balbi, 2017) → appui direct au
  caveat « moindre coût ≠ corridor » (§2, §2.4).
- Échelle de friction **1–100, 8 catégories** (milieu de vie 1 ; favorable 2–3 ; … ; infranchissable
  100) : rubrique reprise telle quelle (seuil habitat ≤ 3).

**Distances de dispersion Cerema (par sous-trame) :** 500–1 000 m (herbacée), 1–2 km (arborée/mixte).
Réconciliation avec les d₀ du rapport : lézard 750 m ✓ (dans 500–1 000), écureuil 2 000 m ✓ (= 2 km),
fauvette 1 500 m ✓ ; **hérisson 3 000 m dépasse la fourchette** → c'est un **ajustement propre**, à
justifier par la littérature hérisson (Tarabon et al., 2019 ≈ 4 km ; Morris 1988 déplacements
nocturnes ~1,6 km/nuit, max 3,14 km ; Berthoud 1978), non par le Cerema.

**Le Cerema documente ses propres sources (bibliographie p. 99-102) = le pool de retro-sourcing.**
Les coefficients Cerema sont *« établis par calibrage, à partir de sources bibliographiques (SRCE
Aquitaine et Poitou-Charentes ; Balbi, 2017 ; Cerema 2020, 2022 & 2024, réf. dans les Fiches espèces),
de dires d'expert et de données d'inventaire (FAUNA, LPO) »* (p. 44). Références Cerema directement
mobilisables pour étayer frictions/d₀/choix d'espèces (à ajouter à `rapport_8_references.md` après
vérification de chacune) :
- **Balbi M. (2017)**, *Validation de la fonctionnalité des continuités écologiques en milieu urbain :
  approches plurispécifiques et multi-sites*, thèse de doctorat, 181 p. — **la** source du calage
  Cerema, distincte de Balbi et al. 2019/2021 déjà en biblio.
- **Sordello R. et al. (2011)**, *TVB — Critères nationaux de cohérence, contribution sur les espèces*,
  MNHN-SPN, 57 p. ; **Sordello R. et al. (2013)**, *Synthèses bibliographiques sur les traits de vie de
  39 espèces… déplacements et besoins de continuité*, MNHN-SPN/Opie, 20 p. + 39 fiches — **socle des
  distances de déplacement par espèce** (dont hérisson, écureuil, lézard).
- **Albert C. H. & Chaurant J. (2018)**, « Comment choisir les espèces pour identifier des réseaux
  écologiques cohérents ? », *Sciences Eaux & Territoires* 25 — appui au choix des espèces de référence.
- **Janin A. et al. (2009)**, « Assessing landscape connectivity with calibrated cost-distance
  modelling… », *J. Applied Ecology* 46:833-841 ; **Matutini F. et al. (2021)**, « Integrating landscape
  resistance… amphibian distribution », *Landscape Ecology* — calage cost-distance/résistance.
- SRCE Aquitaine et Poitou-Charentes ; Cerema (2020) Parc national des Pyrénées ; Cerema (2022)
  Libourne ; Cerema (2024) Maremne Adour Côte Sud ; Eurométropole de Metz & Cerema (2022) — méthodes
  Cerema sœurs, réutilisables en positionnement.

**Conséquence.** Le retro-sourcing ne consiste pas à plaquer des papiers « compatibles » : les
valeurs sont ancrées sur le Cerema La Rochelle, qui **agrège et cite** ses propres sources (ci-dessus).
Citer le Cerema La Rochelle comme source de calage + comparaison, **remonter à Balbi 2017 (thèse) et
Sordello 2011/2013** pour la provenance des traits/distances, et n'ajouter la littérature
espèce-par-espèce (Morris 1988, Wauters 2010, Avon 2014, Beninde 2016…) que là où elle **établit**
réellement l'ordre de grandeur retenu. Le seul point à sourcer hors-Cerema est le d₀ hérisson (3 000 m).

---

## Réserves de vérification (encore à traiter avant rendu)

- **Agents `circuits` et `tampon_bord`** : classifieur de sûreté indisponible pendant leur passage →
  revérifier manuellement McRae 2008, McRae & Beier 2007, Dickson 2019, Koen 2010/2014, Saura 2011/2014.
- **Entrées `[non revérifiée ici]`** dans `rapport_8_references.md` (Baguette 2013, Ricketts 2001,
  Inglada 2017, Rayfield 2011, Vimal 2012, With 1997, Urban 2009, MacArthur & Wilson 1967, Taylor
  1993, Audebert 2018, Herold 2004, Blaschke 2010, etc.) : réelles pour les classiques, mais toute
  **valeur ou attribution précise** reste à confronter à la source avant de s'y fier.
- **Corrections de citation à répercuter dans le CORPS** (pas seulement dans la biblio) : Morris
  1984→1988 ; Liu Z.→Y. ; retrait de Vallet 2010 (→ Radoux 2016) ; Merkens = preprint ; requalifier
  l'usage d'Ossola, Spanowicz et Grafius ; ne plus attribuer de d₀ chiffré aux réfs d'espèces.
