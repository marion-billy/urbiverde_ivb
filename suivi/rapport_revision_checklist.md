# Rapport de stage — checklist de révision (retours tuteur + SIGMA)

> Plan de travail traçable. Sources : commentaires du tuteur (Hugo Poupard, docx `rapport_stage_mb__1_.docx`,
> 55 commentaires), points relayés par Marion, consignes du master SIGMA. Détail complet en mémoire projet.
> Cocher au fur et à mesure. Rien n'est modifié dans le rapport sans le go de Marion.

## Cadre transversal (à tenir partout)
- [ ] **Ton scientifique, rigoureux** ; jamais commercial / racoleur / trendy. Observation -> justification -> affirmation (jamais l'inverse). Pas d'em dash.
- [ ] **PoC (preuve de concept)** assumé et mis en avant (aujourd'hui absent alors que central).
- [ ] Statut opérationnel précis : chaîne = opérationnelle ; dashboard = semi-op (non industrialisé) ; test par les villes pilotes = non op ; ce travail = une partie d'un « service ».
- [ ] Valoriser les **apports personnels** et les **échanges** (villes pilotes, CEREMA en réunion — distinct du doc de référence CEREMA).

## Ordre convenu : d'abord les 4 parties « vitrine »
### 1. Résumé
- [ ] Distinct de l'intro et de la conclusion ; répond en peu de mots à sujet / objectifs / méthodes / résultats / apport.
- [ ] Mentionne le PoC ; un résultat chiffré ; valorise sans survendre. FR + EN alignés (200-250 mots).

### 2. Introduction
- [ ] **Synthèse de l'état de l'art remontée dans l'intro, avant la problématique** (« le gap est ici »).
- [ ] Sortir de l'état de l'art ce qui relève de la méthode (paragraphe graphe/moindre coût, Kirk).
- [ ] Ne pas affirmer « la littérature est mature » sans l'avoir montré juste avant.

### 3. Discussion
- [ ] Interprétation **critique** des résultats + comparaison à des travaux publiés (CEREMA/Kirk).
- [ ] Chaque sous-section : détaillée, reliée à la littérature, débattue sous plusieurs angles, lisible seule.
- [ ] Sortir la validation visuelle des « résultats » (irrecevable) et la traiter ici.
- [ ] Difficultés rencontrées -> moyens -> alternatives -> meilleur compromis vu le temps (6 mois, court).

### 4. Conclusion
- [ ] Valorise le travail ; **ne se termine PAS sur les manques / points non traités** -> reformuler en perspectives positives.
- [ ] Reprend chaque objectif en un paragraphe dédié (pas « les cinq objectifs sont atteints »).

## Puis
### 5. Titres et navigation
- [ ] Sous-titres : décrire une **observation précise** (pas « Interprétation des résultats », « Comparaisons », « Les territoires entre eux »).
- [ ] Paragraphe de transition en tête de chaque chapitre (« dans ce chapitre… », « au chapitre précédent on a vu… ») ; résumé d'un paragraphe en fin de résultats.

### 6. Appareil scientifique
- [ ] Formules en **équations numérotées** (comme des figures) : pᵢⱼ=exp(-dᵢⱼ/d₀), etc. + table des formules.
- [ ] Glossaire des **abréviations** ; glossaire **packages + versions**.
- [ ] Hyperliens : figures, abréviations, titres ; citations/formules/abréviations liées à biblio/glossaire. (Nécessite d'étendre le build LaTeX ou de passer LaTeX-first — décision workflow à trancher.)
- [ ] Références signalées par le tuteur à remplacer/vérifier (Herold 2004, Audebert 2018, Vergnes 2013, Baguette 2013, Ricketts exemple) — déjà surlignées dans le texte.

### 7. Figures
- [ ] Flèche **nord** + barre d'échelle **minimalistes** sur les cartes.
- [ ] Attribution **Esri World Imagery** : « Sources: Esri, DigitalGlobe, GeoEye, i-cubed, USDA FSA, USGS, AEX, Getmapping, Aerogrid, IGN, IGP, swisstopo, and the GIS User Community ».
- [ ] Dashboard : screenshots à intégrer (§3.6, figure 8).

### 8. Chapitre 7 — retour d'expérience (première personne)
- [ ] Setup de travail (VSCode + Claude sur VM GPU OVH : 350 Go RAM, 24 cœurs, H100), réunions du mercredi + 1v1, train of thoughts, retours Hugo + CEREMA.
- [ ] Processus de débogage (Claude, Hugo, sources) ; méthodo de vérification avec Claude = prompt engineering.
- [ ] **Convention Claude** décrite sobrement pour un jury universitaire non-IA (relecture, prompt en boucle, CLAUDE.md sceptique par défaut, temps reporté sur le contrôle, code optimisé) ; anticiper « comment es-tu sûre ? ».
- [ ] Connaissances/compétences acquises + vécu du stage.

## Détails méthode à ajouter (dispersés)
- [ ] Justifier le tampon 2·d₀. Version prod : landcover interne Murmuration. Plus de détail sur l'architecture.
- [ ] Renommer « Vérification des résultats » -> « Automatisation du contrôle et de la validation des résultats ».
- [ ] Nettoyer vocabulaire : « corridor planté » (abus), « ouvrage de franchissement » (non défini).
