# Synthèse : webinaire OFB « MitiConnect : retours d'expérience »

**Date** : 5 juin 2026. **Source** : notes Notion (`MitiConnect ...md`) + 23 captures de slides de ce dossier.
**Intervenantes** : Eva Perez Lopez (avec R. Bedhomme, agglo de La Roche-sur-Yon) ; Solène Nitsche.
**Q&A** : Simon Tarabon, Céline Mathieu (Biotope), Pascal Guichard (TAUW).
REX = retour d'expérience (bilan d'une mise en pratique : avantages, inconvénients, recommandations).

MitiConnect (INRAE) : outil SIG open source (extension QGIS, s'appuie sur Graphab) qui modélise la TVB
pour accompagner la séquence Éviter-Réduire-Compenser et comparer des scénarios d'aménagement.

---

## 1. Point majeur : MitiConnect appliqué à La Roche-sur-Yon (un de nos 6 territoires)

Retour d'expérience Eva Perez Lopez + R. Bedhomme : application à l'agglomération de La Roche-sur-Yon
(13 communes), pour anticiper l'effet de futurs projets sur les continuités, logique ERC.
C'est un **2e point de comparaison externe**, à côté de Cerema/La Rochelle.

Paramètres (par sous-trame, une espèce cible chacune) :

| Sous-trame | Espèce cible | Habitat | Dispersion |
|---|---|---|---|
| Prairiale (prairies, pelouses, habitats ouverts) | Gazé (papillon) | 1000 m² | 1000 m |
| Humide (marais, mares, cours d'eau) | Rainette verte | 5000 m² | 500 m |
| Boisements/haies (ripisylves, bocage) | Écureuil roux | 4000 m² | 1000 m |

- 17 couches ; bases IGN (COSIA, BD TOPO, BD HAIE, CARHAB, RPG), GeoSAS (INRAE), OSM ; résolutions 5 à 10 m.
- Friction **1 à 1000** (habitat = 1, barrière = 1000). Exemple (sous-trame prairiale, 16 couches, ordre de
  friction décroissant) : routes/voies ferrées 1000, bâti 1000, zones imperméables 1000, canopée 500,
  boisements 500, surfaces en eau 100, surfaces perméables 100, cultures 100, chemins ruraux 50, cours
  d'eau 50, milieux humides 50, haies 10, luzernes 10, habitats ouverts / prairies permanentes / pelouses = 1.
- Sorties : cartes de chemins de moindre coût + habitats par sous-trame.

**Écarts avec notre calibration** (à énoncer si on compare) : écureuil dispersion 1000 m (nous 2000),
habitat 4000 m² ; échelle de friction 1-1000 (nous 1-100 + infini) ; ils conservent un profil papillon
(gazé) que nous avons écarté ; entrée par sous-trame + espèce cible, pas par profil de déplacement pur.

## 2. Ce qui valide notre contribution (utile aux §1.5.4 et §4.5)

REX MitiConnect (Solène Nitsche, « dans le cadre de notre application projet ») :
- **Inconvénients** : « Pas d'automatisation possible » ; « Limité sur les grands territoires » ;
  « Dépendant des capacités machine » ; « Temps de calcul longs sur certaines étapes » ; « Pas d'accès
  aux paramètres avancés ».
- **Avantages** : prise en main rapide, interface accessible, paramétrage simplifié, gain de temps pour
  les cartes de friction et jeux de liens, intégration directe QGIS, logiciel libre.
- **Recommandations** : tester les paramètres sur un secteur restreint avant les grands territoires ;
  anticiper les temps de traitement ; vérifier la cohérence écologique des paramètres ; bien documenter
  les hypothèses écologiques.

Lecture : les inconvénients cités sont exactement le verrou opérationnel de notre chapitre 1 (outils
puissants mais non automatisables, peu transposables, lourds sur grandes emprises). Notre chaîne
(automatisée, reproductible, testée sur grandes emprises, Python plein contrôle) répond à ces limites.
Les « améliorations possibles » listées par Eva (analyses de sensibilité + multiplication des profils +
validation experte) sont précisément ce que nous faisons.

## 3. Calibration / friction (utile au §2.3)

- Communauté d'accord : pas de données de référence par espèce/cortège pour les coûts de friction, d'où
  une subjectivité selon l'utilisateur (question de P. Guichard) ; REX chiroptères : « forte dépendance
  à l'expertise écologique, influence importante sur les résultats finaux ». Renforce notre argument
  contraste-avant-valeur-absolue (Bowman) + robustesse (Simpkins).
- Métriques locales de hiérarchisation : IF (Interaction Flux), F (Flux), BC (Betweenness Centrality).
  Tarabon : complémentaires, montrent des choses différentes (flux biologiques, centralité). Nous les
  avons désactivées (dPC, intermédiarité, §6.2) ; ceci situe ce choix.
- Sordello et al. 2013 (traits de vie de 39 espèces) cité comme LA référence traits de déplacement
  (déjà dans notre bibliographie).
- Discrétisation des indices : ruptures naturelles de Jenks, 4 classes (choix MitiConnect).

## 4. Pistes pour nos perspectives (§5.2)

- Plaquer les ouvrages faune/mixtes sur les infrastructures pour ajouter des points/zones de
  perméabilité, si les données existent : passagesfaune.fr (incomplet mais s'enrichit) et data.gouv
  « obstacles à l'écoulement ». Complète notre piste SIPAF (sources supplémentaires).
- Green Urban Sat (GUS) déployé France entière cette année (annonce dans le chat) : conforte notre
  mention de GUS au §2.2 comme évolution possible vers une occupation du sol plus fine.
- Approche trame noire / chiroptères (Solène Nitsche) via Biodispersal + Graphab : illustration concrète
  de l'extension sensorielle que nous évoquons en perspective (pollution lumineuse). HABBY (INRAE) pour
  l'aquatique.

## 5. Suite possible (sur go)

Intégration envisageable, avec citation du webinaire (littérature grise, OFB, 5 juin 2026) :
- ajouter la comparaison MitiConnect / La Roche-sur-Yon à côté de Cerema / La Rochelle (§3.5, §4.4) ;
- appuyer le verrou « pas d'automatisation » du §1.5.4 et l'apport opérationnel du §4.5 sur ce REX.
