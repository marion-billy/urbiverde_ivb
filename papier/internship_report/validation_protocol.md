# Protocole de validation et de robustesse (base du chapitre 5)

> Document de travail. Sans donnee de terrain, la fiabilite se demontre par un faisceau
> d'arguments convergents, structures en trois niveaux. No em dash. A convertir en prose
> pour le rapport une fois les resultats produits.

## Cadre : trois niveaux distincts de fiabilite

1. **Correction interne** : la chaine calcule bien ce qu'elle annonce (deterministe, sorties
   controlees). Deja acquis (controle systematique des 24 jeux ; cf. section D).
2. **Robustesse** : les conclusions ne dependent pas de choix subjectifs (friction, d0). A produire
   -> partie A.
3. **Validite externe** : les sorties correspondent au reel. Pas de suivi de terrain -> preuves
   convergentes partielles (B Cerema, GBIF) + limite assumee.

Chaque partie ci-dessous : objectif, protocole, metrique, visuel, dependances.

---

## A. Analyse de sensibilite (friction + d0) [niveau 2, robustesse]

**Objectif.** Montrer que corridors, points de rupture et KPI ne basculent pas pour une variation
raisonnable des parametres les plus subjectifs. Standard attendu pour un modele de moindre cout
(Beier 2008, Spear 2010, Zeller 2012, Rayfield 2011).

**Parametres perturbes** (un a la fois, OFAT, + 2-3 combinaisons) :
- friction : +/- 20 % sur toutes les classes ; et test cible = deplacer route (52/53) et eau (80)
  d'un cran de permeabilite (les classes les plus structurantes).
- d0 : +/- 25 %.
- (option) seuils : coeur MSPA 1 ha, budget d0 x 3.

**Plan.** 2 territoires contrastes (ex. Perpignan compact + LaRochelle morcele) x 2 profils
(generaliste herisson + specialiste lezard). Chaque perturbation = un re-run parametre.

**Metriques de stabilite** (perturbe vs baseline) :
- corridors : taux de recouvrement spatial (tampon ~20 m, % de longueur retrouvee) + stabilite du nombre.
- points de rupture / blocked : Jaccard des localisations (memes points noirs ?).
- KPI : variation relative de EC, part connectee, n_subnetworks ; **et stabilite du classement**
  entre profils/territoires (l'ordre tient-il ?). C'est le message fort : meme si les valeurs
  bougent, les conclusions comparatives tiennent.

**Visuel.** Tableau parametre -> delta KPI ; diagramme en tornade (sensibilite par parametre) ;
carte de superposition corridors baseline vs perturbe (accord/desaccord).

**Mise en oeuvre (code en place, 2026-07-06).** `run_pipeline.py` accepte `--friction-scale`,
`--d0-scale`, `--out-tag` : perturbe la config en memoire et ecrit sous `data/sensitivity/<tag>/`
(la reference `data/outputs/` reste intacte). Metriques de stabilite + tornado :
`utils/sensitivity_metrics.py`. A LANCER APRES le re-run principal (evite la concurrence).

Grille proposee (Perpignan rapide + LaRochelle ; profils herisson + lezard) :
```
python3 utils/run_pipeline.py Perpignan --ecoprofil ground_mammal --friction-scale 0.8 --out-tag fric_m20
python3 utils/run_pipeline.py Perpignan --ecoprofil ground_mammal --friction-scale 1.2 --out-tag fric_p20
python3 utils/run_pipeline.py Perpignan --ecoprofil ground_mammal --d0-scale 0.75      --out-tag d0_m25
python3 utils/run_pipeline.py Perpignan --ecoprofil ground_mammal --d0-scale 1.25      --out-tag d0_p25
```
Analyse :
```
from sensitivity_metrics import stability_table, tornado_plot, rank_stability
df = stability_table('data/outputs','data/sensitivity','Perpignan','ground_mammal'); print(df)
tornado_plot(df, 'connected_habitat_pct', '_sandbox/tornado_perpignan_gm.png')
```
Sorties de stabilite : recouvrement des corridors (%), Jaccard des liens bloques, delta relatif des
KPI (EC, part connectee, n_subnetworks), et correlation de Spearman du classement des profils.

---

## B. Comparaison Cerema La Rochelle, chiffree [niveau 3, convergence externe]

**Objectif.** Passer du qualitatif (ch.5 actuel) a des taux d'accord sur le territoire commun.

**Dependance bloquante -> PARKE (2026-07-06).** Il faut les **sorties SIG du Cerema** (leurs noyaux,
corridors, points noirs pour La Rochelle) ; **non disponibles pour l'instant** (seul le PDF est en
main). B est donc suspendu tant que les couches ne sont pas obtenues (a solliciter aupres du Cerema /
CeremaDoc). **Repli** en attendant : comparaison semi-quantitative depuis leurs cartes/points noirs
publies (concordance comptee a l'oeil sur le territoire commun), a presenter comme telle (limite).

**Metriques.**
- noyaux : IoU / indice de Jaccard entre nos noyaux et les leurs.
- corridors : % de nos corridors longeant les leurs (tampon) et reciproquement.
- points noirs : matrice de concordance (communs / propres a chacun).

**Visuel.** Cartes cote a cote + une carte de **superposition** (accord en vert, desaccord en rouge).

**Portee.** Convergence de METHODE (deux approches independantes concordent), pas verite terrain.

---

## C. Comparaison aux occurrences GBIF [niveau 3, convergence externe, cote presence]

**Objectif.** Preuve convergente que l'habitat modelise est du vrai habitat : les especes reperes
occurrent-elles preferentiellement dans les noyaux/corridors plutot que dans la matrice ?

**Portee (a ecrire noir sur blanc).** Valide la couche HABITAT / presence, PAS le flux/connectivite
(une presence ne prouve pas qu'une tache est reliee). Complementaire de A et B.

**Donnees.** GBIF (pygbif / telechargement) ; especes reperes (+ congeneres proches) par profil ;
emprise = AOI de chaque ville.

**Filtrage (indispensable).**
- `coordinateUncertaintyInMeters` <= 100 m ; retirer les centroides commune.
- `basisOfRecord = HumanObservation` ; annees recentes (coherentes avec WorldCover v200) ;
  retirer doublons.

**Neutralisation du biais d'observation** (le point critique) :
1. **Amincissement spatial** : 1 occurrence par pixel/patch (une zone sur-visitee ne pese pas x200).
2. **Fond target-group (TGB)** : disponibilite = occurrences de TOUTES les autres especes observees
   par la meme communaute (meme effort). On teste si l'espece tombe dans l'habitat PLUS que ce fond
   general -> signal au-dela du biais d'echantillonnage.

**Test (use-vs-availability).**
- **Ratio de selection** (Jacobs / Manly) par classe {noyau, corridor (tampon), matrice} =
  part des occurrences / part attendue selon le TGB. Ratio > 1 = preference reelle. IC par bootstrap.
- (option connectivite indirecte) distance de chaque occurrence au noyau/corridor le plus proche,
  occurrences vs points aleatoires.

**Visuels.**
1. Carte : noyaux + corridors en fond, points GBIF de l'espece par-dessus (tombent-ils sur le vert ?).
2. Barres de ratio de selection par classe (ligne a 1 = pas de preference), avec IC.
3. Distribution (violon/CDF) des distances occurrence-vs-aleatoire au plus proche habitat.

**Faisabilite.** Le fetch + filtrage GBIF peut etre construit AVANT la fin du re-run (independant) ;
le test croise a besoin des sorties finales. Profils avec assez d'occurrences : herisson, ecureuil,
fauvette probables ; lezard possiblement pauvre (a verifier, sinon congeneres).

---

## D. Reproductibilite [niveau 1, correction interne]

**Objectif.** La chaine est rejouable a l'identique par un tiers.

**Preuves.**
- **Determinisme** : re-run d'1 ville deux fois -> diff = 0 (test a executer et a citer).
- **Donnees 100 % ouvertes** : WorldCover v200 + OSM + GBIF ; provenance dans
  `suivi/sources_methodology.csv` (version WorldCover, date du snapshot OSM).
- **Versionnage** : code sous git ; parametres (friction, d0) dans `species_params.py`.
- Rejouable de bout en bout depuis `run_pipeline.py`.

**Visuel / encadre.** Un encadre "reproduire ces resultats" (donnees + commande) suffit.

---

## Sequencement propose
1. **Maintenant, en parallele du re-run** : construire le fetch + filtrage + TGB GBIF (independant
   des sorties) ; recuperer les couches SIG Cerema (dependance externe, a lancer tot).
2. **Apres le re-run principal** : test croise GBIF (ratios de selection), comparaison Cerema chiffree,
   test de determinisme (D).
3. **Ensuite** : analyse de sensibilite A (re-runs parametres).
4. Rediger la section ch.5 "Validation et robustesse" a partir des resultats.

## Notions a expliciter dans le rapport (§5.5)
- **Intervalle de confiance (IC 95 %)** : les ratios sont estimes sur un echantillon fini d'occurrences ;
  l'IC (obtenu par bootstrap = re-echantillonnage avec remise des occurrences focales, 1000 tirages)
  donne la fourchette dans laquelle le vrai ratio se trouve avec 95 % de confiance. Regle de lecture :
  si l'IC exclut 1, la preference (ou l'evitement) est statistiquement significative ; s'il englobe 1,
  on ne peut pas conclure. Les IC larges (ex. lezard, herisson hors Toulouse) traduisent un n faible.
- **Fond target-group (TGB)** : la "disponibilite" a laquelle on compare l'usage de l'espece n'est PAS
  la surface des classes, mais la repartition des occurrences de TOUTES les especes de la meme classe
  taxonomique (Mammalia / Aves / Reptilia) observees par la meme communaute. Cela neutralise le biais
  d'echantillonnage de GBIF (les observateurs vont dans les parcs, le long des routes) : un ratio > 1
  signifie que l'espece cible frequente cette classe PLUS que la biodiversite generalement observee au
  meme endroit, donc au-dela du simple effort d'observation.
